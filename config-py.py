import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_telegram_bot_token")
GROUP_ID = int(os.getenv("GROUP_ID", "-1000000000"))  # Your Telegram group ID
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "0").split(",")]  # Admin Telegram IDs

# Ainox API setup
AINOX_URL = 'https://go.ainox.pro/api/'
AINOX_LOGIN = os.getenv("AINOX_LOGIN", "your_ainox_login")
AINOX_KEY = os.getenv("AINOX_KEY", "your_ainox_key")

# Wix API setup
WIX_API_KEY = os.getenv("WIX_API_KEY", "your_wix_api_key")
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "your_wix_site_id")

# Payment links
PAYMENT_LINK_INTERNATIONAL = os.getenv("PAYMENT_LINK_INTERNATIONAL", "your_international_payment_link")
PAYMENT_LINK_RUSSIAN = os.getenv("PAYMENT_LINK_RUSSIAN", "your_russian_payment_link")
CANCELLATION_LINK_RUSSIAN = os.getenv("CANCELLATION_LINK_RUSSIAN", "your_russian_cancellation_link")
CANCELLATION_EMAIL = os.getenv("CANCELLATION_EMAIL", "your_cancellation_email")

# Google API credentials
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "credentials.json")
SHEET_ID = os.getenv("SHEET_ID", "your_google_sheet_id")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///subscription_bot.db")

# Conversation states
EMAIL_INPUT = 1
CONFIRM_EMAIL = 2

# Messages in Russian - Can be moved to a separate localization file for multi-language support
MESSAGES = {
    'start': "Привет! Наш цикл с Субагх крийей подошел к концу, с 3 марта стартует новый цикл. Весна - период обновления, лучшее время для реализации новых намерений. Ты с нами?",
    'help': "Доступные команды:\n/start - Начать взаимодействие с ботом\n/subscribe - Оформить подписку\n/status - Проверить статус подписки\n/cancel - Отменить подписку\n/link_email - Привязать email для автоматического отслеживания подписки",
    'subscribe_prompt': "Выберите способ оплаты:",
    'subscribe_international': "Международная карта",
    'subscribe_russian': "Российская карта",
    'payment_international': f"Для оплаты международной картой перейдите по ссылке:\n{PAYMENT_LINK_INTERNATIONAL}",
    'payment_russian': f"Для оплаты российской картой перейдите по ссылке:\n{PAYMENT_LINK_RUSSIAN}",
    'cancel_subscription_russian': f"Для отмены подписки российской картой перейдите по ссылке:\n{CANCELLATION_LINK_RUSSIAN}",
    'cancel_subscription_international': "Для отмены подписки нажмите на [ссылку](" + CANCELLATION_EMAIL + ").",
    'subscription_active': "Ваша подписка активна до {}.",
    'subscription_expired': "Ваша подписка истекла {}. Используйте /subscribe для продления.",
    'no_subscription': "У вас нет активной подписки. Используйте /subscribe для оформления.",
    'reminder_new': "Приглашаем вас оформить подписку для доступа к полному контенту группы.",
    'reminder_renew': "Срок вашей подписки истекает {}. Не забудьте продлить подписку, чтобы сохранить доступ.",
    'reminder_expired': "Ваша подписка истекла. Используйте /subscribe для продления.",
    'link_email_request': "После оплаты, пожалуйста, свяжите ваш email с ботом, используя команду /link_email. Это позволит автоматически отслеживать статус вашей подписки.",
    'unsubscribe': "Нет, хочу отписаться",
    'link_start': "Чтобы связать вашу подписку с аккаунтом Telegram, пожалуйста, введите email, который вы использовали при оформлении подписки.",
    'email_invalid': "Пожалуйста, введите действительный email адрес.",
    'email_confirm': "Вы указали email: {}. Это правильный адрес?",
    'yes': "Да",
    'no': "Нет, ввести заново",
    'email_linked': "Спасибо! Ваш email успешно привязан к аккаунту. Теперь система будет автоматически отслеживать статус вашей подписки.",
    'email_retry': "Давайте попробуем еще раз. Пожалуйста, введите email, который вы использовали при оформлении подписки.",
    'already_linked': "Ваш аккаунт уже связан с email: {}. Хотите изменить его?",
    'change_email': "Изменить email",
    'keep_email': "Оставить текущий"
}
