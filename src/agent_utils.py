import os
import config
from pathlib import Path
from autogen import AssistantAgent, ConversableAgent, GroupChat, GroupChatManager, LocalCommandLineCodeExecutor, register_function

# --- Generic Agent Creation ---
def create_agent(agent_type, name, llm_config=None, sys_prompt=None, description=None):
    if agent_type == "assistant":
        return AssistantAgent(
            name=name,
            system_message=sys_prompt,
            description=description,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )
    elif agent_type == "conversable":
        return ConversableAgent(
            name=name,
            system_message=sys_prompt,
            description=description,
            llm_config=llm_config,
            human_input_mode="TERMINATE",
        )
    elif agent_type == "code_executor":
        executor = LocalCommandLineCodeExecutor(
            timeout=10,
            work_dir=Path(config.WORK_DIR)
        )
        return ConversableAgent(
            name=name,
            description=description,
            code_execution_config={"executor": executor},
            human_input_mode="NEVER",
            llm_config=False,
        )
    else:
        raise ValueError("Unknown agent type.")
