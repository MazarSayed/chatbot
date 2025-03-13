from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import NoResultFound, IntegrityError
from typing import Dict, List, Optional, Any
import logging
import math

# Define the base class for SQLAlchemy models
Base = declarative_base()

class LogActivity(Base):
    __tablename__ = 'log_activity'
    
    session_id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    model_name = Column(String, nullable=True)
    meta_data = Column(Text, nullable=True)

class SQLiteManager:
    # Cost per 1000 tokens (adjust as needed)
    COST_PER_1K_TOKENS = {
        "llama3-70b-8192": {"input": 0.0015, "output": 0.002},
        "default": {"input": 0.0015, "output": 0.002}
    }

    def __init__(self, DATABASE_URL: str):
        self.engine = create_engine(DATABASE_URL, echo=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)  # Create tables if they don't exist

    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on ceiling of token counts to nearest 1000"""
        pricing = self.COST_PER_1K_TOKENS.get(model_name, self.COST_PER_1K_TOKENS["default"])
        
        # Ceiling to nearest 1000
        input_tokens_k = math.ceil(input_tokens / 1000) * 1000
        output_tokens_k = math.ceil(output_tokens / 1000) * 1000
        
        input_cost = (input_tokens_k / 1000) * pricing["input"]
        output_cost = (output_tokens_k / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def get_session(self):
        """Create a new session."""
        return self.SessionLocal()

    def create_item(self, item: Dict) -> Optional[Dict]:
        """Create a new item in the database."""
        session = self.get_session()
        try:
            new_item = LogActivity(**item)  # Assuming item is a dict matching the model
            session.add(new_item)
            session.commit()
            session.refresh(new_item)  # Refresh to get the new item's ID
            return new_item.__dict__  # Return the created item as a dictionary
        except IntegrityError as e:
            logging.error(f"Failed to create item: {str(e)}")
            session.rollback()
            return None
        finally:
            session.close()

    def read_item(self, session_id: str) -> Optional[Dict]:
        """Read an item from the database by session_id."""
        session = self.get_session()
        try:
            item = session.query(LogActivity).filter(LogActivity.session_id == session_id).one()
            return item.__dict__  # Return the item as a dictionary
        except NoResultFound:
            return None
        except Exception as e:
            logging.error(f"Failed to read item: {str(e)}")
            return None
        finally:
            session.close()

    def update_item(self, session_id: str, updates: Dict) -> Optional[Dict]:
        """Update an item in the database."""
        session = self.get_session()
        try:
            item = session.query(LogActivity).filter(LogActivity.session_id == session_id).one()
            for key, value in updates.items():
                setattr(item, key, value)
            session.commit()
            return item.__dict__  # Return the updated item as a dictionary
        except NoResultFound:
            return None
        except Exception as e:
            logging.error(f"Failed to update item: {str(e)}")
            session.rollback()
            return None
        finally:
            session.close()

    def delete_item(self, session_id: str) -> bool:
        """Delete an item from the database."""
        session = self.get_session()
        try:
            item = session.query(LogActivity).filter(LogActivity.session_id == session_id).one()
            session.delete(item)
            session.commit()
            return True
        except NoResultFound:
            return False
        except Exception as e:
            logging.error(f"Failed to delete item: {str(e)}")
            session.rollback()
            return False
        finally:
            session.close()