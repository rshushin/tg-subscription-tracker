import logging
import traceback
from sqlalchemy.exc import SQLAlchemyError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

# Import configuration and models
from models import User, Session
from config import MESSAGES, EMAIL_INPUT, CONFIRM_EMAIL

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Import verification function
from modules.payment_integration import verify_subscription_by_email

async def link_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the email linking process"""
    user_id = update.effective_user.id
    logger.info(f"Starting email linking for user {user_id}")
    
    # Check if user already has a linked email
    db_session = Session()
    try:
        db_user = db_session.query(User).filter_by(telegram_id=user_id).first()
        
        if db_user and db_user.email:
            # User already has an email linked
            logger.info(f"User {user_id} already has email {db_user.email}")
            keyboard = [
                [
                    InlineKeyboardButton(MESSAGES['change_email'], callback_data="change_email"),
                    InlineKeyboardButton(MESSAGES['keep_email'], callback_data="keep_email"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                MESSAGES['already_linked'].format(db_user.email),
                reply_markup=reply_markup
            )
            return CONFIRM_EMAIL
        else:
            # No email linked yet
            logger.info(f"User {user_id} has no email linked yet")
            await update.message.reply_text(MESSAGES['link_start'])
            return EMAIL_INPUT
    
    except Exception as e:
        logger.error(f"Database error in link_email_command: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END
    finally:
        db_session.close()

async def email_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the email input"""
    email = update.message.text.strip()
    user_id = update.effective_user.id
    logger.info(f"Received email input from user {user_id}: {email}")
    
    # Simple email validation
    if '@' not in email or '.' not in email:
        logger.info(f"Invalid email format from user {user_id}: {email}")
        await update.message.reply_text(MESSAGES['email_invalid'])
        return EMAIL_INPUT
    
    # Store the email temporarily in context
    context.user_data['temp_email'] = email
    logger.info(f"Stored email in context for user {user_id}: {email}")
    
    # Ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton(MESSAGES['yes'], callback_data="confirm_email"),
            InlineKeyboardButton(MESSAGES['no'], callback_data="reject_email"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        MESSAGES['email_confirm'].format(email),
        reply_markup=reply_markup
    )
    
    return CONFIRM_EMAIL

async def button_callback_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process button callbacks for email confirmation"""
    query = update.callback_query
    logger.info(f"Email button pressed: {query.data}")
    
    try:
        # Try to answer the callback query, but don't fail if it's already been answered
        await query.answer()
    except Exception as e:
        # Log the error but continue with the function
        logger.warning(f"Error answering callback query: {e}")
    
    if query.data == "confirm_email":
        # User confirmed the email, save it to database
        user_id = update.effective_user.id
        email = context.user_data.get('temp_email')
        
        if not email:
            logger.error("No temp_email found in context")
            try:
                await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте заново с командой /link_email")
            except Exception as e:
                logger.error(f"Could not edit message: {e}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="Произошла ошибка. Пожалуйста, попробуйте заново с командой /link_email"
                )
            return ConversationHandler.END
        
        # Update the database
        db_session = Session()
        try:
            db_user = db_session.query(User).filter_by(telegram_id=user_id).first()
            
            if db_user:
                # CRITICAL: Always reset subscription status first, then update email
                old_email = db_user.email
                db_user.subscription_status = 'none'
                db_user.subscription_end_date = None
                db_user.email = email
                db_session.commit()
                logger.info(f"Updated user {user_id} email from {old_email} to {email} and reset subscription")
                
                # Show confirmation message that email was updated
                try:
                    await query.delete_message()
                except Exception as e:
                    logger.error(f"Could not delete message: {e}")
                
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"Email обновлен с {old_email if old_email else 'отсутствует'} на {email}. Проверяем подписку..."
                )
                
                # Now check for actual subscription in payment systems
                try:
                    # Check if the email has an actual subscription
                    is_subscribed, subscription_info = await verify_subscription_by_email(email)
                    
                    if is_subscribed:
                        # Update user with subscription info
                        db_user.subscription_status = 'active'
                        if subscription_info.get('end_date'):
                            db_user.subscription_end_date = subscription_info['end_date']
                        db_user.is_russian_card = subscription_info.get('payment_method') == 'russian'
                        db_session.commit()
                        
                        # Show success message with subscription info
                        formatted_date = db_user.subscription_end_date.strftime('%d.%m.%Y') if db_user.subscription_end_date else "неизвестная дата"
                        success_message = f"{MESSAGES['email_linked']}\n\nНайдена активная подписка до {formatted_date}."
                    else:
                        # No active subscription found for this email
                        success_message = f"{MESSAGES['email_linked']}\n\nАктивной подписки для этого email не найдено. Используйте /subscribe для оформления подписки."
                except Exception as e:
                    logger.error(f"Error verifying subscription: {e}")
                    logger.error(traceback.format_exc())
                    success_message = f"{MESSAGES['email_linked']}\n\nПроизошла ошибка при проверке статуса подписки. Используйте /status для проверки позже."
                
                # Send final message with result
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=success_message
                )
            else:
                logger.error(f"User {user_id} not found in database")
                try:
                    await query.delete_message()
                except Exception as e:
                    logger.error(f"Could not delete message: {e}")
                
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="Пользователь не найден. Пожалуйста, выполните команду /start"
                )
            
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Database error in confirm_email: {e}")
            logger.error(traceback.format_exc())
            try:
                await query.delete_message()
            except Exception as e:
                logger.error(f"Could not delete message: {e}")
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Произошла ошибка. Пожалуйста, попробуйте позже."
            )
            return ConversationHandler.END
        finally:
            db_session.close()
    
    elif query.data == "reject_email":
        # User rejected the email, ask again
        logger.info("User rejected email, asking again")
        try:
            await query.edit_message_text(MESSAGES['email_retry'])
        except Exception as e:
            logger.error(f"Could not edit message: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=MESSAGES['email_retry']
            )
        return EMAIL_INPUT
    
    elif query.data == "change_email":
        # User wants to change their email
        logger.info("User requested to change email")
        try:
            await query.edit_message_text(MESSAGES['link_start'])
        except Exception as e:
            logger.error(f"Could not edit message: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=MESSAGES['link_start']
            )
        return EMAIL_INPUT
    
    elif query.data == "keep_email":
        # User wants to keep their current email
        logger.info("User chose to keep current email")
        try:
            await query.delete_message()
        except Exception as e:
            logger.error(f"Could not delete message: {e}")
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Вы решили сохранить текущий email. Ваша подписка остается связанной с вашим аккаунтом."
        )
        return ConversationHandler.END
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    logger.info("User canceled email linking")
    await update.message.reply_text("Процесс привязки email отменен.")
    return ConversationHandler.END

def get_email_linking_handler():
    """Return the conversation handler for email linking"""
    logger.info("Creating email linking conversation handler")
    
    handler = ConversationHandler(
        entry_points=[CommandHandler("link_email", link_email_command)],
        states={
            EMAIL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_input)],
            CONFIRM_EMAIL: [
                CallbackQueryHandler(button_callback_email, pattern="^(confirm_email|reject_email|change_email|keep_email)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="email_linking",
        conversation_timeout=300  # 5 minutes timeout
    )
    
    logger.info("Email linking conversation handler created")
    return handler

# Helper functions for other modules
def has_linked_email(telegram_id):
    """Check if a user has a linked email"""
    db_session = Session()
    try:
        db_user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
        return db_user and db_user.email is not None
    except SQLAlchemyError as e:
        logger.error(f"Database error checking linked email: {e}")
        return False
    finally:
        db_session.close()

def get_user_email(telegram_id):
    """Get a user's email"""
    db_session = Session()
    try:
        db_user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
        return db_user.email if db_user else None
    except SQLAlchemyError as e:
        logger.error(f"Database error getting user email: {e}")
        return None
    finally:
        db_session.close()