"""
OpenRouter Configuration for SOTA Model Comparison

This module provides configuration for accessing frontier models via OpenRouter API.
Supports Claude Sonnet 4.5 and Claude Opus 4.5 for vulnerability detection experiments.

Usage:
    export OPENROUTER_API_KEY=<your-key>
    export OPENROUTER_MODEL=anthropic/claude-sonnet-4  # or anthropic/claude-opus-4
    python src/single_agent_vuln_openrouter.py --shot zero
"""

import os

# ========================================================================================
# DIRECTORY PATHS
# ========================================================================================

PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green')
RESULT_DIR = os.getenv('RESULTS_DIR', f'{PROJECT_ROOT}/results')

# ========================================================================================
# DATASETS
# ========================================================================================

VULN_DATASET = os.getenv('VULN_DATASET', f"{PROJECT_ROOT}/data/VulTrial_386_samples_balanced.jsonl")

# ========================================================================================
# OPENROUTER CONFIGURATION
# ========================================================================================

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_API_BASE = os.getenv('OPENROUTER_API_BASE', 'https://openrouter.ai/api/v1')

# Model selection
# Options: anthropic/claude-sonnet-4, anthropic/claude-opus-4
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4')

# Extended thinking for Opus 4.5
ENABLE_EXTENDED_THINKING = os.getenv('ENABLE_EXTENDED_THINKING', 'false').lower() == 'true'

# Temperature (0.0 for deterministic output)
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.0'))

# Build LLM config for AutoGen compatibility
LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [{
        "model": OPENROUTER_MODEL,
        "base_url": OPENROUTER_API_BASE,
        "api_type": "openai",  # OpenRouter is OpenAI-compatible
        "api_key": OPENROUTER_API_KEY,
    }],
    "temperature": TEMPERATURE
}

# Model display name for results
def get_model_display_name():
    """Get a clean display name for the model."""
    model = OPENROUTER_MODEL
    if 'claude-sonnet-4' in model:
        return 'Claude-Sonnet-4.5'
    elif 'claude-opus-4' in model:
        return 'Claude-Opus-4.5'
    elif 'gpt-4o' in model:
        return 'GPT-4o'
    elif 'deepseek' in model:
        return 'DeepSeek-R1'
    else:
        return model.split('/')[-1]

# ========================================================================================
# VULNERABILITY DETECTION PROMPTS (imported from config.py)
# ========================================================================================

# Few-Shot Examples
EXAMPLE_C_VULN = r"""```c
char buffer[10];
strcpy(buffer, user_input);
```
Analysis: This code uses strcpy() with no bounds checking. If user_input exceeds 10 bytes, a buffer overflow occurs.
"""

EXAMPLE_C_SAFE = r"""```c
int validate_and_copy(char *dest, const char *src, size_t dest_size) {
    if (!dest || !src || dest_size == 0) return -1;
    size_t src_len = strlen(src);
    if (src_len >= dest_size) return -1;
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\0';
    return 0;
}
```
Analysis: All inputs validated, copy is bounded and null-terminated. No overflow risk.
"""

EXAMPLE_CPP_VULN = r"""```cpp
class UserManager {
private:
    std::vector<User*> users;
public:
    void addUser(const std::string& name, const std::string& password) {
        users.push_back(new User(name, password));
    }
    void deleteUser(int idx) {
        if (idx >= 0 && idx < users.size())
            users.erase(users.begin() + idx);
    }
    ~UserManager() {}
};
```
Analysis: deleteUser removes elements without deleting underlying objects. Destructor does not free memory -> memory leak.
"""

# Single Agent Prompts
VULNERABILITY_TASK_PROMPT = """Please analyze the following code:
```
{code}
```
Please indicate your result:
(1) YES: Vulnerability detected.
(2) NO: No vulnerability.
Let's think step-by-step."""

SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT = f"""You are a security expert skilled in static analysis.
Use these canonical examples as your guide:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
(1) YES

Example 2 (C safe):
{EXAMPLE_C_SAFE}
(2) NO

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
(1) YES

Now analyze the following code and respond with explicit YES or NO."""

SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT = """You are a security expert skilled in static program analysis.
Analyze the provided code and decide whether it is vulnerable (YES) or not (NO)."""
