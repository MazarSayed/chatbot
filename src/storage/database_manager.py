from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import NoResultFound, IntegrityError
from typing import Dict, List, Optional, Any
import logging

# Define the base class for SQLAlchemy models
Base = declarative_base()

class LogActivity(Base):
    __tablename__ = 'log_activity'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

class SQLiteManager:
    def __init__(self, DATABASE_URL: str):
        self.engine = create_engine(DATABASE_URL, echo=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)  # Create tables if they don't exist

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

    def read_item(self, item_id: int) -> Optional[Dict]:
        """Read an item from the database by ID."""
        session = self.get_session()
        try:
            item = session.query(LogActivity).filter(LogActivity.id == item_id).one()
            return item.__dict__  # Return the item as a dictionary
        except NoResultFound:
            return None
        except Exception as e:
            logging.error(f"Failed to read item: {str(e)}")
            return None
        finally:
            session.close()

    def update_item(self, item_id: int, updates: Dict) -> Optional[Dict]:
        """Update an item in the database."""
        session = self.get_session()
        try:
            item = session.query(LogActivity).filter(LogActivity.id == item_id).one()
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

    def delete_item(self, item_id: int) -> bool:
        """Delete an item from the database."""
        session = self.get_session()
        try:
            item = session.query(LogActivity).filter(LogActivity.id == item_id).one()
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