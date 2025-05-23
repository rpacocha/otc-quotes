import discord
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
import asyncio

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Set up Discord client intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

def scrape_yahoo_finance(ticker_symbol):
    """
    Scrape stock data from Yahoo Finance for the given ticker symbol.
    Returns a dictionary with stock data or None if failed.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    url = f"https://finance.yahoo.com/quote/{ticker_symbol}"
    
    try:
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize data dictionary
        data = {
            'ticker': ticker_symbol,
            'name': ticker_symbol,
            'current_price': None,
            'previous_close': None,
            'open': None,
            'day_range': None,
            'volume': None,
            'market_cap': None,
            'price_change': None,
            'price_change_percent': None
        }
        
        # Try to get company name from title first (most reliable)
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text
            # Pattern: "Company Name (TICKER) Stock Price..."
            title_pattern = r'^([^(]+?)\s*\(\s*' + re.escape(ticker_symbol) + r'\s*\)'
            title_match = re.search(title_pattern, title_text, re.IGNORECASE)
            if title_match:
                data['name'] = title_match.group(1).strip()
        
        # Get current price - try multiple selectors
        price_selectors = [
            # New working selectors based on investigation
            '[data-testid="qsp-price"]',
            f'fin-streamer[data-symbol="{ticker_symbol}"][data-field="regularMarketPrice"]',
            f'fin-streamer[data-testid="qsp-price"]',
            '[data-testid="qsp-price"] fin-streamer'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_value = price_element.get('value') or price_element.text
                if price_value:
                    data['current_price'] = price_value.strip()
                    break
        
        # Get price change information  
        change_element = soup.select_one('[data-testid="qsp-price-change"]')
        if change_element:
            data['price_change'] = change_element.text.strip()
        
        change_percent_element = soup.select_one('[data-testid="qsp-price-change-percent"]')
        if change_percent_element:
            data['price_change_percent'] = change_percent_element.text.strip()
        
        # Get other data using data-test attributes (more reliable)
        data_mappings = {
            'PREV_CLOSE-value': 'previous_close',
            'OPEN-value': 'open',
            'DAYS_RANGE-value': 'day_range',
            'MARKET_CAP-value': 'market_cap'
        }
        
        for test_id, data_key in data_mappings.items():
            element = soup.find('td', {'data-test': test_id})
            if element:
                data[data_key] = element.text.strip()
        
        # Get volume with multiple approaches
        volume_element = soup.find('fin-streamer', {'data-symbol': ticker_symbol, 'data-field': 'regularMarketVolume'})
        if volume_element:
            volume_value = volume_element.get('value') or volume_element.text
            if volume_value:
                data['volume'] = volume_value.strip()
        else:
            # Fallback to data-test approach
            volume_element = soup.find('td', {'data-test': 'TD_VOLUME-value'})
            if volume_element:
                data['volume'] = volume_element.text.strip()
        
        print(f"Scraped data for {ticker_symbol}: {data}")
        return data
        
    except requests.exceptions.Timeout:
        print(f"Timeout error for {ticker_symbol}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for {ticker_symbol}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {ticker_symbol}: {e}")
        return None

def parse_number(value_str):
    """Convert string numbers with K, M, B, T suffixes to float."""
    if not value_str:
        return None
    
    # Clean the string
    clean_str = str(value_str).replace(',', '').replace('$', '').strip()
    
    # Handle multipliers
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}
    
    if clean_str and clean_str[-1].upper() in multipliers:
        try:
            number = float(clean_str[:-1])
            return number * multipliers[clean_str[-1].upper()]
        except ValueError:
            return None
    
    try:
        return float(clean_str)
    except ValueError:
        return None

def format_number(value):
    """Format large numbers with appropriate suffixes."""
    if value is None:
        return "N/A"
    
    if value >= 1_000_000_000_000:
        return f"${value/1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.2f}K"
    else:
        return f"${value:.2f}"

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Bot is ready in {len(client.guilds)} server(s)')

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Check for quote command
    if message.content.startswith('!quote'):
        parts = message.content.split()
        if len(parts) < 2:
            await message.channel.send("❌ Please provide a ticker symbol!\nUsage: `!quote <TICKER>`\nExample: `!quote FNMA`")
            return
        
        ticker = parts[1].upper()
        
        # Send initial message
        status_msg = await message.channel.send(f"🔍 Fetching data for **{ticker}** from Yahoo Finance...")
        
        try:
            # Run scraping in executor to avoid blocking
            loop = asyncio.get_event_loop()
            stock_data = await loop.run_in_executor(None, scrape_yahoo_finance, ticker)
            
            if not stock_data or not stock_data.get('current_price'):
                await status_msg.edit(content=f"❌ Could not fetch data for **{ticker}**\n\n**Possible reasons:**\n• Invalid ticker symbol\n• Yahoo Finance structure changed\n• Network/timeout issue\n\nTry again or check the ticker symbol.")
                return
            
            # Parse the numerical values
            current_price = parse_number(stock_data.get('current_price'))
            previous_close = parse_number(stock_data.get('previous_close'))
            open_price = parse_number(stock_data.get('open'))
            volume = parse_number(stock_data.get('volume'))
            market_cap = parse_number(stock_data.get('market_cap'))
            
            # Parse price change data (already extracted from Yahoo)
            price_change_raw = stock_data.get('price_change')
            price_change_percent_raw = stock_data.get('price_change_percent')
            price_change = parse_number(price_change_raw) if price_change_raw else None
            
            # Parse day range
            day_low = day_high = None
            day_range = stock_data.get('day_range')
            if day_range and ' - ' in day_range:
                try:
                    low_str, high_str = day_range.split(' - ')
                    day_low = parse_number(low_str)
                    day_high = parse_number(high_str)
                except:
                    pass
            
            # Create Discord embed
            company_name = stock_data.get('name', ticker)
            
            # Determine color based on price change
            embed_color = discord.Color.blue()  # Default
            if price_change is not None:
                if price_change > 0:
                    embed_color = discord.Color.green()
                elif price_change < 0:
                    embed_color = discord.Color.red()
            elif current_price and previous_close:
                if current_price > previous_close:
                    embed_color = discord.Color.green()
                elif current_price < previous_close:
                    embed_color = discord.Color.red()
            
            embed = discord.Embed(
                title=f"{company_name} ({ticker})",
                url=f"https://finance.yahoo.com/quote/{ticker}",
                color=embed_color,
                description="Real-time quote from Yahoo Finance"
            )
            
            # Add price information
            if current_price is not None:
                embed.add_field(
                    name="💰 Current Price", 
                    value=f"${current_price:,.2f}", 
                    inline=True
                )
            
            if previous_close is not None:
                embed.add_field(
                    name="📊 Previous Close", 
                    value=f"${previous_close:,.2f}", 
                    inline=True
                )
            
            # Use extracted price change data if available, otherwise calculate
            if price_change is not None and price_change_percent_raw:
                change_emoji = "📈" if price_change >= 0 else "📉"
                # Clean up the percent format (remove parentheses if present)
                percent_clean = price_change_percent_raw.strip('()')
                embed.add_field(
                    name=f"{change_emoji} Change", 
                    value=f"${price_change:+,.2f} {percent_clean}", 
                    inline=True
                )
            elif current_price and previous_close:
                # Fallback to manual calculation
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                change_emoji = "📈" if change >= 0 else "📉"
                embed.add_field(
                    name=f"{change_emoji} Change", 
                    value=f"${change:+,.2f} ({change_percent:+.2f}%)", 
                    inline=True
                )
            
            if open_price is not None:
                embed.add_field(
                    name="🌅 Open", 
                    value=f"${open_price:,.2f}", 
                    inline=True
                )
            
            if day_low is not None and day_high is not None:
                embed.add_field(
                    name="📈 Day's Range", 
                    value=f"${day_low:,.2f} - ${day_high:,.2f}", 
                    inline=True
                )
            
            if volume is not None:
                embed.add_field(
                    name="📊 Volume", 
                    value=f"{int(volume):,}", 
                    inline=True
                )
            
            if market_cap is not None:
                embed.add_field(
                    name="🏢 Market Cap", 
                    value=format_number(market_cap), 
                    inline=True
                )
            
            embed.set_footer(text="Data scraped from Yahoo Finance • May be delayed")
            
            await status_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            print(f"Error in message handler: {e}")
            await status_msg.edit(content=f"❌ An unexpected error occurred while fetching data for **{ticker}**.\n\nPlease try again later.")

# Main execution
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in .env file!")
        print("Please make sure you have created a .env file with your Discord bot token.")
        exit(1)
    
    try:
        print("🚀 Starting Discord bot...")
        client.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("❌ Failed to login to Discord!")
        print("Please check your DISCORD_TOKEN in the .env file.")
    except Exception as e:
        print(f"❌ Bot startup error: {e}") 