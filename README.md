# Telegram Subscription Bot

A Telegram bot that manages user subscriptions with integration for payment systems (Wix and Ainox). The bot handles subscription tracking, reminder notifications, and email verification.

## Features

- User subscription management
- Integration with Wix and Ainox payment systems
- Email verification for subscription tracking
- Automatic subscription status updates
- Customizable reminder notifications
- Admin broadcast functionality
- Multi-language support (currently Russian)

## Project Structure

```
telegram-subscription-bot/
├── README.md
├── requirements.txt
├── config.py
├── models.py
├── bot.py
├── modules/
│   ├── __init__.py
│   ├── payment_integration.py
│   ├── user_linking.py
│   ├── utils.py
│   └── handlers.py
```

## Requirements

- Python 3.7+
- SQLite 3
- python-telegram-bot 20.0+
- gspread
- oauth2client
- SQLAlchemy
- requests

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-subscription-bot.git
cd telegram-subscription-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your config.py file with your API credentials and configuration:
```python
# Create a file named config.py with your credentials
BOT_TOKEN = "your_telegram_bot_token"
GROUP_ID = -1000000000  # Your Telegram group ID
ADMIN_IDS = [000000000, 111111111]  # Admin Telegram IDs

# Ainox API credentials
AINOX_LOGIN = "your_ainox_login"
AINOX_KEY = "your_ainox_key"

# Wix API credentials
WIX_API_KEY = "your_wix_api_key"
WIX_SITE_ID = "your_wix_site_id"

# Payment links
PAYMENT_LINK_INTERNATIONAL = "your_international_payment_link"
PAYMENT_LINK_RUSSIAN = "your_russian_payment_link"
CANCELLATION_LINK_RUSSIAN = "your_russian_cancellation_link"
CANCELLATION_EMAIL = "your_cancellation_email"

# Google API credentials path
CREDENTIALS_PATH = "path/to/your/google_credentials.json"
SHEET_ID = "your_google_sheet_id"
```

4. Run the bot:
```bash
python bot.py
```

## Bot Commands

- `/start` - Start the bot
- `/help` - Get help information
- `/subscribe` - Subscribe to the service
- `/status` - Check subscription status
- `/cancel` - Cancel a subscription
- `/link_email` - Link email to account for automatic subscription verification

### Admin Commands

- `/update_sub [user_id] [status] [months]` - Update a user's subscription
- `/broadcast [message]` - Send a message to all users
- `/sync_subscriptions` - Manually sync subscriptions with payment systems
- `/schedule_broadcast` - Schedule a broadcast message

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Wix API](https://dev.wix.com/)
- [Ainox API](https://ainox.pro/)
