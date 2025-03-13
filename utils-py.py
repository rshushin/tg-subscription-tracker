import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_email(email):
    """
    Validate email format using a simple regex
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_date(date_obj):
    """
    Format a datetime object to a readable string
    
    Args:
        date_obj (datetime): Date to format
        
    Returns:
        str: Formatted date string
    """
    if not date_obj:
        return "неизвестная дата"
    
    try:
        return date_obj.strftime('%d.%m.%Y')
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return "неизвестная дата"

def get_days_until_date(date_obj):
    """
    Calculate days until a specific date
    
    Args:
        date_obj (datetime): Target date
        
    Returns:
        int: Number of days until the date, or 0 if date is in the past
    """
    if not date_obj:
        return 0
    
    try:
        days = (date_obj - datetime.now()).days
        return max(0, days)
    except Exception as e:
        logger.error(f"Error calculating days until date: {e}")
        return 0

def is_last_day_of_month(date_obj):
    """
    Check if a date is the last day of the month
    
    Args:
        date_obj (datetime): Date to check
        
    Returns:
        bool: True if it's the last day of the month
    """
    if not date_obj:
        return False
    
    try:
        next_day = date_obj.replace(day=date_obj.day + 1)
        return False
    except ValueError:
        # ValueError means we're at the last day of the month
        return True
    except Exception as e:
        logger.error(f"Error checking if last day of month: {e}")
        return False

def sanitize_database_input(text):
    """
    Sanitize user input for database safety
    
    Args:
        text (str): Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Remove any potentially harmful characters
    return re.sub(r'[^\w\s@.-]', '', text)

def get_last_day_of_month(year, month):
    """
    Get the last day of a specific month
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        
    Returns:
        int: Last day of the month
    """
    if month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        # Check for leap year
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        else:
            return 28
    else:
        return 31
