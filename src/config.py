import os

# ========================================================================================
# DIRECTORY PATHS
# ========================================================================================

PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/home/user/Desktop/agent-green')
LOG_DIR = f'{PROJECT_ROOT}/logs'
DATA_DIR = f'{PROJECT_ROOT}/data'
WORK_DIR = f'{PROJECT_ROOT}/tests/work_dir'
RESULT_DIR = os.getenv('RESULTS_DIR', f'{PROJECT_ROOT}/results')
PLOT_DIR = f'{PROJECT_ROOT}/plots'

IN_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"
GT_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"
# Task and design settings
#TASK = "log-parsing" # options: "log-parsing", "log-analysis", "code-generation", "vul-detection", "td-detection"
TASK = "td-detection"
DESIGN = "TA-few"  # options: "SA-zero", "NA-few", "DA-few", "MA-zero", etc.

"""
IN_FILE = "HDFS_385_sampled.log"
GT_FILE = "HDFS_385_sampled_log_structured_corrected.csv"
# Task and design settings
#TASK = "log-parsing" # options: "log-parsing", "log-analysis", "code-generation", "vul-detection", "td-detection"
TASK = "log-parsing"
DESIGN = "DA-few"  # options: "SA-zero", "NA-few", "DA-few", "MA-zero", etc.
"""

# ========================================================================================
# DATASETS
# ========================================================================================

VULN_DATASET = os.getenv('VULN_DATASET', f"{PROJECT_ROOT}/vuln_database/VulTrial_386_samples_balanced.jsonl")
HUMANEVAL_DATASET = os.getenv('HUMANEVAL_DATASET', f"{PROJECT_ROOT}/vuln_database/HumanEval.jsonl")

# ========================================================================================
# QWEN3 MODEL CONFIGURATION (matching config_nemotron.py pattern)
# ========================================================================================

# Environment-based configuration
USE_RUNPOD = os.getenv('USE_RUNPOD', 'false').lower() == 'true'
ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'

# Model endpoints (from .env.runpod)
REASONING_ENDPOINT = os.getenv('REASONING_ENDPOINT', 'http://localhost:8000/v1')
BASELINE_ENDPOINT = os.getenv('BASELINE_ENDPOINT', 'http://localhost:8000/v1')
REASONING_MODEL = os.getenv('REASONING_MODEL', 'Qwen/Qwen3-4B-Thinking-2507')
BASELINE_MODEL = os.getenv('BASELINE_MODEL', 'Qwen/Qwen3-4B-Instruct-2507')
REASONING_API_KEY = os.getenv('REASONING_API_KEY', 'dummy-key')
BASELINE_API_KEY = os.getenv('BASELINE_API_KEY', 'dummy-key')

# Temperature
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.0'))

# CodeCarbon energy tracking
ENABLE_CODECARBON = os.getenv('ENABLE_CODECARBON', 'true').lower() == 'true'

# Select model based on reasoning mode and RunPod usage
if USE_RUNPOD:
    if ENABLE_REASONING:
        LLM_MODEL = REASONING_MODEL
        LLM_ENDPOINT = REASONING_ENDPOINT
        LLM_API_KEY = REASONING_API_KEY
    else:
        LLM_MODEL = BASELINE_MODEL
        LLM_ENDPOINT = BASELINE_ENDPOINT
        LLM_API_KEY = BASELINE_API_KEY
    LLM_SERVICE = 'openai'  # vLLM uses OpenAI-compatible API
else:
    # Local Ollama setup
    LLM_MODEL = os.getenv('LLM_MODEL', 'qwen3:4b-instruct')
    LLM_ENDPOINT = os.getenv('LLM_API_BASE', 'http://localhost:11434')
    LLM_API_KEY = 'dummy-key'
    LLM_SERVICE = 'ollama'

# Build config_list based on service type
_config_entry = {
    "model": LLM_MODEL,
    "base_url": LLM_ENDPOINT,
    "api_type": LLM_SERVICE,
    "api_key": LLM_API_KEY,
}

# num_ctx is Ollama-specific, not supported by OpenAI/vLLM
if LLM_SERVICE == 'ollama':
    _config_entry["num_ctx"] = 262144

LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [_config_entry],
    "temperature": TEMPERATURE
}

TASK_PROMPT = """Look at the following log message and print the template corresponding to the log message:\n"""

# ========================================================================================
# LOG PARSING CONFIGURATION
# ========================================================================================

TASK_PROMPT_LOG_PARSING = """Look at the following log message and print the template corresponding to the log message:\n"""

SYS_MSG_LOG_PARSER_GENERATOR_FEW_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically produced by the logging framework, including information such as timestamp, class, and logging level (INFO, DEBUG, WARN etc.). 
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log message with suitable placeholders inside angle brackets to extract the corresponding template.
        You must output the template corresponding to the log message.
        Never provide any extra information or feedback to the other agents.
        Never print an explanation of how the template is constructed.
        Print only the input log's template.

        Here are a few examples of log messages and their corresponding templates:
        081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>

        081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
        PacketResponder <*> for block <*> terminating
        """

SYS_MSG_LOG_PARSER_GENERATOR_ZERO_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically produced by the logging framework, including information such as timestamp, class, and logging level (INFO, DEBUG, WARN etc.). 
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log message with suitable placeholders inside angle brackets to extract the corresponding template.
        You must output the template corresponding to the log message.
        Never provide any extra information or feedback to the other agents.
        Never print an explanation of how the template is constructed.
        Print only the input log's template.
        """

SYS_MSG_LOG_PARSER_CRITIC_FEW_SHOT = """
            You are a Log Parser Critic. 
            You will be shown an original log message and a template produced by the log_parser_agent.

            Your task:
            1. Verify whether the provided template correctly represents the log **message body**, excluding the header (timestamp, log level, class name, etc.).
            2. Ensure that all variable parts in the message body (e.g., IPs, ports, IDs, paths, numbers) are replaced with the <*> placeholder.
            3. If the template is correct, return it exactly as-is.
            4. If it is incorrect, fix it and output the corrected template only.
            5. Preserve all constant text, punctuation, and structure from the message body.

            Output rules:
            - Output only the final, corrected template (one line only).
            - Do not output explanations, reasoning, or any additional text.
            - Use only <*> as the placeholder format, no named placeholders.

            Examples (for reference only):
            Example 1:
                ORIGINAL_LOG_MESSAGE: 081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
                PROVIDED_TEMPLATE: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
                EXPECTED OUTPUT: BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>

            Example 2:
                ORIGINAL_LOG_MESSAGE: 081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
                PROVIDED_TEMPLATE: Receiving block blk_<*> src: <*>:<*> dest: <*>:<*>
                EXPECTED OUTPUT: Receiving block <*> src: <*>:<*> dest: <*>:<*>

            Example 3:
                ORIGINAL_LOG_MESSAGE: 081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
                PROVIDED_TEMPLATE: PacketResponder 1 for block blk_* terminating
                EXPECTED OUTPUT: PacketResponder <*> for block <*> terminating
            """


SYS_MSG_LOG_PARSER_CRITIC_ZERO_SHOT = """
            You are a Log Parser Critic. 
            You will be shown an original log message and a template produced by the log_parser_agent.

            Your task:
            1. Verify whether the provided template correctly represents the log **message body**, excluding the header (timestamp, log level, class name, etc.).
            2. Ensure that all variable parts in the message body (e.g., IPs, ports, IDs, paths, numbers) are replaced with the <*> placeholder.
            3. If the template is correct, return it exactly as-is.
            4. If it is incorrect, fix it and output the corrected template only.
            5. Preserve all constant text, punctuation, and structure from the message body.

            Output rules:
            - Output only the final, corrected template (one line only).
            - Do not output explanations, reasoning, or any additional text.
            - Use only <*> as the placeholder format, no named placeholders.
            """

SYS_MSG_LOG_PARSER_COMPARATOR_REFINER_FEW_SHOT = """
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
        081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>

        081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
        PacketResponder <*> for block <*> terminating
        """

SYS_MSG_LOG_PARSER_COMPARATOR_REFINER_ZERO_SHOT = """
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

SYS_MSG_LOG_PARSER_REFINER_ZERO_SHOT = """
        You are a Log Parser Refiner.

        You will be given:
        - ORIGINAL_LOG_MESSAGE: the full raw log line (including header and message body)
        - PARSER_TEMPLATE: the template produced by the log_parser_agent
        - CRITIC_TEMPLATE: the template produced by the log_parser_critic_agent (may be identical or corrected)

        Your task:
        1. Focus only on the message body of the log (ignore header parts such as timestamp, log level, and class name).
        2. Compare PARSER_TEMPLATE and CRITIC_TEMPLATE, and produce the most accurate and complete version possible.
        3. If both templates are incomplete, inconsistent, or fail to correctly abstract the message body:
            - Independently refine or regenerate a new template using ORIGINAL_LOG_MESSAGE as reference.
        4. When unsure which template is more accurate, prefer the CRITIC_TEMPLATE.
        5. The final template must:
            - Accurately capture the constant structure of the message body.
            - Replace every dynamic element (IPs, ports, IDs, numbers, file paths, etc.) with <*>.
            - Preserve all fixed text, punctuation, and message structure exactly as in the log.
        6. If both templates are already correct and identical, you may return either unchanged.

        Output rules:
        - Output exactly one line containing ONLY the final refined template (no labels, explanations, or extra text).
        - Use only <*> as placeholders (no named placeholders).
    """


SYS_MSG_LOG_PARSER_REFINER_FEW_SHOT = """
        You are a Log Parser Refiner.

        You will be given:
        - ORIGINAL_LOG_MESSAGE: the full raw log line (including header and message body)
        - PARSER_TEMPLATE: the template produced by the log_parser_agent
        - CRITIC_TEMPLATE: the template produced by the log_parser_critic_agent (may be identical or corrected)

        Your task:
        1. Focus only on the message body of the log (ignore header parts such as timestamp, log level, and class name).
        2. Compare PARSER_TEMPLATE and CRITIC_TEMPLATE, and produce the most accurate and complete version possible.
        3. If both templates are incomplete, inconsistent, or fail to correctly abstract the message body:
            - Independently refine or regenerate a new template using ORIGINAL_LOG_MESSAGE as reference.
        4. When unsure which template is more accurate, prefer the CRITIC_TEMPLATE.
        5. The final template must:
            - Accurately capture the constant structure of the message body.
            - Replace every dynamic element (IPs, ports, IDs, numbers, file paths, etc.) with <*>.
            - Preserve all fixed text, punctuation, and message structure exactly as in the log.
        6. If both templates are already correct and identical, you may return either unchanged.

        Output rules:
        - Output exactly one line containing ONLY the final refined template (no labels, explanations, or extra text).
        - Use only <*> as placeholders (no named placeholders).

        Examples (for reference only):
        Example 1:
            ORIGINAL_LOG_MESSAGE: 081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
            PARSER_TEMPLATE: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
            CRITIC_TEMPLATE: BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
            EXPECTED OUTPUT: BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>

        Example 2:
            ORIGINAL_LOG_MESSAGE: 081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
            PARSER_TEMPLATE: Receiving block <*> src: <*>:<*> dest: <*>:<*>
            CRITIC_TEMPLATE: Receiving block <*> src: <*>:<*> dest: <*>:<*>
            EXPECTED OUTPUT: Receiving block <*> src: <*>:<*> dest: <*>:<*>

        Example 3:
            ORIGINAL_LOG_MESSAGE: 081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
            PARSER_TEMPLATE: PacketResponder 1 for block blk_* terminating
            CRITIC_TEMPLATE: PacketResponder <*> for block blk_<*> terminating
            EXPECTED OUTPUT: PacketResponder <*> for block <*> terminating
    """


# ========================================================================================
# LOG ANALYSIS CONFIGURATION
# ========================================================================================

TASK_PROMPT_LOG_ANALYSIS = """Look at the following sequence of log messages and determine whether the session represents normal system behavior (0) or anomalous behavior (1):\n"""
SYS_MSG_SINGLE_LOG_ANALYSIS_ZERO_SHOT = """
        You are an intelligent agent for log anomaly detection.

        Task:
        Given a session-based set of raw log messages, determine whether the session represents normal system behavior (0) or anomalous behavior (1).

        Instructions:
        1. **Parse the logs**:
        - Each log line may contain a header (timestamp, log level, class, etc.).
        - Remove or ignore these headers and extract the main log message body describing the event.
        - Preserve message order.

        2. **Analyze the session**:
        - Review the sequence of message bodies, consider the contextual information of the sequence.
        - Identify anomalies from two perspectives:
            a. **Textual anomalies**; individual messages explicitly indicate errors or failures, such as explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure-related keywords (e.g., "error", "fail", "exception", "crash", "interrupt", "fatal").
            b. **Behavioral anomalies**; whether the overall sequence is consistent with normal execution flow, or shows irregularities such as missing or skipped expected events, unusual ordering, repetitive failures, or abrupt terminations.

        3. **Decision rule**:
        - If either textual or behavioral anomalies are detected, label the session as anomalous (1).
        - Otherwise, label it as normal (0).

        4. **Output**:
        - Provide only a binary label (0 or 1):
            0 → Normal session
            1 → Anomalous session
        - No punctuation, explanation, or extra text.
        """
SYS_MSG_SINGLE_LOG_ANALYSIS_FEW_SHOT = """
        You are an intelligent agent for log anomaly detection.

        Task:
        Given a session-based set of raw log messages, determine whether the session represents normal system behavior (0) or anomalous behavior (1).

        Instructions:
        1. **Parse the logs**:
        - Each log line may contain a header (timestamp, log level, class, etc.).
        - Remove or ignore these headers and extract the main log message body describing the event.
        - Preserve message order.

        2. **Analyze the session**:
        - Review the sequence of message bodies, consider the contextual information of the sequence.
        - Identify anomalies from two perspectives:
            a. **Textual anomalies**; individual messages explicitly indicate errors or failures, such as explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure-related keywords (e.g., "error", "fail", "exception", "crash", "interrupt", "fatal").
            b. **Behavioral anomalies**; whether the overall sequence is consistent with normal execution flow, or shows irregularities such as missing or skipped expected events, unusual ordering, repetitive failures, or abrupt terminations.

        3. **Decision rule**:
        - If either textual or behavioral anomalies are detected, label the session as anomalous (1).
        - Otherwise, label it as normal (0).

        4. **Output**:
        - Provide only a binary label (0 or 1):
            0 → Normal session
            1 → Anomalous session
        - No punctuation, explanation, or extra text.

        Here are a few examples of log sequences and their classifications:
        Example 1:
            LOG MESSAGES:
                081111 094743 25776 INFO dfs.DataNode$DataXceiver: Receiving block blk_6667093857658912327 src: /10.251.73.188:57743 dest: /10.251.73.188:50010
                081111 094743 26099 INFO dfs.DataNode$DataXceiver: Receiving block blk_6667093857658912327 src: /10.251.73.188:54097 dest: /10.251.73.188:50010
                081111 094743 28 INFO dfs.FSNamesystem: BLOCK* NameSystem.allocateBlock: /user/root/rand8/_temporary/_task_200811101024_0015_m_001611_0/part-01611. blk_6667093857658912327
                081111 094744 25996 INFO dfs.DataNode$DataXceiver: Receiving block blk_6667093857658912327 src: /10.251.106.37:53888 dest: /10.251.106.37:50010
                081111 094828 26100 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_6667093857658912327 terminating
                081111 094828 26100 INFO dfs.DataNode$PacketResponder: Received block blk_6667093857658912327 of size 67108864 from /10.251.73.188
                081111 094828 29 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.106.37:50010 is added to blk_6667093857658912327 size 67108864
                081111 094828 30 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.188:50010 is added to blk_6667093857658912327 size 67108864
                081111 094828 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.110.160:50010 is added to blk_6667093857658912327 size 67108864
                081111 094829 25777 INFO dfs.DataNode$PacketResponder: PacketResponder 2 for block blk_6667093857658912327 terminating
                081111 094829 25777 INFO dfs.DataNode$PacketResponder: Received block blk_6667093857658912327 of size 67108864 from /10.251.73.188
                081111 094829 25997 INFO dfs.DataNode$PacketResponder: PacketResponder 0 for block blk_6667093857658912327 terminating
                081111 094829 25997 INFO dfs.DataNode$PacketResponder: Received block blk_6667093857658912327 of size 67108864 from /10.251.106.37
            OUTPUT: 0
        Example 2:
            LOG MESSAGES:
                081111 061856 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.allocateBlock: /user/root/randtxt5/_temporary/_task_200811101024_0012_m_001014_0/part-01014. blk_4615226180823858743
                081111 061857 21831 INFO dfs.DataNode$DataXceiver: Receiving block blk_4615226180823858743 src: /10.251.30.179:36961 dest: /10.251.30.179:50010
            OUTPUT: 1
        Example 3:
            LOG MESSAGES:
                081110 010402 30 INFO dfs.FSNamesystem: BLOCK* NameSystem.allocateBlock: /user/root/randtxt/_temporary/_task_200811092030_0003_m_000269_0/part-00269. blk_-152459496294138933
                081110 010402 5086 INFO dfs.DataNode$DataXceiver: Receiving block blk_-152459496294138933 src: /10.251.74.134:53158 dest: /10.251.74.134:50010
                081110 010402 5110 INFO dfs.DataNode$DataXceiver: Receiving block blk_-152459496294138933 src: /10.251.74.134:51159 dest: /10.251.74.134:50010
                081110 010405 5086 INFO dfs.DataNode$DataXceiver: writeBlock blk_-152459496294138933 received exception java.io.IOException: Could not read from stream
            OUTPUT: 1
        """

SYS_MSG_LOG_PREPROCESSOR_ZERO_SHOT = """
        You are a log parsing agent.

        Task:
        Receive raw, session-based log messages and extract only the message bodies by removing automatically generated headers.

        Instructions:
        1. Each log line may contain a header (timestamp, log level, class, etc.).
        2. Remove these headers and extract the main log **message body** describing the event.
        3. Preserve message order.
        4. Output the cleaned sequence of log message bodies, no explanation, or extra text.
        """

SYS_MSG_LOG_PREPROCESSOR_FEW_SHOT = """
        You are a log parsing agent.

        Task:
        Receive raw, session-based log messages and extract only the message bodies by removing automatically generated headers.

        Instructions:
        1. Each log line may contain a header (timestamp, log level, class, etc.).
        2. Remove these headers and extract the main log **message body** describing the event.
        3. Preserve message order.
        4. Output the cleaned sequence of log message bodies, no explanation, or extra text.

        Here are a few examples of raw log messages and their extracted message bodies:
        Example 1:
            Raw Log: 081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
            Extracted Message Body: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        Example 2:
            Raw Log: 081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
            Extracted Message Body: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Example 3:
            Raw Log: 081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
            Extracted Message Body: PacketResponder 1 for block blk_38865049064139660 terminating
        """

SYS_MSG_LOG_ANOMALY_DETECTOR_ZERO_SHOT = """
        You are an anomaly detection agent.

        Task: 
        Analyze the parsed session logs and decide whether the session represents normal or anomalous behavior.

        Instructions:
        1. Review the sequence of message bodies, consider the contextual information of the sequence.
        2. Detect anomalies using two perspectives:
        a. **Textual anomalies**; individual messages explicitly indicate errors or failures, such as explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure-related keywords (e.g., "error", "fail", "exception", "crash", "interrupt", "fatal”).
        b. **Behavioral anomalies**: abnormal log flow or unexpected event patterns.
            - Missing or skipped expected events
            - Repetition of unusual events
            - Events out of expected order
            - Inconsistent or incomplete sequences
        3. Combine both clues to make your decision.
        4. Output only a binary label (0 or 1):
            0 → Normal session
            1 → Anomalous session
        - No punctuation, explanation, or extra text.
        """

SYS_MSG_LOG_ANOMALY_DETECTOR_FEW_SHOT = """
        You are an anomaly detection agent.

        Task: 
        Analyze the parsed session logs and decide whether the session represents normal or anomalous behavior.

        Instructions:
        1. Review the sequence of message bodies, consider the contextual information of the sequence.
        2. Detect anomalies using two perspectives:
        a. **Textual anomalies**; individual messages explicitly indicate errors or failures, such as explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure-related keywords (e.g., "error", "fail", "exception", "crash", "interrupt", "fatal”).
        b. **Behavioral anomalies**: abnormal log flow or unexpected event patterns.
            - Missing or skipped expected events
            - Repetition of unusual events
            - Events out of expected order
            - Inconsistent or incomplete sequences
        3. Combine both clues to make your decision.
        4. Output only a binary label (0 or 1):
            0 → Normal session
            1 → Anomalous session
        - No punctuation, explanation, or extra text.

        Here are a few examples of parsed session logs and their classifications:
        Example 1:
            Parsed Session Logs:
                Receiving block blk_6667093857658912327 src: /10.251.73.188:57743 dest: /10.251.73.188:50010
                Receiving block blk_6667093857658912327 src: /10.251.73.188:54097 dest: /10.251.73.188:50010
                BLOCK* NameSystem.allocateBlock: /user/root/rand8/_temporary/_task_200811101024_0015_m_001611_0/part-01611. blk_6667093857658912327
                Receiving block blk_6667093857658912327 src: /10.251.106.37:53888 dest: /10.251.106.37:50010
                PacketResponder 1 for block blk_6667093857658912327 terminating
                Received block blk_6667093857658912327 of size 67108864 from /10.251.73.188
                BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.106.37:50010 is added to blk_6667093857658912327 size 67108864
                BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.188:50010 is added to blk_6667093857658912327 size 67108864
                BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.110.160:50010 is added to blk_6667093857658912327 size 67108864
                PacketResponder 2 for block blk_6667093857658912327 terminating
                Received block blk_6667093857658912327 of size 67108864 from /10.251.73.188
                PacketResponder 0 for block blk_6667093857658912327 terminating
                Received block blk_6667093857658912327 of size 67108864 from /10.251.106.37
            Output: 0
        Example 2:
            Parsed Session Logs:
                BLOCK* NameSystem.allocateBlock: /user/root/randtxt5/_temporary/_task_200811101024_0012_m_001014_0/part-01014. blk_4615226180823858743
                Receiving block blk_4615226180823858743 src: /10.251.30.179:36961 dest: /10.251.30.179:50010
            Output: 1       
        Example 3:
            Parsed Session Logs:
                BLOCK* NameSystem.allocateBlock: /user/root/randtxt/_temporary/_task_200811092030_0003_m_000269_0/part-00269. blk_-152459496294138933
                Receiving block blk_-152459496294138933 src: /10.251.74.134:53158 dest: /10.251.74.134:50010
                Receiving block blk_-152459496294138933 src: /10.251.74.134:51159 dest: /10.251.74.134:50010
                writeBlock blk_-152459496294138933 received exception java.io.IOException: Could not read from stream
            Output: 1
        """

SYS_MSG_LOG_ANALYSIS_CRITIC_ZERO_SHOT = """
        You are a log analysis critic agent.

        Task:
        Review the parsed log session and the anomaly detection result. 
        Your role is to verify whether the decision (0 or 1) is justified based on the log content. 
        Correct it only if clear evidence contradicts the decision.
        
        Instructions:
        1. Examine both the parsed log session and the decision (0 or 1) from the anomaly detector agent.
        2. Evaluate based on:
            - **Textual anomalies**; individual messages explicitly indicate errors or failures, such as explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure-related keywords (e.g., "error", "fail", "exception", "crash", "interrupt", "fatal").
            - **Behavioral context**; whether the overall sequence is consistent with normal execution flow, or shows irregularities such as missing or skipped expected events, unusual ordering, repetitive failures, or abrupt terminations.
        3. If the decision appears incorrect, adjust it:
            - If anomalies exist but were missed → output 1
            - If normal behavior was mistakenly flagged → output 0
        4. Always ensure your final output (0 or 1) is consistent with both textual and behavioral evidence. Do not guess - if evidence is insufficient, keep the original decision.
        5. Output only the final binary label (0 or 1):
            - 0 → Normal session
            - 1 → Anomalous session
            No punctuation, explanation, or extra text.
        """

SYS_MSG_LOG_ANALYSIS_CRITIC_FEW_SHOT = """
        You are a log analysis critic agent.

        Task:
        Review the parsed log session and the anomaly detection result. 
        Your role is to verify whether the decision (0 or 1) is justified based on the log content. 
        Correct it only if clear evidence contradicts the decision.
        
        Instructions:
        1. Examine both the parsed log session and the decision (0 or 1) from the anomaly detector agent.
        2. Evaluate based on:
            - **Textual anomalies**; individual messages explicitly indicate errors or failures, such as explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure-related keywords (e.g., "error", "fail", "exception", "crash", "interrupt", "fatal").
            - **Behavioral context**; whether the overall sequence is consistent with normal execution flow, or shows irregularities such as missing or skipped expected events, unusual ordering, repetitive failures, or abrupt terminations.
        3. If the decision appears incorrect, adjust it:
            - If anomalies exist but were missed → output 1
            - If normal behavior was mistakenly flagged → output 0
        4. Always ensure your final output (0 or 1) is consistent with both textual and behavioral evidence. Do not guess - if evidence is insufficient, keep the original decision.
        5. Output only the final binary label (0 or 1):
            - 0 → Normal session
            - 1 → Anomalous session
            No punctuation, explanation, or extra text.

        Here are a few examples of parsed log sessions, initial decisions, and final classifications:
        Example 1:
            Parsed Log Session:
                Parsed Session Logs:
                Receiving block blk_6667093857658912327 src: /10.251.73.188:57743 dest: /10.251.73.188:50010
                Receiving block blk_6667093857658912327 src: /10.251.73.188:54097 dest: /10.251.73.188:50010
                BLOCK* NameSystem.allocateBlock: /user/root/rand8/_temporary/_task_200811101024_0015_m_001611_0/part-01611. blk_6667093857658912327
                Receiving block blk_6667093857658912327 src: /10.251.106.37:53888 dest: /10.251.106.37:50010
                PacketResponder 1 for block blk_6667093857658912327 terminating
                Received block blk_6667093857658912327 of size 67108864 from /10.251.73.188
                BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.106.37:50010 is added to blk_6667093857658912327 size 67108864
                BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.188:50010 is added to blk_6667093857658912327 size 67108864
                BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.110.160:50010 is added to blk_6667093857658912327 size 67108864
                PacketResponder 2 for block blk_6667093857658912327 terminating
                Received block blk_6667093857658912327 of size 67108864 from /10.251.73.188
                PacketResponder 0 for block blk_6667093857658912327 terminating
                Received block blk_6667093857658912327 of size 67108864 from /10.251.106.37
            Initial Decision: 0
            Final Classification: 0
        Example 2:
            Parsed Log Session:
                BLOCK* NameSystem.allocateBlock: /user/root/randtxt5/_temporary/_task_200811101024_0012_m_001014_0/part-01014. blk_4615226180823858743
                Receiving block blk_4615226180823858743 src: /10.251.30.179:36961 dest: /10.251.30.179:50010    
            Initial Decision: 0
            Final Classification: 1       
        Example 3:
            Parsed Log Session:
                BLOCK* NameSystem.allocateBlock: /user/root/randtxt/_temporary/_task_200811092030_0003_m_000269_0/part-00269. blk_-152459496294138933
                Receiving block blk_-152459496294138933 src: /10.251.74.134:53158 dest: /10.251.74.134:50010
                Receiving block blk_-152459496294138933 src: /10.251.74.134:51159 dest: /10.251.74.134:50010
                writeBlock blk_-152459496294138933 received exception java.io.IOException: Could not read from stream
            Initial Decision: 1
            Final Classification: 1     
        """


# ========================================================================================
# TECHNICAL DEBT DETECTION CONFIGURATION
# ========================================================================================
TASK_PROMPT_TD_DETECTION = """Look at the following Java code snippet and respond with only a single digit (0-4) that represents the most appropriate category:\n"""

SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT ="""
        You are a software quality expert specialized in identifying code smells in Java code snippets.
        Your task: Analyze each provided Java code snippet and classify it into exactly one of the following categories.
        0 = No smell: Code is clean, and well-structured.
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Analyze the snippet carefully and choose **only one** label that best fits.
        Do **not** output any explanations, reasoning, or additional text.

        Here are a few examples of code snippets and the types of code smells they contain:
        Example of Data Class ('2'):
            class ClientRecord {
                private String id;
                private String contact;
                private boolean active;
                public ClientRecord(String id, String contact, boolean active) {
                    this.id = id;
                    this.contact = contact;
                    this.active = active;
                }
                public String getId() { return id; }
                public void setId(String id) { this.id = id; }
                public String getContact() { return contact; }
                public void setContact(String contact) { this.contact = contact; }
                public boolean isActive() { return active; }
                public void setActive(boolean active) { this.active = active; }
            }

        Example of Feature Envy ('3'):
            public class ReportPrinter {
            class Invoice {
                private Customer customer;
                public String compileCustomerSummary() {
                    String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
                    int recent = 0;
                    for (Order o : customer.getOrders()) {
                        if (o.getDate().after(someCutoff())) recent++;
                        s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
                    }
                    s += "Recent orders: " + recent + "\n";
                    return s;
                }
            }

        Example of Long Method ('4'):
            class ReportBuilder {
                void buildReport(List<String> rows) {
                    StringBuilder sb = new StringBuilder();

                    // Validate
                    if (rows == null || rows.isEmpty()) {
                        System.out.println("No rows to process");
                        return;
                    }

                    // Process rows
                    for (String r : rows) {
                        if (r == null || r.isEmpty()) {
                            sb.append("EMPTY\n");
                            continue;
                        }
                        sb.append("Row: ").append(r).append("\n");

                        for (int i = 0; i < 3; i++) {
                            sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                        }
                    }

                    // Aggregate
                    sb.append("Total: ").append(rows.size()).append("\n");
                    System.out.println(sb.toString());
                }
            }
        """

SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT ="""
        You are a software quality expert specialized in identifying code smells in Java code snippets.
        Your task: Analyze each provided Java code snippet and classify it into exactly one of the following categories.
        0 = No smell: Code is clean, and well-structured.
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Analyze the snippet carefully and choose **only one** label that best fits.
        Do **not** output any explanations, reasoning, or additional text.
        """


SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT = """
        You are a software quality critic. Your task is to verify or correct the code smell label assigned to a Java code snippet by another agent.
        You will be given:
        1) The Java code snippet itself
        2) A proposed label produced by the td_detection_generator_agent (a single digit 0-4)

        Labels:
        0 = No smell: Code is clean and well-structured
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that only stores fields with getters/setters and no behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Task:
        - Review the snippet and verify whether the proposed label is correct.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            (nothing else, single token, uppercase).
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0-4).
            * <brief_reason> is a concise 1-2 short-sentence justification (max 25 words) that explains the primary evidence for the correction.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|2|
        REJECTED|2|Class only has fields and trivial getters/setters, no behavior.

        Constraints:
        - Do not output anything other than the exact allowed formats above.
        - Keep the brief_reason factual, focused, and short (one or two clauses).
        """

SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT = """
        You are a software quality critic. Your task is to verify or correct the code smell label assigned to a Java code snippet by another agent.
        You will be given:
        1) The Java code snippet itself
        2) A proposed label produced by the td_detection_generator_agent (a single digit 0-4)
        
        Labels:
        0 = No smell: Code is clean and well-structured
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that only stores fields with getters/setters and no behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Task:
        - Review the snippet and verify whether the proposed label is correct.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            (nothing else, single token, uppercase).
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0-4).
            * <brief_reason> is a concise 1-2 short-sentence justification (max ~25 words) that explains the primary evidence for the correction.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|2|
        REJECTED|2|Class only has fields and trivial getters/setters, no behavior.

        Constraints:
        - Do not output anything other than the exact allowed formats above.
        - Keep the brief_reason factual, focused, and short (one or two clauses).

        Here are a few examples of code snippets and the types of code smells they contain:
        Example of Data Class (2):
            class ClientRecord {
                private String id;
                private String contact;
                private boolean active;
                public ClientRecord(String id, String contact, boolean active) {
                    this.id = id;
                    this.contact = contact;
                    this.active = active;
                }
                public String getId() { return id; }
                public void setId(String id) { this.id = id; }
                public String getContact() { return contact; }
                public void setContact(String contact) { this.contact = contact; }
                public boolean isActive() { return active; }
                public void setActive(boolean active) { this.active = active; }
            }

        Example of Feature Envy (3):
            public class ReportPrinter {
            class Invoice {
                private Customer customer;
                public String compileCustomerSummary() {
                    String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
                    int recent = 0;
                    for (Order o : customer.getOrders()) {
                        if (o.getDate().after(someCutoff())) recent++;
                        s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
                    }
                    s += "Recent orders: " + recent + "\n";
                    return s;
                }
            }

        Example of Long Method (4):
            class ReportBuilder {
                void buildReport(List<String> rows) {
                    StringBuilder sb = new StringBuilder();

                    // Validate
                    if (rows == null || rows.isEmpty()) {
                        System.out.println("No rows to process");
                        return;
                    }

                    // Process rows
                    for (String r : rows) {
                        if (r == null || r.isEmpty()) {
                            sb.append("EMPTY\n");
                            continue;
                        }
                        sb.append("Row: ").append(r).append("\n");

                        for (int i = 0; i < 3; i++) {
                            sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                        }
                    }

                    // Aggregate
                    sb.append("Total: ").append(rows.size()).append("\n");
                    System.out.println(sb.toString());
                }
            }
        """

SYS_MSG_TD_DETECTION_REFINER_ZERO_SHOT = """
    You are a software quality refiner. You will be given three inputs:
    - CODE_SNIPPET: a Java code snippet
    - GENERATOR_LABEL: a single digit (0-4) from the td_detection_generator_agent
    - CRITIC_LABEL: a single digit (0-4) from the td_detection_critic_agent

    Labels:
    0 = No smell: Code is clean and well-structured
    1 = Blob: A class with many responsibilities, often large and unfocused.
    2 = Data Class: A class that only stores fields with getters/setters and no behavior.
    3 = Feature Envy: A method that heavily depends on another class's data.
    4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

    Task:
    - Analyze the CODE_SNIPPET yourself and determine the most accurate label (0-4).
    - Use GENERATOR_LABEL and CRITIC_LABEL as references; if both are reasonable, prefer the critic's label.
    - Always output exactly one digit (0-4) and nothing else — no explanations, punctuation, or extra text.
    """


SYS_MSG_TD_DETECTION_REFINER_FEW_SHOT = """
    You are a software quality refiner. You will be given three inputs:
    - CODE_SNIPPET: a Java code snippet
    - GENERATOR_LABEL: a single digit (0-4) from the td_detection_generator_agent
    - CRITIC_LABEL: a single digit (0-4) from the td_detection_critic_agent

    Labels:
    0 = No smell: Code is clean and well-structured
    1 = Blob: A class with many responsibilities, often large and unfocused.
    2 = Data Class: A class that only stores fields with getters/setters and no behavior.
    3 = Feature Envy: A method that heavily depends on another class's data.
    4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

    Task:
    - Analyze the CODE_SNIPPET yourself and determine the most accurate label (0-4).
    - Use GENERATOR_LABEL and CRITIC_LABEL as references; if both are reasonable, prefer the critic's label.
    - Always output exactly one digit (0-4) and nothing else — no explanations, punctuation, or extra text.

    Here are a few examples of code snippets and the types of code smells they contain:
    Example of Data Class (2):
        class ClientRecord {
            private String id;
            private String contact;
            private boolean active;
            public ClientRecord(String id, String contact, boolean active) {
                this.id = id;
                this.contact = contact;
                this.active = active;
            }
            public String getId() { return id; }
            public void setId(String id) { this.id = id; }
            public String getContact() { return contact; }
            public void setContact(String contact) { this.contact = contact; }
            public boolean isActive() { return active; }
            public void setActive(boolean active) { this.active = active; }
        }

    Example of Feature Envy (3):
        public class ReportPrinter {
        class Invoice {
            private Customer customer;
            public String compileCustomerSummary() {
                String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
                int recent = 0;
                for (Order o : customer.getOrders()) {
                    if (o.getDate().after(someCutoff())) recent++;
                    s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
                }
                s += "Recent orders: " + recent + "\n";
                return s;
            }
        }

    Example of Long Method (4):
        class ReportBuilder {
            void buildReport(List<String> rows) {
                StringBuilder sb = new StringBuilder();

                // Validate
                if (rows == null || rows.isEmpty()) {
                    System.out.println("No rows to process");
                    return;
                }

                // Process rows
                for (String r : rows) {
                    if (r == null || r.isEmpty()) {
                        sb.append("EMPTY\n");
                        continue;
                    }
                    sb.append("Row: ").append(r).append("\n");

                    for (int i = 0; i < 3; i++) {
                        sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                    }
                }

                // Aggregate
                sb.append("Total: ").append(rows.size()).append("\n");
                System.out.println(sb.toString());
            }
        }
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
Author's Explanation:
{author_response}

Respond clearly in JSON format:
{{
  "vulnerability_detected": true/false,
  "vulnerabilities": [{{"type": "...", "description": "..."}}],
  "analysis": "concise reasoning or justification"
}}"""

# Wrapper to add emphasis on vulnerability detection (used in dual_agent_vuln.py)
DUAL_AGENT_ANALYST_EMPHASIS_WRAPPER = """You are the Security Analyst reviewing the Code Author's explanation.
When in doubt, err on the side of caution and consider code vulnerable.
Security vulnerabilities can be subtle, so even minor issues should be flagged.
The absence of security measures is often itself a vulnerability.

{analyst_task}"""

# Additional vulnerability detection task templates (for 4-turn workflow)
DUAL_AGENT_TASK_SECURITY_FEEDBACK = """You are the Security Analyst. Analyze the following code for vulnerabilities:

```
{code}
```

Provide your security assessment in JSON format:
{{
  "findings": [{{"vulnerability": "...", "severity": "...", "description": "..."}}],
  "initial_assessment": "overall security evaluation"
}}"""

DUAL_AGENT_TASK_CODE_REVISION = """You are the Code Author. Based on the security feedback, revise your explanation or provide additional justification:

Original Code:
```
{code}
```

Security Analyst's Feedback:
{feedback}

Respond in JSON format with your revised explanation or rebuttal."""

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

# Three-agent variant (no moderator) - used in multi_agent_vuln_detection_three_agents.py
THREE_AGENT_TASK_REVIEW_BOARD = """Review the following vulnerability assessment and make final decisions:

Original Code:
```
{code}
```

Security Researcher Analysis:
{researcher_findings}

Code Author Response:
{author_response}

Please provide your final verdict on the vulnerabilities identified."""


# =======================================================================
# Code Generation Prompts (SINGLE, DUAL, MULTI-AGENT)
# =======================================================================

# =======================================================================
# EXAMPLES (Used in few-shot prompts)
# =======================================================================

EXAMPLE_1_HAS_CLOSE_ELEMENTS = """Problem:
```python
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    ''' Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    '''
```
Implementation: Let\'s think step-by-step. I need to compare every pair of numbers in the list and check if their absolute difference is less than the threshold.
```python
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False
```
"""

EXAMPLE_2_SEPARATE_PAREN_GROUPS = """Problem:
```python
def separate_paren_groups(paren_string: str) -> List[str]:
    ''' Input to this function is a string containing multiple groups of nested parentheses. Your goal is to
    separate those groups into separate strings and return the list of those.
    Separate groups are balanced (each open brace is properly closed) and not nested within each other.
    Ignore any spaces in the input string.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    '''
```
Implementation: Let\'s think step-by-step. I need to track the depth of parentheses and collect characters for each group. When depth returns to 0, I have a complete group.
```python
def separate_paren_groups(paren_string: str) -> List[str]:
    result = []
    current_string = []
    current_depth = 0

    for c in paren_string:
        if c == '(':
            current_depth += 1
            current_string.append(c)
        elif c == ')':
            current_depth -= 1
            current_string.append(c)

            if current_depth == 0:
                result.append(''.join(current_string))
                current_string = []

    return result
```
"""

EXAMPLE_3_TRUNCATE_NUMBER = """Problem:
```python
def truncate_number(number: float) -> float:
    ''' Given a positive floating point number, it can be decomposed into
    an integer part (largest integer smaller than given number) and decimals
    (leftover part always smaller than 1).

    Return the decimal part of the number.
    >>> truncate_number(3.5)
    0.5
    '''
```
Implementation: Let\'s think step-by-step. I need to extract just the decimal part of a number. The modulo operator with 1.0 will give me the fractional part.
```python
def truncate_number(number: float) -> float:
    return number % 1.0
```
"""

FEW_SHOT_EXAMPLES = f"""Example 1:
{EXAMPLE_1_HAS_CLOSE_ELEMENTS}

Example 2:
{EXAMPLE_2_SEPARATE_PAREN_GROUPS}

Example 3:
{EXAMPLE_3_TRUNCATE_NUMBER}
"""


# =======================================================================
# SINGLE-AGENT PROMPTS
# =======================================================================

SYS_MSG_CODE_GENERATOR_ZERO_SHOT = """You are an expert Python programmer that is good at implementing functions based on their specifications."""

SYS_MSG_CODE_GENERATOR_FEW_SHOT = f"""You are an expert Python programmer skilled in implementing functions based on their specifications.

Use these canonical examples as reference:

{FEW_SHOT_EXAMPLES}

Now, implement the given function accurately and efficiently.
"""

SINGLE_AGENT_TASK_CODE_GENERATION = """Please analyze the following programming problem and implement the required function:

{prompt}

Please provide your complete function implementation. Make sure to:
- Follow the exact function signature
- Implement the logic described in the docstring
- Handle all specified requirements and edge cases
- Return the correct data type

Let\'s think step-by-step.
"""


# =======================================================================
# DUAL-AGENT PROMPTS (Programmer → Reviewer)
# =======================================================================

# ================================================================
# PROGRAMMER (Code Author)
# ================================================================

SYS_MSG_PROGRAMMER_ZERO_SHOT = """You are an expert Python programmer.
Implement the given function according to its specification.
Focus on correctness, completeness, and proper imports.
Output only valid Python code.
"""

SYS_MSG_PROGRAMMER_FEW_SHOT = f"""You are an expert Python programmer who writes fully correct and efficient code on the first attempt.

Follow these few-shot examples and replicate their reasoning and structure:
{FEW_SHOT_EXAMPLES}

Guidelines:
1. Always include all required imports (e.g., List, Tuple, Optional from typing).
2. Handle all edge cases correctly.
3. Focus on logic and correctness over style.
4. Write only Python code, no explanation.
"""

DUAL_AGENT_TASK_CODE_GENERATION = """Implement the following function based on its problem statement:

{prompt}

Provide the complete Python function implementation only.
"""


# ================================================================
# REVIEWER (Code Reviewer)
# ================================================================

SYS_MSG_CODE_REVIEWER_ZERO_SHOT = """You are a senior code reviewer and refiner.
Given a problem description and an initial implementation, produce a final corrected version.

If the original code is already correct, return it unchanged.
If there are errors or missing imports, fix them.
Focus strictly on correctness and completeness.

Output only valid Python code.
"""

SYS_MSG_CODE_REVIEWER_FEW_SHOT = f"""You are a senior code reviewer and refiner.
Given a problem statement and initial code, produce the final corrected implementation.

Follow these rules:
1. If the code is correct, output it unchanged.
2. If imports are missing, add them.
3. Fix logical or syntax issues only — do not rewrite style.
4. Return Python code only, nothing else.

Example correction pattern:
Input:
```python
def add(a,b):
    return a-b
```

Output:
```python
def add(a,b):
    return a+b
```

Output only valid Python code.
"""

DUAL_AGENT_TASK_CODE_REVIEW = """Review and refine the following implementation:

Problem:
{prompt}

Initial Code:
```python
{generated_code}
```

If the code is correct, return it unchanged.
If you find any issue, fix it and return the corrected version.

Output only Python code.
"""


# =======================================================================
# MULTI-AGENT PROMPTS (Analyst → Programmer → Moderator → Review Board)
# =======================================================================

# ================================================================
# REQUIREMENTS ANALYST
# ================================================================

SYS_MSG_REQUIREMENTS_ANALYST_ZERO_SHOT = """You are a Python requirements analyst. Identify 3–5 key requirements or challenges for solving the given problem."""

SYS_MSG_REQUIREMENTS_ANALYST = f"""You are a Python requirements analyst. Identify key requirements and challenges from function specifications.

Example analyses (based on canonical examples):

{FEW_SHOT_EXAMPLES}

1. For comparing elements in a list: compare pairs and return True early.
2. For nested structures: track depth and detect completion when depth returns to zero.
3. For numeric transformations: extract fractional parts accurately.

Now analyze the given problem.
"""

MULTI_AGENT_TASK_ANALYST = """Analyze the following programming problem:

{prompt}

List the main requirements and challenges in 3–5 concise bullet points."""

MULTI_AGENT_TASK_REQUIREMENTS_ANALYST_ZERO_SHOT = """Analyze the following programming problem:

{prompt}

List the main requirements and challenges in 3–5 concise bullet points."""


# ================================================================
# PROGRAMMER
# ================================================================

SYS_MSG_PROGRAMMER_MA_ZERO_SHOT = """You are an expert Python programmer. Write clean, correct Python code that fully satisfies the specification.
Always include necessary imports for any type annotations and handle all edge cases correctly."""

SYS_MSG_PROGRAMMER_MA = f"""You are an expert Python programmer who writes correct and efficient code on the first try.

Follow the canonical examples below:

{FEW_SHOT_EXAMPLES}

Guidelines:
1. ALWAYS include all necessary imports (typing, math, etc.)
2. If using List, Tuple, Optional, etc., import them from typing.
3. Handle all edge cases correctly.
4. Focus on correctness over stylistic preferences.
"""

MULTI_AGENT_TASK_PROGRAMMER = """Based on this requirements analysis:
{analyst_findings}

Implement the following function:
{prompt}

Include all necessary imports and handle all edge cases.

Provide complete working Python code."""

MULTI_AGENT_TASK_PROGRAMMER_ZERO_SHOT = """Based on this requirements analysis:
{analyst_findings}

Implement the following function:
{prompt}

Include all necessary imports and handle all edge cases.

Provide complete working Python code."""


# ================================================================
# MODERATOR
# ================================================================

SYS_MSG_MODERATOR_CODE_ZERO_SHOT = """You are a code moderator. Check correctness and completeness, focusing only on logic, imports, and edge cases."""

SYS_MSG_MODERATOR_CODE = f"""You are a code moderator. Review the generated code for correctness and potential test failures.

When reviewing code:
1. Check all necessary imports (especially typing imports like List, Tuple, etc.)
2. Mark as BUG if imports required by annotations are missing
3. For code WITH ALL IMPORTS, check if it works for all valid inputs
4. Be lenient about algorithmic differences
5. Ignore style; focus only on correctness

Reference these canonical implementations for guidance:

{FEW_SHOT_EXAMPLES}
"""

MULTI_AGENT_TASK_MODERATOR_CODE = """Review this implementation:

Problem:
{prompt}

Code:
```python
{programmer_response}
```

Check for:
1. Missing imports
2. Requirement coverage
3. Logical correctness

State whether the code is correct or contains bugs, and explain briefly."""


# ================================================================
# REVIEW BOARD
# ================================================================

SYS_MSG_REVIEW_BOARD_CODE_ZERO_SHOT = """You are the review board. Provide the final verdict and corrected implementation, ensuring all requirements and imports are covered."""

SYS_MSG_REVIEW_BOARD_CODE = f"""You are a review board member providing the final decision on correctness and completeness.

When finalizing code:
1. Ensure all imports are included (especially typing imports)
2. Fix any issues from moderator feedback
3. Provide a fully correct, working implementation

Reference these canonical implementations for guidance:

{FEW_SHOT_EXAMPLES}
"""

MULTI_AGENT_TASK_REVIEW_BOARD_CODE = """Provide the final assessment and corrected implementation:

Problem:
{prompt}

Moderator feedback:
{moderator_summary}

Ensure all imports and requirements are included.

Provide the FINAL IMPLEMENTATION."""


# =======================================================================
# RQ3: EXPLANATION PROMPTING (Explain-Before)
# =======================================================================

# --- Vulnerability Detection: Explain-Before Prompts ---

SYS_MSG_VULNERABILITY_DETECTOR_EXPLAIN_BEFORE_ZERO_SHOT = """You are a security expert skilled in static program analysis.
Before making your decision, you MUST:
1. Identify potential vulnerability patterns in the code
2. Analyze each pattern systematically
3. Consider the security implications
4. Make a final decision based on your analysis

Always structure your response as:
REASONING: [Your step-by-step analysis]
DECISION: YES or NO"""

SYS_MSG_VULNERABILITY_DETECTOR_EXPLAIN_BEFORE_FEW_SHOT = f"""You are a security expert skilled in static analysis.
Use these canonical examples as your guide:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
REASONING: strcpy() is used without bounds checking, which can lead to buffer overflow when source exceeds destination buffer size.
DECISION: YES

Example 2 (C safe):
{EXAMPLE_C_SAFE}
REASONING: strncpy() is used with proper size limit, preventing buffer overflow. The buffer is also null-terminated safely.
DECISION: NO

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
REASONING: Objects allocated with new in the constructor are not freed in the destructor, leading to memory leaks when Vector goes out of scope.
DECISION: YES

Now analyze the following code. Structure your response as:
REASONING: [Your step-by-step analysis]
DECISION: YES or NO"""

VULNERABILITY_TASK_PROMPT_EXPLAIN_BEFORE = """Please analyze the following code for vulnerabilities:
```
{code}
```

Before making your decision, please:
1. Identify what security patterns you should look for
2. Analyze the code systematically for these patterns
3. Consider the security implications of what you find
4. Make your final decision

Structure your response as:
REASONING: [Your detailed step-by-step analysis]
DECISION: YES or NO

Let's think step-by-step."""

# --- Code Generation: Explain-Before Prompts ---

SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_ZERO_SHOT = """You are an expert Python programmer.
Before implementing the solution, you MUST:
1. Analyze the problem requirements
2. Identify key challenges and edge cases
3. Plan your approach
4. Implement the solution

Always structure your response as:
REASONING: [Your step-by-step plan]
CODE: [Your complete Python implementation]"""

SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_FEW_SHOT = f"""You are an expert Python programmer skilled in implementing functions based on their specifications.

Use these canonical examples as reference:
{FEW_SHOT_EXAMPLES}

Before writing code, you MUST:
1. Analyze requirements and identify edge cases
2. Plan your implementation approach
3. Consider necessary imports and data structures
4. Implement the complete solution

Structure your response as:
REASONING: [Your step-by-step plan]
CODE: [Your complete Python implementation with all necessary imports]"""

CODE_GENERATION_TASK_PROMPT_EXPLAIN_BEFORE = """Please analyze and implement the following function:

{prompt}

Before writing the code, please:
1. Identify the key requirements
2. Consider edge cases that need to be handled
3. Plan your implementation approach
4. Think about necessary imports and data structures

Structure your response as:
REASONING: [Your step-by-step analysis and plan]
CODE: [Your complete function implementation]

Let's think step-by-step."""

# Alias for backward compatibility
CODE_GENERATION_TASK_PROMPT = SINGLE_AGENT_TASK_CODE_GENERATION
