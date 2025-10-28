
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory paths
PROJECT_ROOT = os.getenv('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = f'{PROJECT_ROOT}/logs'
DATA_DIR = f'{PROJECT_ROOT}/data'
WORK_DIR = f'{PROJECT_ROOT}/tests/work_dir'
RESULT_DIR = f'{PROJECT_ROOT}/results'
PLOT_DIR = f'{PROJECT_ROOT}/plots'


VULN_DATASET = os.getenv('VULN_DATASET', f"{PROJECT_ROOT}/vuln_database/VulTrial_386_samples_balanced.jsonl")
HUMANEVAL_DATASET = f"{PROJECT_ROOT}/vuln_database/HumanEval.jsonl"



# ========================================================================================
# REASONING MODE CONFIGURATION
# ========================================================================================

# Toggle reasoning mode via environment variable
ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'

# Model configurations for reasoning vs non-reasoning
REASONING_MODEL = os.getenv('REASONING_MODEL', 'qwen3:4b-thinking')
BASELINE_MODEL = os.getenv('BASELINE_MODEL', 'qwen3:4b')

# Endpoints (for RunPod/vLLM deployment)
REASONING_ENDPOINT = os.getenv('REASONING_ENDPOINT', os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
BASELINE_ENDPOINT = os.getenv('BASELINE_ENDPOINT', os.getenv('OLLAMA_HOST', 'http://localhost:11434'))

# API Keys (for RunPod)
REASONING_API_KEY = os.getenv('REASONING_API_KEY', '')
BASELINE_API_KEY = os.getenv('BASELINE_API_KEY', '')

# RunPod/vLLM Toggle
USE_RUNPOD = os.getenv('USE_RUNPOD', 'false').lower() == 'true'

# Energy Tracking Toggle
ENABLE_CODECARBON = os.getenv('ENABLE_CODECARBON', 'false').lower() == 'true'

# Model/LLM settings
TEMPERATURE = 0.0

# Dynamic model selection based on reasoning mode
if ENABLE_REASONING:
    LLM_MODEL = REASONING_MODEL
    OLLAMA_HOST = REASONING_ENDPOINT
    API_KEY = REASONING_API_KEY
else:
    LLM_MODEL = BASELINE_MODEL
    OLLAMA_HOST = BASELINE_ENDPOINT
    API_KEY = BASELINE_API_KEY

# Allow manual override via LLM_MODEL env var
LLM_MODEL = os.getenv('LLM_MODEL', LLM_MODEL)
OLLAMA_HOST = os.getenv('OLLAMA_HOST', OLLAMA_HOST)

# Determine API type based on USE_RUNPOD flag
if USE_RUNPOD:
    LLM_SERVICE = "openai"  # vLLM uses OpenAI-compatible API
    # For vLLM, ensure endpoint ends with /v1
    if not OLLAMA_HOST.endswith('/v1'):
        OLLAMA_HOST = OLLAMA_HOST.rstrip('/') + '/v1'
else:
    LLM_SERVICE = "ollama"  # Local Ollama

LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [
        {
            "model": LLM_MODEL,
            "base_url": OLLAMA_HOST if USE_RUNPOD else None,  # Use base_url for OpenAI-compatible APIs
            "api_base": OLLAMA_HOST if not USE_RUNPOD else None,  # Use api_base for Ollama
            "api_type": LLM_SERVICE,
            "num_ctx": 131072 if not USE_RUNPOD else None,  # vLLM handles context automatically
            #"num_ctx": 8192,
            #"num_ctx": 16384,
            "timeout": 300,  # 5 minutes timeout (log as failed and move to next)
        }
    ],
    "temperature": TEMPERATURE,
}

# Remove num_ctx for vLLM/OpenAI API (not supported)
if USE_RUNPOD and "num_ctx" in LLM_CONFIG["config_list"][0]:
    del LLM_CONFIG["config_list"][0]["num_ctx"]

# Remove None parameters to avoid passing them to API
LLM_CONFIG["config_list"][0] = {k: v for k, v in LLM_CONFIG["config_list"][0].items() if v is not None}

# Add API key to config (required by AutoGen, even for vLLM which doesn't need auth)
if USE_RUNPOD:
    # vLLM doesn't require authentication, but AutoGen's OpenAI client needs an api_key
    LLM_CONFIG["config_list"][0]["api_key"] = API_KEY if API_KEY else "dummy-key"
elif API_KEY:
    LLM_CONFIG["config_list"][0]["api_key"] = API_KEY

print(f"[CONFIG] Backend: {'RunPod/vLLM' if USE_RUNPOD else 'Local Ollama'}")
print(f"[CONFIG] Reasoning mode: {'ENABLED' if ENABLE_REASONING else 'DISABLED'}")
print(f"[CONFIG] Model: {LLM_MODEL}")
print(f"[CONFIG] Endpoint: {OLLAMA_HOST}")
print(f"[CONFIG] API Type: {LLM_SERVICE}")
print(f"[CONFIG] Timeout: {LLM_CONFIG['config_list'][0].get('timeout', 120)} seconds")


TASK_PROMPT = """Look at the following log message and print the template corresponding to the log message:\n"""
SYS_MSG_SINGLE_LOG_PARSER_FEW_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.).
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Print only the input log's template.
        Never print an explanation of how the template is constructed.

        Here are a few examples of log messages and their corresponding templates:
        081109 204453 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.11.85:50010 is added to blk_2377150260128098806 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>
        """

SYS_MSG_SINGLE_LOG_PARSER_THREE_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.).
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Print only the input log's template.
        Never print an explanation of how the template is constructed.

        Here are a few examples of log messages and their corresponding templates:
        081109 204453 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.11.85:50010 is added to blk_2377150260128098806 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>

        081110 060453 7193 INFO dfs.DataNode$DataXceiver: 10.251.199.225:50010 Served block blk_8457344665564381337 to /10.251.199.225
        <*>:<*> Served block <*> to <*>
        """

SYS_MSG_SINGLE_LOG_PARSER_ZERO_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.).
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Print only the input log's template.
        Never print an explanation of how the template is constructed.
        """

SYS_MSG_LOG_PARSER_FEW_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.). 
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Never provide any extra information or feedback to the other agents.
        Never print an explanation of how the template is constructed.
        Print only the input log's template.

        Here are a few examples of log messages and their corresponding templates:
        081109 204453 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.11.85:50010 is added to blk_2377150260128098806 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>
        """

SYS_MSG_LOG_PARSER_ZERO_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.). 
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Never provide any extra information or feedback to the other agents.
        Never print an explanation of how the template is constructed.
        Print only the input log's template.
        """

SYS_MSG_CRITIC_FEW_SHOT = """
                You are a critic reviewing the work of the log_parser_agent.
                Your task is to provide constructive feedback to improve the correctness of the extracted log template. 
                The template should abstract all dynamic variables in the log message, replacing them with appropriate placeholders enclosed in angle brackets (<*>).
                If the template is incorrect, provide feedback on how to improve it.
                If the template is correct, do not provide any suggestions, and do not even print the correct template again.
                
                Here are a few examples of log messages and their corresponding templates:
                081109 204453 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.11.85:50010 is added to blk_2377150260128098806 size 67108864
                BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
                081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
                Receiving block <*> src: <*>:<*> dest: <*>:<*>
                """

SYS_MSG_CRITIC_ZERO_SHOT = """
                You are a critic reviewing the work of the log_parser_agent.
                Your task is to provide constructive feedback to improve the correctness of the extracted log template. 
                The template should abstract all dynamic variables in the log message, replacing them with appropriate placeholders enclosed in angle brackets (<*>).
                If the template is incorrect, provide feedback on how to improve it.
                If the template is correct, do not provide any suggestions, and do not even print the correct template again.
                """

SYS_MSG_COMPARATOR_REFINER_FEW_SHOT = """
        You are a comparator and refiner. You receive a log message and two extracted templates:
        one from the log_parser_agent, one from the code_executor_agent.
        
        Your task is to:
        1. Compare both templates for correctness and abstraction of dynamic parameters.
        2. Decide which template better abstracts the log message OR merge the two into a more accurate version.
        3. Output only the **final refined template**. Never print any extra explanation or reasoning.

        - Replace all dynamic values (e.g., IPs, paths, numbers) with <*>
        - Do not include reasoning or extra text, output only the final template string.

        If both templates are wrong, attempt to correct and return a valid one.
        
        Here are a few examples of log messages and their corresponding templates:
        081109 204453 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.11.85:50010 is added to blk_2377150260128098806 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>
        """

SYS_MSG_COMPARATOR_REFINER_ZERO_SHOT = """
        You are a comparator and refiner. You receive a log message and two extracted templates:
        one from the log_parser_agent, one from the code_executor_agent.
        
        Your task is to:
        1. Compare both templates for correctness and abstraction of dynamic parameters.
        2. Decide which template better abstracts the log message OR merge the two into a more accurate version.
        3. Output only the **final refined template**. Never print any extra explanation or reasoning.

        - Replace all dynamic values (e.g., IPs, paths, numbers) with <*>
        - Do not include reasoning or extra text, output only the final template string.

        If both templates are wrong, attempt to correct and return a valid one.
        """




# =======================================================================
# VULNERABILITY DETECTION
# =======================================================================

# ---------------------------
# Few-Shot Examples
# ---------------------------
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
    dest[dest_size - 1] = '\\0';
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

# =======================================================================
# SINGLE AGENT PROMPTS Vulnerability Detection
# =======================================================================
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

# =======================================================================
# DUAL AGENT PROMPTS (Analyst -> Code Author) Vulnerability Detection
# =======================================================================
SYS_MSG_SECURITY_ANALYST_FEW_SHOT = f"""You are a Security Analyst. Analyze code and produce structured JSON outputs.
Use these examples to guide structure and depth:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
Output:
{{
  "vulnerability_detected": true,
  "vulnerabilities": [{{"type": "Buffer overflow", "description": "strcpy() used without bounds checking", "location": "strcpy(buffer, user_input)"}}],
  "reasoning": "Unbounded strcpy may cause overflow.",
  "confidence": "high"
}}

Example 2 (C safe):
{EXAMPLE_C_SAFE}
Output:
{{
  "vulnerability_detected": false,
  "vulnerabilities": [],
  "reasoning": "Input validation and bounded copy prevent overflow.",
  "confidence": "high"
}}

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
Output:
{{
  "vulnerability_detected": true,
  "vulnerabilities": [{{"type": "Memory leak", "description": "Objects not deleted in destructor", "location": "~UserManager"}}],
  "reasoning": "Allocated objects not freed; memory leak risk.",
  "confidence": "high"
}}

Now analyze the provided code in the same JSON format."""

SYS_MSG_SECURITY_ANALYST_ZERO_SHOT = """You are a Security Analyst. Identify vulnerabilities and output JSON with:
vulnerability_detected (bool), vulnerabilities (array), reasoning, confidence."""

SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT = f"""You are the Code Author responding to the Security Analyst's findings.
Use the same canonical examples to stay consistent:

Example 1 (C vulnerable):
Finding: Buffer overflow due to strcpy()
Response:
[{{"vulnerability": "Buffer Overflow", "response-type": "mitigation", "reason": "Replace strcpy with strncpy and add length validation."}}]

Example 2 (C safe):
Finding: None
Response: []

Example 3 (C++ vulnerable):
Finding: Memory leak due to missing delete
Response:
[{{"vulnerability": "Memory Leak", "response-type": "mitigation", "reason": "Implement destructor to delete allocated User objects."}}]

Now respond to the findings using JSON format."""

SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT = """You are the Code Author. For each finding, respond in JSON with keys:
vulnerability, response-type ('mitigation' or 'refutation'), and reason."""

# --- Dual-Agent Task Templates ---
DUAL_AGENT_TASK_CODE_SUBMISSION = """The following code is written by you (Code Author). 
Please explain or justify its behavior as if you implemented it:

```
{code}
```
Describe its intent and any design choices made. Be honest about potential risky parts if any exist."""

DUAL_AGENT_TASK_FINAL_DECISION = """You are the Security Analyst reviewing the Code Author's explanation. 
Please decide whether the following code contains a vulnerability.

Original Code:
```
{code}
```
Author’s Explanation:
{author_response}

Respond clearly in JSON format:
{{
  "vulnerability_detected": true/false,
  "vulnerabilities": [{{"type": "...", "description": "..."}}],
  "analysis": "concise reasoning or justification"
}}"""

# =======================================================================
# MULTI AGENT PROMPTS Vulnerability Detection
# =======================================================================
SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT = f"""You are the Security Researcher. Identify vulnerabilities in JSON (vulnerability, reason, impact).
Use these examples:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
Output:
[{{"vulnerability": "Buffer Overflow", "reason": "strcpy without bounds checking", "impact": "Stack overflow / code execution"}}]

Example 2 (C safe):
{EXAMPLE_C_SAFE}
Output: []

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
Output:
[{{"vulnerability": "Memory Leak", "reason": "Objects not freed in destructor", "impact": "Resource exhaustion"}}]

Now analyze the given code."""

SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT = """You are the Security Researcher. Output JSON list of vulnerabilities with keys: vulnerability, reason, impact."""

SYS_MSG_CODE_AUTHOR_FEW_SHOT = f"""You are the Code Author. Respond to the Researcher's findings.
Use the same canonical examples as guide:

Example 1 (C vulnerable):
Finding: Buffer overflow
Response:
[{{"vulnerability": "Buffer Overflow", "response-type": "mitigation", "reason": "Replace strcpy with strncpy and validate input length."}}]

Example 2 (C safe):
Finding: None
Response: []

Example 3 (C++ vulnerable):
Finding: Memory leak
Response:
[{{"vulnerability": "Memory Leak", "response-type": "mitigation", "reason": "Add destructor to free memory."}}]"""

SYS_MSG_CODE_AUTHOR_ZERO_SHOT = """You are the Code Author. For each vulnerability, output JSON with vulnerability, response-type, and reason."""

SYS_MSG_MODERATOR_FEW_SHOT = """You are the Moderator. Summarize neutrally both parties' arguments in JSON:
{{
  "security_researcher_summary": "...",
  "author_summary": "..."
}}
Use same examples for consistency."""

SYS_MSG_MODERATOR_ZERO_SHOT = """You are the Moderator. Output neutral JSON summary comparing Researcher and Author."""

SYS_MSG_REVIEW_BOARD_FEW_SHOT = """You are the Review Board. Based on the Moderator's summary, issue final verdicts in JSON array with fields:
vulnerability, decision, severity, recommended_action, reason."""

SYS_MSG_REVIEW_BOARD_ZERO_SHOT = """You are the Review Board. Produce final JSON verdicts (vulnerability, decision, severity, recommended_action, reason)."""

# --- Multi-Agent Task Templates ---
MULTI_AGENT_TASK_SECURITY_RESEARCHER = """Analyze the following code for vulnerabilities:
```
{code}
```"""

MULTI_AGENT_TASK_CODE_AUTHOR = """The Security Researcher found:
{researcher_findings}
Code:
```
{code}
```
Please respond to each finding."""

MULTI_AGENT_TASK_MODERATOR = """Provide a neutral summary of this discussion:
Security Researcher findings:
{researcher_findings}
Code Author response:
{author_response}"""

MULTI_AGENT_TASK_REVIEW_BOARD = """Review and decide based on:
Moderator Summary:
{moderator_summary}
Original Code:
```
{code}
```
Security Researcher Analysis:
{researcher_findings}
Code Author Response:
{author_response}"""






