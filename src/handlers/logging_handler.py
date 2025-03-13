from uuid import UUID, uuid4
from typing import Any, Dict, List, Optional
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from datetime import datetime, timezone
import logging
from src.storage.database_manager import SQLiteManager
from src.storage.containers.logs import LogsContainer
import math
import json

class LLMLoggingHandler(BaseCallbackHandler):
    """Callback handler for logging LLM interactions with cost tracking."""

    # Cost per 1000 tokens (adjust as needed)
    COST_PER_1K_TOKENS = {
        "llama3-70b-8192": {"input": 0.0015, "output": 0.002},
        "default": {"input": 0.0015, "output": 0.002}
    }

    def __init__(self, sqlite_manager: SQLiteManager, user_id: str):
        super().__init__()
        self.sqlite_manager = sqlite_manager
        self.user_id = user_id
        self.log = logging.getLogger(__name__)
        self.logs_container = LogsContainer(sqlite_manager)
        self.session_id = str(uuid4())  # Generate a session ID for this instance
        self.conversation_id = str(uuid4())  # Generate a conversation ID
        self.current_log = None
        self.accumulated_tokens = {"input": 0, "output": 0}

    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of the LLM interaction."""
        pricing = self.COST_PER_1K_TOKENS.get(model_name, self.COST_PER_1K_TOKENS["default"])
        # Ceiling to nearest 1000
        input_tokens_k = math.ceil(input_tokens / 1000) * 1000
        output_tokens_k = math.ceil(output_tokens / 1000) * 1000
        input_cost = (input_tokens_k / 1000) * pricing["input"]
        output_cost = (output_tokens_k / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def update_token_usage(self, input_tokens: int, output_tokens: int, model_name: str = "llama3-70b-8192"):
        """Update accumulated token usage"""
        self.accumulated_tokens["input"] += input_tokens
        self.accumulated_tokens["output"] += output_tokens
        
        # Calculate cost based on accumulated tokens
        cost = self._calculate_cost(
            model_name,
            self.accumulated_tokens["input"],
            self.accumulated_tokens["output"]
        )
        
        return {
            "input_tokens": self.accumulated_tokens["input"],
            "output_tokens": self.accumulated_tokens["output"],
            "cost_usd": cost
        }

    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        try:
            # Create a new conversation log entry for the input
            self.current_log = await self.logs_container.create_conversation_log(
                user_id=self.user_id,
                input_text=prompts[0],  # Assuming single prompt for now
                session_id=self.session_id,
                conversation_id=self.conversation_id,
                meta_data={
                    "model_parameters": serialized.get("kwargs", {}),
                    **kwargs.get("metadata", {})
                }
            )
        except Exception as e:
            self.log.exception(f"Error in on_llm_start: {e}")

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        try:
            if self.current_log:
                # Get token usage from response
                token_usage = response.llm_output.get("token_usage", {})
                input_tokens = token_usage.get("prompt_tokens", 0)
                output_tokens = token_usage.get("completion_tokens", 0)
                
                # Update accumulated tokens
                usage_info = self.update_token_usage(input_tokens, output_tokens)
                
                # Update the conversation log with response and token usage
                await self.logs_container.update_conversation_log(
                    session_id=self.session_id,
                    output_text=response.generations[0][0].text,
                    input_tokens=usage_info["input_tokens"],
                    output_tokens=usage_info["output_tokens"],
                    model_name=response.llm_output.get("model_name", "llama3-70b-8192")
                )
                
                self.current_log = None  # Reset current log
                
        except Exception as e:
            self.log.exception(f"Error in on_llm_end: {e}")

    async def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        try:
            if self.current_log:
                # Update the log with error information
                await self.logs_container.update_conversation_log(
                    session_id=self.session_id,
                    output_text=f"Error: {str(error)}",
                    input_tokens=self.accumulated_tokens["input"],
                    output_tokens=self.accumulated_tokens["output"]
                )
                self.current_log = None
        except Exception as e:
            self.log.exception(f"Error in on_llm_error: {e}")

    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id

    def get_conversation_id(self) -> str:
        """Get the current conversation ID"""
        return self.conversation_id