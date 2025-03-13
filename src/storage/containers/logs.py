from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
import uuid
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import NoResultFound, IntegrityError
import logging
from src.storage.database_manager import SQLiteManager
# Define the base class for SQLAlchemy models
Base = declarative_base()

class TokenUsage(BaseModel):
    """Model for token usage statistics"""
    input_tokens: int
    output_tokens: int
    total_tokens: int

class LLMRequestDetails(BaseModel):
    """Model for LLM request details"""
    input_messages: List[str]
    output_messages: Optional[List[str]] = None
    model_parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    parent_run_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    additional_info: Dict[str, Any] = Field(default_factory=dict)

class LogActivityBase(BaseModel):
    """Base model for all log activities"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    type: str
    title: str
    description: str

class LogLLMRequestActivity(LogActivityBase):
    """Model for LLM request logs"""
    type: str = "llm_request"
    trace_id: str
    run_id: str
    model_name: str
    status: Literal["pending", "completed", "error"] = "pending"
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    token_usage: Optional[TokenUsage] = None
    cost_usd: Optional[float] = None
    meta_data: LLMRequestDetails

class UserActivityLog(LogActivityBase):
    """Model for general user activity logs"""
    type: str = "user_activity"
    meta_data: Dict[str, Any] = Field(default_factory=dict)

class ConversationLog(BaseModel):
    """Model for conversation logs"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    input_text: str
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    model_name: str = "llama3-70b-8192"
    meta_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    type: str = "conversation"  # Always set a default type

    class Config:
        validate_assignment = True

class LogsContainer:
    def __init__(self, sqlite_manager: SQLiteManager):
        self.sqlite_manager = sqlite_manager
        self.container_name = "logs"  # This can be used for logging purposes

    async def create_llm_request(
        self,
        user_id: str,
        title: str,
        description: str,
        trace_id: str,
        run_id: str,
        model_name: str,
        input_messages: List[str],
        model_parameters: Dict[str, Any] = None,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """Create a new LLM request log"""
        request_details = LLMRequestDetails(
            input_messages=input_messages,
            model_parameters=model_parameters or {},
            parent_run_id=parent_run_id,
            tags=tags or [],
            additional_info=additional_info or {}
        )

        activity = LogLLMRequestActivity(
            user_id=user_id,
            title=title,
            description=description,
            trace_id=trace_id,
            run_id=run_id,
            model_name=model_name,
            start_time=datetime.now(timezone.utc).isoformat(),
            meta_data=request_details
        )
        
        return self.sqlite_manager.create_item(activity.dict())  # Use the SQLite manager to create the item

    async def update_llm_request(
        self,
        trace_id: str,
        run_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict]:
        """Update an existing LLM request log"""
        # Here you would implement the logic to find the log entry by trace_id and run_id
        # For simplicity, let's assume we are updating by run_id
        session = self.sqlite_manager.get_session()
        try:
            item = session.query(LogLLMRequestActivity).filter(LogLLMRequestActivity.run_id == run_id).one()
            for key, value in updates.items():
                setattr(item, key, value)
            item.updated_at = datetime.now(timezone.utc).isoformat()
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

    async def get_llm_requests(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> List[Dict]:
        """Get LLM requests with filtering options"""
        session = self.sqlite_manager.get_session()
        query = session.query(LogLLMRequestActivity).filter(LogLLMRequestActivity.type == "llm_request")

        if user_id:
            query = query.filter(LogLLMRequestActivity.user_id == user_id)

        if start_date:
            query = query.filter(LogLLMRequestActivity.start_time >= start_date)

        if end_date:
            query = query.filter(LogLLMRequestActivity.start_time <= end_date)

        if status:
            query = query.filter(LogLLMRequestActivity.status == status)

        if trace_id:
            query = query.filter(LogLLMRequestActivity.trace_id == trace_id)

        return [item.__dict__ for item in query.all()]  # Return items as a list of dictionaries

    async def create_user_activity_log(
        self,
        user_id: str,
        title: str,
        description: str,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Create a new user activity log"""
        activity = UserActivityLog(
            user_id=user_id,
            title=title,
            description=description,
            meta_data=meta_data or {}
        )
        
        return self.sqlite_manager.create_item(activity.dict())  # Use the SQLite manager to create the item

    async def create_conversation_log(
        self,
        user_id: str,
        input_text: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        output_text: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        model_name: Optional[str] = None
    ) -> Dict:
        """Create a new conversation log entry"""
        log = ConversationLog(
            session_id=session_id or str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            user_id=user_id,
            input_text=input_text,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name=model_name or "llama3-70b-8192",
            meta_data=meta_data or {},
            type="conversation"  # Explicitly set type
        )
        
        return self.sqlite_manager.create_item(log.dict())

    async def update_conversation_log(
        self,
        session_id: str,
        output_text: str,
        input_tokens: int,
        output_tokens: int,
        model_name: str = "llama3-70b-8192"
    ) -> Optional[Dict]:
        """Update an existing conversation log with response and token usage"""
        total_tokens = input_tokens + output_tokens
        cost_usd = self.sqlite_manager.calculate_cost(model_name, input_tokens, output_tokens)
        
        updates = {
            "output_text": output_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "model_name": model_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return self.sqlite_manager.update_item(session_id, updates)

    async def get_conversation_logs(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get conversation logs with filtering options"""
        session = self.sqlite_manager.get_session()
        query = session.query(ConversationLog).filter(ConversationLog.type == "conversation")

        if user_id:
            query = query.filter(ConversationLog.user_id == user_id)
        if session_id:
            query = query.filter(ConversationLog.session_id == session_id)
        if conversation_id:
            query = query.filter(ConversationLog.conversation_id == conversation_id)
        if start_date:
            query = query.filter(ConversationLog.created_at >= start_date)
        if end_date:
            query = query.filter(ConversationLog.created_at <= end_date)

        return [item.__dict__ for item in query.all()] 