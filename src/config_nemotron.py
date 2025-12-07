"""
Llama-Nemotron Configuration for Cross-Architecture Validation

This config file extends the base config.py for Llama-Nemotron experiments.
Unlike Qwen3/DeepSeek which use API parameters, Nemotron uses SYSTEM PROMPT
to toggle thinking mode.

Toggle Mechanisms:
- Nano-8B v1: "detailed thinking on" / "detailed thinking off" in system prompt
- Super-49B v1.5: default=ON, "/no_think" in system prompt = OFF

Usage:
    # In your experiment script, replace:
    #   import config
    # with:
    #   import config_nemotron as config

Reference: docs/Cross_Architecture_Validation_Plan.md
"""

import os

# ========================================================================================
# DIRECTORY PATHS (from base config)
# ========================================================================================

PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/workspace/agent-green')
LOG_DIR = f'{PROJECT_ROOT}/logs'
DATA_DIR = f'{PROJECT_ROOT}/data'
WORK_DIR = f'{PROJECT_ROOT}/tests/work_dir'
RESULT_DIR = os.getenv('RESULTS_DIR', f'{PROJECT_ROOT}/results')
PLOT_DIR = f'{PROJECT_ROOT}/plots'

# ========================================================================================
# DATASETS
# ========================================================================================

VULN_DATASET = os.getenv('VULN_DATASET', f"{PROJECT_ROOT}/vuln_database/VulTrial_386_samples_balanced.jsonl")
HUMANEVAL_DATASET = os.getenv('HUMANEVAL_DATASET', f"{PROJECT_ROOT}/vuln_database/HumanEval.jsonl")

# ========================================================================================
# NEMOTRON MODEL CONFIGURATION
# ========================================================================================

# Environment-based configuration
USE_RUNPOD = os.getenv('USE_RUNPOD', 'true').lower() == 'true'
ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'

# Model endpoints (from .env.nemotron)
REASONING_ENDPOINT = os.getenv('REASONING_ENDPOINT', 'http://localhost:8000/v1')
BASELINE_ENDPOINT = os.getenv('BASELINE_ENDPOINT', 'http://localhost:8000/v1')
REASONING_MODEL = os.getenv('REASONING_MODEL', 'nvidia/Llama-3.1-Nemotron-Nano-8B-v1')
BASELINE_MODEL = os.getenv('BASELINE_MODEL', 'nvidia/Llama-3.1-Nemotron-Nano-8B-v1')
REASONING_API_KEY = os.getenv('REASONING_API_KEY', '')
BASELINE_API_KEY = os.getenv('BASELINE_API_KEY', '')

# Temperature (matching Qwen3 baseline: 0.0 for deterministic output)
# Note: Nemotron recommends 0.6 for thinking mode, but we use 0.0 for fair comparison
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.0'))

# Select model based on reasoning mode
if ENABLE_REASONING:
    LLM_MODEL = REASONING_MODEL
    LLM_ENDPOINT = REASONING_ENDPOINT
    LLM_API_KEY = REASONING_API_KEY
else:
    LLM_MODEL = BASELINE_MODEL
    LLM_ENDPOINT = BASELINE_ENDPOINT
    LLM_API_KEY = BASELINE_API_KEY

# Service type for AutoGen
LLM_SERVICE = os.getenv('LLM_SERVICE', 'openai')

# ========================================================================================
# NEMOTRON THINKING MODE SYSTEM PROMPTS
# ========================================================================================
#
# IMPORTANT: Nemotron uses SYSTEM PROMPT to control thinking mode, not API parameters!
#
# Model-specific toggle mechanisms:
# - Nano-8B v1: "detailed thinking on" / "detailed thinking off"
# - Super-49B v1.5: default (no system prompt) = ON, "/no_think" = OFF
#
# The experiment scripts must prepend these system prompts to enable/disable thinking.

def is_super_model():
    """Check if current model is Super-49B (uses different toggle syntax)."""
    return 'Super' in LLM_MODEL or '49B' in LLM_MODEL


def get_thinking_system_prompt():
    """
    Get the system prompt to ENABLE thinking mode.

    Returns:
        str: System prompt for thinking mode
    """
    if is_super_model():
        # Super-49B v1.5: default (empty) enables thinking
        return ""
    else:
        # Nano-8B v1: explicit "detailed thinking on"
        return "detailed thinking on"


def get_non_thinking_system_prompt():
    """
    Get the system prompt to DISABLE thinking mode.

    Returns:
        str: System prompt for non-thinking mode
    """
    if is_super_model():
        # Super-49B v1.5: "/no_think" disables thinking
        return "/no_think"
    else:
        # Nano-8B v1: explicit "detailed thinking off"
        return "detailed thinking off"


def get_reasoning_system_prompt():
    """
    Get the appropriate system prompt based on ENABLE_REASONING setting.

    Returns:
        str: System prompt for current reasoning mode
    """
    if ENABLE_REASONING:
        return get_thinking_system_prompt()
    else:
        return get_non_thinking_system_prompt()


# ========================================================================================
# LLM CONFIG FOR AUTOGEN
# ========================================================================================

# Nemotron context length: 128K (inherited from Llama 3.1/3.3)
# Standardized to 64K to match Qwen3 experiments for fair comparison
# Note: 49B with FP8 may be limited to 32K due to memory constraints
MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', '65536'))

# Build the config_list entry
_config_entry = {
    "model": LLM_MODEL,
    "base_url": LLM_ENDPOINT,
    "api_type": LLM_SERVICE,
}

# Add API key if provided
if LLM_API_KEY:
    _config_entry["api_key"] = LLM_API_KEY
else:
    _config_entry["api_key"] = "not-needed"  # vLLM doesn't require API key by default

# NOTE: Unlike DeepSeek/Qwen3, Nemotron does NOT use extra_body for thinking toggle!
# The thinking mode is controlled via system prompt in the messages array.
# Experiment scripts must use get_reasoning_system_prompt() to prepend the toggle.

LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [_config_entry],
    "temperature": TEMPERATURE
}

# ========================================================================================
# MODEL INFO (for logging and experiment tracking)
# ========================================================================================

MODEL_FAMILY = "Nemotron"
MODEL_ARCHITECTURE = "Dense"  # Llama-Nemotron is dense (not MoE)

def get_model_info():
    """Return model information for experiment logging."""
    return {
        "model": LLM_MODEL,
        "family": MODEL_FAMILY,
        "architecture": MODEL_ARCHITECTURE,
        "enable_thinking": ENABLE_REASONING,
        "thinking_toggle": "system_prompt",  # Different from Qwen3/DeepSeek
        "thinking_prompt": get_reasoning_system_prompt(),
        "temperature": TEMPERATURE,
        "endpoint": LLM_ENDPOINT,
        "max_context": MAX_CONTEXT_LENGTH,
    }

# ========================================================================================
# IMPORT ALL PROMPTS FROM BASE CONFIG
# ========================================================================================

# Import all prompt templates from base config
from config import (
    # Task prompts
    TASK_PROMPT,
    TASK_PROMPT_LOG_PARSING,
    TASK_PROMPT_LOG_ANALYSIS,
    TASK_PROMPT_TD_DETECTION,

    # Vulnerability detection prompts
    VULNERABILITY_TASK_PROMPT,
    VULNERABILITY_TASK_PROMPT_EXPLAIN_BEFORE,
    SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT,
    SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT,
    SYS_MSG_VULNERABILITY_DETECTOR_EXPLAIN_BEFORE_ZERO_SHOT,
    SYS_MSG_VULNERABILITY_DETECTOR_EXPLAIN_BEFORE_FEW_SHOT,

    # Dual-agent vulnerability prompts
    SYS_MSG_SECURITY_ANALYST_FEW_SHOT,
    SYS_MSG_SECURITY_ANALYST_ZERO_SHOT,
    SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT,
    SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT,
    DUAL_AGENT_TASK_CODE_SUBMISSION,
    DUAL_AGENT_TASK_FINAL_DECISION,
    DUAL_AGENT_ANALYST_EMPHASIS_WRAPPER,
    DUAL_AGENT_TASK_SECURITY_FEEDBACK,
    DUAL_AGENT_TASK_CODE_REVISION,

    # Multi-agent vulnerability prompts
    SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT,
    SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT,
    SYS_MSG_CODE_AUTHOR_FEW_SHOT,
    SYS_MSG_CODE_AUTHOR_ZERO_SHOT,
    SYS_MSG_MODERATOR_FEW_SHOT,
    SYS_MSG_MODERATOR_ZERO_SHOT,
    SYS_MSG_REVIEW_BOARD_FEW_SHOT,
    SYS_MSG_REVIEW_BOARD_ZERO_SHOT,
    MULTI_AGENT_TASK_SECURITY_RESEARCHER,
    MULTI_AGENT_TASK_CODE_AUTHOR,
    MULTI_AGENT_TASK_MODERATOR,
    MULTI_AGENT_TASK_REVIEW_BOARD,
    THREE_AGENT_TASK_REVIEW_BOARD,

    # Code generation prompts
    FEW_SHOT_EXAMPLES,
    SYS_MSG_CODE_GENERATOR_ZERO_SHOT,
    SYS_MSG_CODE_GENERATOR_FEW_SHOT,
    SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_ZERO_SHOT,
    SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_FEW_SHOT,
    SINGLE_AGENT_TASK_CODE_GENERATION,
    CODE_GENERATION_TASK_PROMPT,
    CODE_GENERATION_TASK_PROMPT_EXPLAIN_BEFORE,

    # Dual-agent code generation prompts
    SYS_MSG_PROGRAMMER_ZERO_SHOT,
    SYS_MSG_PROGRAMMER_FEW_SHOT,
    DUAL_AGENT_TASK_CODE_GENERATION,
    SYS_MSG_CODE_REVIEWER_ZERO_SHOT,
    SYS_MSG_CODE_REVIEWER_FEW_SHOT,
    DUAL_AGENT_TASK_CODE_REVIEW,

    # Multi-agent code generation prompts
    SYS_MSG_REQUIREMENTS_ANALYST_ZERO_SHOT,
    SYS_MSG_REQUIREMENTS_ANALYST,
    MULTI_AGENT_TASK_ANALYST,
    MULTI_AGENT_TASK_REQUIREMENTS_ANALYST_ZERO_SHOT,
    SYS_MSG_PROGRAMMER_MA_ZERO_SHOT,
    SYS_MSG_PROGRAMMER_MA,
    MULTI_AGENT_TASK_PROGRAMMER,
    MULTI_AGENT_TASK_PROGRAMMER_ZERO_SHOT,
    SYS_MSG_MODERATOR_CODE_ZERO_SHOT,
    SYS_MSG_MODERATOR_CODE,
    MULTI_AGENT_TASK_MODERATOR_CODE,
    SYS_MSG_REVIEW_BOARD_CODE_ZERO_SHOT,
    SYS_MSG_REVIEW_BOARD_CODE,
    MULTI_AGENT_TASK_REVIEW_BOARD_CODE,

    # Log parsing/analysis prompts (for completeness)
    SYS_MSG_LOG_PARSER_GENERATOR_FEW_SHOT,
    SYS_MSG_LOG_PARSER_GENERATOR_ZERO_SHOT,
    SYS_MSG_LOG_PARSER_CRITIC_FEW_SHOT,
    SYS_MSG_LOG_PARSER_CRITIC_ZERO_SHOT,
    SYS_MSG_LOG_PARSER_COMPARATOR_REFINER_FEW_SHOT,
    SYS_MSG_LOG_PARSER_COMPARATOR_REFINER_ZERO_SHOT,
    SYS_MSG_LOG_PARSER_REFINER_ZERO_SHOT,
    SYS_MSG_LOG_PARSER_REFINER_FEW_SHOT,

    # Technical debt detection prompts
    SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT,
    SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT,
    SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT,
    SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT,
    SYS_MSG_TD_DETECTION_REFINER_ZERO_SHOT,
    SYS_MSG_TD_DETECTION_REFINER_FEW_SHOT,
)

# ========================================================================================
# HELPER FUNCTION: PREPEND THINKING TOGGLE TO SYSTEM MESSAGE
# ========================================================================================

def prepend_thinking_toggle(system_message: str) -> str:
    """
    Prepend the Nemotron thinking toggle to a system message.

    For Nemotron, the thinking toggle must be at the START of the system prompt.
    This function prepends the appropriate toggle based on ENABLE_REASONING.

    Args:
        system_message: The original system message (e.g., agent instructions)

    Returns:
        str: System message with thinking toggle prepended

    Example:
        >>> # With ENABLE_REASONING=True (Nano-8B)
        >>> prepend_thinking_toggle("You are a security analyst.")
        "detailed thinking on\n\nYou are a security analyst."

        >>> # With ENABLE_REASONING=False (Nano-8B)
        >>> prepend_thinking_toggle("You are a security analyst.")
        "detailed thinking off\n\nYou are a security analyst."
    """
    toggle = get_reasoning_system_prompt()

    if not toggle:
        # Super-49B thinking mode: no prefix needed (default is thinking ON)
        return system_message

    if not system_message:
        return toggle

    return f"{toggle}\n\n{system_message}"


# ========================================================================================
# PRINT CONFIGURATION ON IMPORT (for debugging)
# ========================================================================================

if __name__ == "__main__":
    print("Llama-Nemotron Configuration")
    print("=" * 60)
    print(f"Model: {LLM_MODEL}")
    print(f"Endpoint: {LLM_ENDPOINT}")
    print(f"Enable Reasoning: {ENABLE_REASONING}")
    print(f"Thinking Toggle: System Prompt")
    print(f"Thinking Prompt: '{get_reasoning_system_prompt()}'")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Max Context: {MAX_CONTEXT_LENGTH}")
    print()
    print("LLM Config:")
    import json
    print(json.dumps(LLM_CONFIG, indent=2, default=str))
    print()
    print("Example system message with toggle:")
    example = prepend_thinking_toggle("You are a helpful assistant.")
    print(f"  '{example}'")
