"""
API Interaction Tracking for RQ4: Cost and Efficiency Analysis

Tracks API calls, token usage, latency, and cost for single/dual/multi-agent experiments.
"""

import time
import tiktoken
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class APITracker:
    """Track API interactions for efficiency analysis (RQ4)."""

    # Model pricing (USD per 1K tokens) - adjust based on actual costs
    # For Ollama (local), cost is 0, but we track tokens for potential cloud comparison
    MODEL_PRICING = {
        "qwen3:4b-instruct": {"prompt": 0.0, "completion": 0.0},
        "qwen3:4b-thinking": {"prompt": 0.0, "completion": 0.0},
        "qwen3:30b-instruct": {"prompt": 0.0, "completion": 0.0},
        # Add OpenAI pricing for comparison if needed
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    }

    def __init__(self, model_name: str = "qwen3:4b-instruct"):
        """Initialize tracker with model name for token encoding."""
        self.model_name = model_name
        self.interactions: List[Dict[str, Any]] = []

        # Initialize tiktoken encoder (use cl100k_base for qwen/general models)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to gpt2 encoding if cl100k_base unavailable
            self.encoder = tiktoken.get_encoding("gpt2")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def track_interaction(
        self,
        agent_name: str,
        prompt: str,
        response: str,
        latency: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a single agent interaction.

        Args:
            agent_name: Name of the agent (e.g., "code_author", "security_analyst")
            prompt: Input prompt/message
            response: Agent's response
            latency: Time taken in seconds
            metadata: Additional metadata (e.g., response dict from AutoGen)

        Returns:
            Dict with interaction metrics
        """
        prompt_tokens = self.count_tokens(prompt)
        completion_tokens = self.count_tokens(response)
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
        pricing = self.MODEL_PRICING.get(self.model_name, {"prompt": 0.0, "completion": 0.0})
        cost = (prompt_tokens / 1000 * pricing["prompt"]) + \
               (completion_tokens / 1000 * pricing["completion"])

        interaction = {
            "agent_name": agent_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_seconds": round(latency, 3),
            "cost_usd": round(cost, 6),
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            interaction["metadata"] = metadata

        self.interactions.append(interaction)
        return interaction

    def get_sample_summary(self) -> Dict[str, Any]:
        """
        Get aggregated metrics for the current sample.

        Returns:
            Dict with total API calls, tokens, time, and cost for this sample
        """
        if not self.interactions:
            return {
                "total_api_calls": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_latency_seconds": 0.0,
                "total_cost_usd": 0.0,
                "interactions": []
            }

        return {
            "total_api_calls": len(self.interactions),
            "total_prompt_tokens": sum(i["prompt_tokens"] for i in self.interactions),
            "total_completion_tokens": sum(i["completion_tokens"] for i in self.interactions),
            "total_tokens": sum(i["total_tokens"] for i in self.interactions),
            "total_latency_seconds": round(sum(i["latency_seconds"] for i in self.interactions), 3),
            "total_cost_usd": round(sum(i["cost_usd"] for i in self.interactions), 6),
            "interactions": self.interactions.copy()
        }

    def reset(self):
        """Reset interactions for next sample."""
        self.interactions = []


def track_generate_reply(
    tracker: APITracker,
    agent,
    agent_name: str,
    messages: List[Dict[str, str]]
) -> Tuple[Any, Dict[str, Any]]:
    """
    Wrapper for agent.generate_reply() with tracking.

    Args:
        tracker: APITracker instance
        agent: AutoGen agent instance
        agent_name: Name for tracking (e.g., "code_author")
        messages: Messages to pass to generate_reply()

    Returns:
        Tuple of (response, interaction_metrics)
    """
    # Extract prompt text
    prompt = messages[0]["content"] if messages else ""

    # Time the API call
    start_time = time.time()
    response = agent.generate_reply(messages=messages)
    latency = time.time() - start_time

    # Extract response text
    if isinstance(response, dict):
        response_text = response.get("content", "")
    else:
        response_text = str(response)

    # Track interaction
    interaction = tracker.track_interaction(
        agent_name=agent_name,
        prompt=prompt,
        response=response_text,
        latency=latency,
        metadata={"response_type": type(response).__name__}
    )

    return response, interaction


def track_initiate_chat(
    tracker: APITracker,
    user_proxy,
    recipient,
    agent_name: str,
    message: str,
    max_turns: int = 1,
    summary_method: str = "last_msg"
) -> Tuple[Any, Dict[str, Any]]:
    """
    Wrapper for user_proxy.initiate_chat() with tracking.

    Args:
        tracker: APITracker instance
        user_proxy: AutoGen user proxy agent
        recipient: Recipient agent
        agent_name: Name for tracking (e.g., "security_researcher")
        message: Message to send
        max_turns: Maximum conversation turns
        summary_method: Summary method for AutoGen

    Returns:
        Tuple of (chat_result, interaction_metrics)
    """
    # Time the API call
    start_time = time.time()
    result = user_proxy.initiate_chat(
        recipient=recipient,
        message=message,
        max_turns=max_turns,
        summary_method=summary_method
    )
    latency = time.time() - start_time

    # Extract response
    response_text = result.summary.strip() if hasattr(result, 'summary') else str(result)

    # Track interaction
    interaction = tracker.track_interaction(
        agent_name=agent_name,
        prompt=message,
        response=response_text,
        latency=latency,
        metadata={
            "max_turns": max_turns,
            "summary_method": summary_method
        }
    )

    return result, interaction


def calculate_experiment_metrics(all_sample_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate experiment-level aggregated metrics from all samples.

    Args:
        all_sample_summaries: List of sample summaries from get_sample_summary()

    Returns:
        Dict with experiment-level metrics (averages, totals, etc.)
    """
    if not all_sample_summaries:
        return {
            "total_samples": 0,
            "avg_api_calls_per_sample": 0.0,
            "avg_tokens_per_sample": 0.0,
            "avg_latency_per_sample": 0.0,
            "avg_cost_per_sample": 0.0,
            "total_api_calls": 0,
            "total_tokens": 0,
            "total_latency_seconds": 0.0,
            "total_cost_usd": 0.0
        }

    total_samples = len(all_sample_summaries)

    return {
        "total_samples": total_samples,
        "avg_api_calls_per_sample": round(
            sum(s["total_api_calls"] for s in all_sample_summaries) / total_samples, 2
        ),
        "avg_tokens_per_sample": round(
            sum(s["total_tokens"] for s in all_sample_summaries) / total_samples, 2
        ),
        "avg_latency_per_sample": round(
            sum(s["total_latency_seconds"] for s in all_sample_summaries) / total_samples, 3
        ),
        "avg_cost_per_sample": round(
            sum(s["total_cost_usd"] for s in all_sample_summaries) / total_samples, 6
        ),
        "total_api_calls": sum(s["total_api_calls"] for s in all_sample_summaries),
        "total_tokens": sum(s["total_tokens"] for s in all_sample_summaries),
        "total_latency_seconds": round(
            sum(s["total_latency_seconds"] for s in all_sample_summaries), 3
        ),
        "total_cost_usd": round(
            sum(s["total_cost_usd"] for s in all_sample_summaries), 6
        )
    }
