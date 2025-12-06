"""
Config Selector - Dynamically loads appropriate config based on MODEL_FAMILY environment variable.

Usage:
    # Replace 'import config' with:
    from config_selector import *

    # Or:
    import config_selector as config

Environment Variables:
    MODEL_FAMILY: "qwen" (default) or "deepseek"

This allows running the same experiment scripts with different model configurations
without modifying the code.

Examples:
    # Run with Qwen3 (default)
    python src/single_agent_code_generation.py SA-few

    # Run with DeepSeek
    MODEL_FAMILY=deepseek python src/single_agent_code_generation.py SA-few
"""

import os
import sys

# Determine which config to load based on MODEL_FAMILY environment variable
MODEL_FAMILY = os.getenv('MODEL_FAMILY', 'qwen').lower()

if MODEL_FAMILY == 'deepseek':
    print(f"[Config] Loading DeepSeek configuration (MODEL_FAMILY={MODEL_FAMILY})")
    from config_deepseek import *
    # Also expose the module-level flag for scripts that check it
    _CONFIG_MODULE = 'config_deepseek'
else:
    print(f"[Config] Loading Qwen3 configuration (MODEL_FAMILY={MODEL_FAMILY})")
    from config import *
    _CONFIG_MODULE = 'config'

# Provide a way to check which config is loaded
def get_config_info():
    """Return information about which config module is loaded."""
    return {
        'model_family': MODEL_FAMILY,
        'config_module': _CONFIG_MODULE,
    }
