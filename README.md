# Discord OTC Stock Quote Bot

A Discord bot that scrapes real-time stock quotes from Yahoo Finance, specifically designed to work well with OTC (Over-The-Counter) stocks like FNMA.

## Features

- 📈 Real-time stock quotes via web scraping
- 🎨 Beautiful Discord embeds with color-coded price changes
- 📊 Comprehensive data including price, volume, market cap, day's range
- ⚡ Asynchronous processing (non-blocking)
- 🔍 Works with OTC stocks and regular exchange-traded stocks

## Setup Instructions

### 1. Install Python Dependencies

Make sure you're in your project directory, then run:

```bash
pip install -r requirements.txt
```

Or if you use `pip3`:

```bash
pip3 install -r requirements.txt
```

### 2. Verify Your .env File

Make sure you have a `.env` file in your project directory with your Discord bot token:

```
DISCORD_TOKEN=MTM3NTMwMzIwNzA4NTAxNTA2MQ.GWgDA1.WjM-8TrBCdVtZ-sOdJfIZEtHBo7U3wKPiySooA
```

### 3. Enable Message Content Intent

**This is crucial!** Go to the Discord Developer Portal:

1. Visit https://discord.com/developers/applications
2. Select your bot application
3. Go to the "Bot" section
4. Under "Privileged Gateway Intents", enable **"Message Content Intent"**
5. Save changes

### 4. Run the Bot

```bash
python bot.py
```

Or:

```bash
python3 bot.py
```

You should see:
```
🚀 Starting Discord bot...
YourBotName#1234 has connected to Discord!
Bot is ready in X server(s)
```

## Usage

In any Discord channel where your bot has access:

```
!quote FNMA
!quote AAPL
!quote TSLA
!quote PNBK
```

The bot will respond with a beautiful embed containing:

- 💰 Current Price
- 📊 Previous Close  
- 📈/📉 Price Change (with percentage)
- 🌅 Open Price
- 📈 Day's Range (High - Low)
- 📊 Volume
- 🏢 Market Cap

## Example Output

When you type `!quote FNMA`, you'll get an embed like:

**Fannie Mae (FNMA)**
- 💰 Current Price: $1.23
- 📊 Previous Close: $1.20
- 📈 Change: +$0.03 (+2.50%)
- 🌅 Open: $1.21
- 📈 Day's Range: $1.18 - $1.25
- 📊 Volume: 5,234,567
- 🏢 Market Cap: $142.5M

## Troubleshooting

### Bot doesn't respond to commands
- Make sure "Message Content Intent" is enabled in Discord Developer Portal
- Check that the bot has permission to read messages and send messages in the channel

### "Could not fetch data" error
- The ticker symbol might be invalid
- Yahoo Finance might have changed their website structure
- Network/timeout issues

### Bot won't start
- Check your DISCORD_TOKEN in the .env file
- Make sure all dependencies are installed
- Verify your Python version (3.7+ recommended)

## Notes

- Data is scraped from Yahoo Finance and may be delayed
- The bot works best with US stocks and OTC stocks
- Web scraping can occasionally fail if Yahoo Finance changes their layout
- Rate limiting: Avoid making too many requests in quick succession

## Files

- `bot.py` - Main bot script
- `requirements.txt` - Python dependencies
- `.env` - Discord bot token (create this yourself)
- `README.md` - This file 