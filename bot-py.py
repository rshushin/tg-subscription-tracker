#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Subscription Bot
-------------------------
A bot for managing user subscriptions with Telegram.
This bot handles subscription management, payment verification,
and automatic reminders for subscription renewal.
"""

import logging
import sys
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import config and handlers
from config import BOT_TOKEN, MAIN_MENU_KEYBOARD

# Import handlers from modules
from modules.handlers import (
    start, help_command, subscribe, check_status, 
    cancel_subscription, button_callback, check_new_members,
    admin_update_subscription, admin_broadcast, 
    admin_schedule_broadcast, admin_sync_subscriptions,
    send_reminders, setup_commands_job, schedule_subscription_sync
)

# Import email linking handler
from modules.user_linking import get_email_linking_handler

def main() -> None:
    """Start the bot."""
    # Check if token is provided
    if BOT_TOKEN == "your_telegram_bot_token":
        logger.error("Please set your bot token in config.py or .env file")
        sys.exit(1)
        
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    logger.info("Registering command handlers")
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("status", check_status))
    application.add_handler(CommandHandler("cancel", cancel_subscription))
    
    # Admin commands
    application.add_handler(CommandHandler("update_sub", admin_update_subscription))
    application.add_handler(CommandHandler("broadcast", admin_broadcast))
    application.add_handler(CommandHandler("sync_subscriptions", admin_sync_subscriptions))
    application.add_handler(CommandHandler("schedule_broadcast", admin_schedule_broadcast)) 
    
    # Add email linking handler
    logger.info("Registering email linking handler")
    application.add_handler(get_email_linking_handler())
    logger.info("Email linking handler registered")
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add handler for new members
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, check_new_members))
    
    # Add job queue
    job_queue = application.job_queue
    
    # Job for sending reminders (run every day)
    job_queue.run_repeating(send_reminders, interval=86400, first=10)
    
    # Job for syncing subscriptions (run every 12 hours)
    job_queue.run_repeating(schedule_subscription_sync, interval=43200, first=60)
    
    # Run the initial subscription sync when bot starts
    job_queue.run_once(schedule_subscription_sync, when=120)
    
    # Set up command menu (run once at startup)
    job_queue.run_once(setup_commands_job, when=5)
    
    logger.info("Bot started with subscription integration")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    from telegram import Update
    main()
