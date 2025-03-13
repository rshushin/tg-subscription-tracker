import logging
import hashlib
import traceback
from datetime import datetime, timedelta
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials

# Import models and config
from models import User, Session
from config import (
    AINOX_URL, AINOX_LOGIN, AINOX_KEY, 
    WIX_API_KEY, WIX_SITE_ID,
    CREDENTIALS_PATH, SHEET_ID
)

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# API headers
AINOX_HEADERS = {
    'api-login': AINOX_LOGIN,
    'api-key': AINOX_KEY
}

def generate_ainox_unsubscribe_link(email):
    """
    Generate an Ainox-style unsubscribe link for a given email
    
    Args:
        email (str): The user's email address
        
    Returns:
        str: A properly formatted Ainox unsubscribe URL
    """
    try:
        # Find the subscriber ID by email
        subscribers_data = {
            "request": "subscriber",
            "type": "output",
            "limit": 0,
            "offset": 0,
            "filter": {"email": email},
            "fields": ["id"]
        }
        
        response = requests.post(
            AINOX_URL,
            json=subscribers_data,
            headers=AINOX_HEADERS
        )
        
        if response.status_code == 200 and 'data' in response.json():
            subscribers = response.json()['data']
            if subscribers:
                subscriber_id = subscribers[0].get('id')
                if subscriber_id:
                    # Generate the hash part using MD5 (similar to how Ainox does it)
                    hash_input = f"{email}:{subscriber_id}"
                    hash_output = hashlib.md5(hash_input.encode()).hexdigest()
                    
                    # Format the URL with the subscriber ID and hash
                    return f"https://onlayn-meditaciya-na-procvetanie.ainox.pro/unsubscribe::{subscriber_id}::{hash_output}"
        
        # If we couldn't find a subscription or generate a proper link, return the generic page
        logger.warning(f"Could not generate specific unsubscribe link for {email}")
        return "https://onlayn-meditaciya-na-procvetanie.ainox.pro/unsubscribe"
    
    except Exception as e:
        logger.error(f"Error generating unsubscribe link: {e}")
        return "https://onlayn-meditaciya-na-procvetanie.ainox.pro/unsubscribe"

class WixSubscriptionManager:
    """Class to handle Wix subscription API interactions"""
    def __init__(self, api_key=WIX_API_KEY, site_id=WIX_SITE_ID):
        self.headers = {
            "Authorization": api_key,
            "wix-site-id": site_id,
            "Content-Type": "application/json"
        }

    def get_purchased_plans(self):
        """Get all active orders with 'online' in plan name"""
        endpoint = "https://www.wixapis.com/pricing-plans/v2/orders"
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            all_orders = response.json().get('orders', [])
            # Log all order data for debugging
            for order in all_orders:
                logger.debug(f"Order: {order.get('id')}, Plan: {order.get('planName')}, Status: {order.get('status')}")
            return [order for order in all_orders if order.get('status', '').lower() == 'active']
        logger.error(f"Failed to get Wix orders: {response.status_code}, {response.text}")
        return []

    def get_subscriber_info(self, order):
        """Get subscriber information from a Wix order"""
        try:
            contact_id = order['buyer']['contactId']
            response = requests.get(
                f"https://www.wixapis.com/contacts/v4/contacts/{contact_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                contact_data = response.json()
                contact = contact_data.get('contact', {})
                
                # Get email from primaryEmail
                email = contact.get('primaryEmail', {}).get('email', '')
                logger.info(f"Found Wix contact email: {email}")
                
                # Get status and calculate end date
                status = order.get('status', '').lower()
                is_active = status == 'active'
                
                # Extract renewal date from order
                created_date = order.get('startDate', order.get('createdDate', ''))
                end_date = None
                
                # Calculate end date to the last day of the month
                if created_date:
                    try:
                        date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        
                        # Get current month and year
                        current_month = date_obj.month
                        current_year = date_obj.year
                        
                        # Get the last day of the current month
                        if current_month in [4, 6, 9, 11]:
                            last_day = 30
                        elif current_month == 2:
                            if (current_year % 4 == 0 and current_year % 100 != 0) or (current_year % 400 == 0):
                                last_day = 29  # Leap year
                            else:
                                last_day = 28
                        else:
                            last_day = 31
                        
                        # Set end date to the last day of the current month
                        end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
                        
                        logger.info(f"Calculated end date (end of month): {end_date}")
                    except (ValueError, TypeError, KeyError):
                        logger.error(f"Error calculating end date from: {created_date}")
                
                return {
                    'email': email,
                    'is_active': is_active,
                    'end_date': end_date,
                    'payment_method': 'international',  # Wix is for international payments
                    'order_id': order.get('id', '')
                }
            
            logger.error(f"Failed to get contact info: {response.status_code}, {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting subscriber info: {e}")
            logger.error(traceback.format_exc())
            return None

def get_ainox_subscribers():
    """Get all subscribers from Ainox"""
    subscribers_data = {
        "request": "subscriber",
        "type": "output",
        "limit": 0,
        "offset": 0,
        "fields": ["id", "email", "status", "next_payment_date", "next_payment_price", "price", "first_invoice_id"]
    }

    response = requests.post(AINOX_URL, json=subscribers_data, headers=AINOX_HEADERS)
    
    if response.status_code == 200 and 'data' in response.json():
        return response.json()['data']
    
    logger.error(f"Failed to get Ainox subscribers: {response.status_code}, {response.text}")
    return []

def get_ainox_subscriber_info(subscriber):
    """Process Ainox subscriber data"""
    try:
        subscriber_id = str(subscriber.get('id', ''))
        email = subscriber.get('email', '')
        
        # Get additional info from first invoice
        name = "Unknown"
        phone = "Unknown"
        first_invoice_id = subscriber.get('first_invoice_id')

        if first_invoice_id:
            parent_request_data = {
                "request": "request",
                "type": "output",
                "id": first_invoice_id
            }

            parent_response = requests.post(AINOX_URL, json=parent_request_data, headers=AINOX_HEADERS)
            
            if parent_response.status_code == 200:
                parent_response_json = parent_response.json()
                
                if 'data' in parent_response_json:
                    parent_data = parent_response_json.get('data', {})
                    name = parent_data.get('name', name)
                    phone = parent_data.get('phone', phone)

        # Process status and next payment date
        status = subscriber.get('status', 0)
        is_active = status == 1  # 1 = Active in Ainox
        
        next_payment_date = None
        if subscriber.get('next_payment_date'):
            try:
                next_payment_date = datetime.strptime(subscriber['next_payment_date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        return {
            'email': email,
            'is_active': is_active,
            'end_date': next_payment_date,
            'payment_method': 'russian',  # Assuming Ainox is for Russian payments
            'name': name,
            'phone': phone,
            'subscriber_id': subscriber_id
        }
    except Exception as e:
        logger.error(f"Error processing Ainox subscriber: {e}")
        return None

def update_user_subscription_status(telegram_id, subscription_info):
    """Update user subscription status in the database"""
    try:
        db_session = Session()
        db_user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if db_user:
            if subscription_info['is_active']:
                db_user.subscription_status = 'active'
                db_user.subscription_end_date = subscription_info['end_date']
                db_user.is_russian_card = subscription_info['payment_method'] == 'russian'
            else:
                # Only mark as expired if it was previously active
                if db_user.subscription_status == 'active':
                    db_user.subscription_status = 'expired'
            
            db_session.commit()
            logger.info(f"Updated subscription for user {telegram_id}: {subscription_info['is_active']}")
            return True
        else:
            logger.warning(f"User with telegram_id {telegram_id} not found")
            return False
    
    except Exception as e:
        logger.error(f"Error updating user subscription: {e}")
        return False
    finally:
        db_session.close()

def find_telegram_id_by_email(email):
    """Find a user's Telegram ID by their email"""
    try:
        # Query the database to see if any user has this email
        db_session = Session()
        db_user = db_session.query(User).filter_by(email=email).first()
        
        if db_user:
            return db_user.telegram_id
        return None
    
    except Exception as e:
        logger.error(f"Error finding user by email: {e}")
        logger.error(traceback.format_exc())  # Print full error traceback
        return None
    finally:
        db_session.close()

async def sync_subscriptions():
    """Main function to sync all subscription data"""
    logger.info("Starting subscription sync")
    
    # Get Wix subscriptions
    wix_manager = WixSubscriptionManager()
    wix_orders = wix_manager.get_purchased_plans()
    
    for order in wix_orders:
        subscriber_info = wix_manager.get_subscriber_info(order)
        if subscriber_info:
            telegram_id = find_telegram_id_by_email(subscriber_info['email'])
            if telegram_id:
                update_user_subscription_status(telegram_id, subscriber_info)
    
    # Get Ainox subscriptions
    ainox_subscribers = get_ainox_subscribers()
    
    for subscriber in ainox_subscribers:
        subscriber_info = get_ainox_subscriber_info(subscriber)
        if subscriber_info:
            telegram_id = find_telegram_id_by_email(subscriber_info['email'])
            if telegram_id:
                update_user_subscription_status(telegram_id, subscriber_info)
    
    logger.info("Subscription sync completed")

async def verify_subscription_by_email(email):
    """Verify if an email has an active subscription and return proper provider info"""
    try:
        normalized_email = email.lower().strip()
        logger.info(f"Verifying subscription for email: {normalized_email}")
        
        # Store results from each provider
        ainox_result = None
        wix_result = None
        
        # Check Wix FIRST (this is the key change - prioritize Wix over Ainox)
        logger.info("Checking Wix subscriptions...")
        wix_manager = WixSubscriptionManager()
        wix_orders = wix_manager.get_purchased_plans()
        
        for order in wix_orders:
            subscriber_info = wix_manager.get_subscriber_info(order)
            
            # Check if email matches and status is active
            if (subscriber_info and 
                subscriber_info.get('email', '').lower().strip() == normalized_email and 
                subscriber_info.get('is_active')):
                
                logger.info(f"Found active Wix subscription for: {email}")
                wix_result = subscriber_info
                # Return immediately if found in Wix
                return True, wix_result
        
        # Only check Ainox if not found in Wix
        subscribers_data = {
            "request": "subscriber",
            "type": "output",
            "limit": 0,
            "offset": 0,
            "filter": {"email": normalized_email},
            "fields": ["id", "email", "status", "next_payment_date"]
        }
        
        response = requests.post(AINOX_URL, json=subscribers_data, headers=AINOX_HEADERS)
        
        if response.status_code == 200 and 'data' in response.json():
            subscribers = response.json()['data']
            
            # Extra validation for Ainox - check if the subscriber has status = 1 (active)
            # AND verify the email exactly matches, not just contains
            for subscriber in subscribers:
                subscriber_email = subscriber.get('email', '').lower().strip()
                
                # Strict email matching
                if subscriber_email != normalized_email:
                    logger.info(f"Skipping non-exact email match: '{subscriber_email}' vs requested '{normalized_email}'")
                    continue
                
                status = subscriber.get('status', 0)
                is_active = status == 1
                
                if is_active:
                    next_payment_date = None
                    if subscriber.get('next_payment_date'):
                        try:
                            next_payment_date = datetime.strptime(subscriber['next_payment_date'], '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            pass
                    
                    logger.info(f"Found active Ainox subscription (status=1) for: {email}")
                    ainox_result = {
                        'email': email,
                        'is_active': True,
                        'end_date': next_payment_date,
                        'payment_method': 'russian',
                        'subscriber_id': subscriber.get('id')
                    }
                    return True, ainox_result
        
        # No active subscription found in either system
        logger.info(f"No active subscription found for: {email}")
        return False, {}
    
    except Exception as e:
        logger.error(f"Error verifying subscription: {e}")
        logger.error(traceback.format_exc())  # Add detailed error tracing
        return False, {}

# Function to be called from the main bot
async def schedule_subscription_sync(context):
    """Function to be called by the job queue"""
    await sync_subscriptions()