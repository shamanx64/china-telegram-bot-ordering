# Telegram Food Ordering Bot

This project is a simple Telegram bot for food ordering. Users can:

- browse a menu of dishes
- add multiple items to an order
- view the current cart
- checkout and receive a final receipt with the total price

## Setup

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather).
2. Copy your bot token.
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Set the bot token:

```powershell
$env:TELEGRAM_BOT_TOKEN="your-token-here"
```

5. Run the bot:

```powershell
python bot.py
```

## Bot Commands

- `/start` - welcome message and menu
- `/menu` - show the available dishes
- `/cart` - show selected dishes and current total
- `/checkout` - generate the final receipt and clear the cart

## Notes

- The menu is defined directly in [bot.py](/C:/Users/User/telegrambot/bot.py) and can be edited easily.
- Orders are stored in memory per user session while the bot is running.
