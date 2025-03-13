import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

class User(Base):
    """User model for storing Telegram user data and subscription information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    language_code = Column(String)
    subscription_status = Column(String, default='none')  # 'none', 'active', 'expired'
    subscription_end_date = Column(DateTime, nullable=True)
    is_russian_card = Column(Boolean, default=False)
    last_reminder_sent = Column(DateTime, nullable=True)
    joined_date = Column(DateTime, default=datetime.now)
    email = Column(String, nullable=True)  # Email field for subscription linking

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, name='{self.first_name}', status='{self.subscription_status}')>"

    def is_subscription_active(self):
        """Check if user has an active subscription"""
        if self.subscription_status != 'active':
            return False
        
        if not self.subscription_end_date:
            return False
            
        return self.subscription_end_date > datetime.now()

    def get_formatted_end_date(self):
        """Return formatted subscription end date"""
        if not self.subscription_end_date:
            return "неизвестная дата"
        return self.subscription_end_date.strftime('%d.%m.%Y')
        
    def is_expiring_soon(self, days=7):
        """Check if subscription is expiring within given days"""
        if not self.is_subscription_active():
            return False
            
        days_remaining = (self.subscription_end_date - datetime.now()).days
        return days_remaining <= days

    def days_until_expiration(self):
        """Return number of days until subscription expires"""
        if not self.is_subscription_active():
            return 0
            
        return (self.subscription_end_date - datetime.now()).days

# Initialize database
try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    logger.info(f"Database initialized at {DATABASE_URL}")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise
