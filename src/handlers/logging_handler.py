from uuid import UUID, uuid4
from typing import Any, Dict, List, Optional
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from datetime import datetime, timezone
import logging
from src.storage.database_manager import SQLiteManager
from src.storage.containers.logs import LogsContainer

class LLMLoggingHandler(BaseCallbackHandler):
    """Callback handler for logging LLM interactions with cost tracking."""

    # GPT-4 pricing per 1k tokens (adjust as needed)
    COST_PER_1K_TOKENS = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
    }

    def __init__(self, sqlite_manager: SQLiteManager, user_id: str, trace_id: str = None, metadata: Dict[str, Any] = None):
        super().__init__()
        self.sqlite_manager = sqlite_manager
        self.user_id = user_id
        self.trace_id = trace_id or str(uuid4())
        self.metadata = metadata or {}
        self.log = logging.getLogger(__name__)
        self.logs_container = LogsContainer(sqlite_manager)
        self.start_times: Dict[str, datetime] = {}
        self.trace_items: Dict[str, Dict[str, Any]] = {}

    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of the LLM interaction."""
        pricing = self.COST_PER_1K_TOKENS.get(model_name, self.COST_PER_1K_TOKENS["gpt-4"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        try:
            run_id = str(kwargs.get("run_id", uuid4()))
            self.start_times[run_id] = datetime.now(timezone.utc)

            model_name = (
                serialized.get("kwargs", {}).get("deployment_name")
                or serialized.get("name", "unknown")
            )
            
            trace_item = await self.logs_container.create_llm_request(
                user_id=self.user_id,
                title="LLM Interaction",
                description=f"LLM interaction with model {model_name}",
                trace_id=self.trace_id,
                run_id=run_id,
                model_name=model_name,
                input_messages=prompts,
                model_parameters=serialized.get("kwargs", {}),
                parent_run_id=str(kwargs.get("parent_run_id")) if kwargs.get("parent_run_id") else None,
                tags=kwargs.get("tags", []),
                additional_info={
                    **self.metadata,
                    **kwargs.get("metadata", {})
                }
            )
            self.trace_items[run_id] = trace_item

        except Exception as e:
            self.log.exception(f"Error in on_llm_start: {e}")

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        try:
            run_id = str(kwargs.get("run_id", "unknown"))
            end_time = datetime.now(timezone.utc).isoformat()
            
            if run_id in self.start_times:
                duration = (datetime.now(timezone.utc) - self.start_times[run_id]).total_seconds()
                
                token_usage = response.llm_output.get("token_usage", {})
                model_name = response.llm_output.get("model_name", "gpt-4")
                cost = self._calculate_cost(
                    model_name,
                    token_usage.get("prompt_tokens", 0),
                    token_usage.get("completion_tokens", 0)
                )

                # Get the existing metadata from trace_items
                existing_metadata = self.trace_items[run_id].get("metadata", {})
                # Update the metadata with new output_messages while preserving existing data
                updated_metadata = {
                    **existing_metadata,  # Keep all existing metadata
                    "output_messages": [gen.text for gen in response.generations[0]]
                }

                await self.logs_container.update_llm_request(
                    trace_id=self.trace_id,
                    run_id=run_id,
                    updates={
                        "status": "completed",
                        "end_time": end_time,
                        "duration_seconds": duration,
                        "token_usage": {
                            "input_tokens": token_usage.get("prompt_tokens", 0),
                            "output_tokens": token_usage.get("completion_tokens", 0),
                            "total_tokens": token_usage.get("total_tokens", 0)
                        },
                        "cost_usd": cost,
                        "metadata": updated_metadata
                    }
                )

                del self.start_times[run_id]
                del self.trace_items[run_id]

        except Exception as e:
            self.log.exception(f"Error in on_llm_end: {e}")