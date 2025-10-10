# Agent Green

Agent Green is a research project for evaluating the energy consumption and accuracy of Large Language Model (LLM) agents in log parsing tasks. The project investigates non-agentic, single-agent, dual-agent, tool-using, and multi-agent LLM configurations, measuring their effectiveness and sustainability.

## Frameworks and Tools

- **AG2 (formerly AutoGen):** Used for building agentic LLM workflows ([AG2 GitHub](https://github.com/ag2ai/ag2)).
- **CodeCarbon:** Used for measuring energy consumption ([CodeCarbon GitHub](https://github.com/mlco2/codecarbon)).
- **Ollama:** Used for running and evaluating LLM models ([Ollama](https://ollama.com/)).

## Dataset

- **Source:** HDFS 2k log file from the [LogHub repository](https://github.com/logpai/loghub).
- **Sampling:** 200 log messages sampled using proportional stratified sampling by template category.
- **Templates:** Modified templates provided by Khan et al.

## Experiment Procedure

- Ollama server is started before and stopped after each run to ensure isolated energy measurements.
- Agent-level caching in AG2 is disabled for all experiments.
- Each experiment is run three times; average results are reported.
- Experiments cover five configurations:
  - **Non-Agentic (NA):** Direct LLM calls.
  - **Single Agent (SA):** One LLM-based agent as parser.
  - **Tool-Using Agent (TA):** Agent using external parser tool.
  - **Dual Agents (DA):** Two LLM-based agents; parser agent and verifier agent.
  - **Multiple Agents (MA):** User-proxy, parser, tool-using, and comparator-refiner agents.

## Repository Structure

```
agent-green/
├── config/                # Configuration files and experiment settings
├── logs/                  # Raw and processed log files (e.g., HDFS_200_sampled.log)
├── src/                   # Source code and notebooks
│   ├── agent_utils.py
│   ├── config.py
│   ├── drain_utils.py
│   ├── evaluation.py
│   ├── format_output.py
│   ├── log_utils.py
│   ├── ollama_utils.py
│   ├── visualization.ipynb
│   ├── no_agents.ipynb
│   ├── single_agent.ipynb
│   ├── tool-based_agents.ipynb
│   ├── two_agents.ipynb
│   ├── multi_agents.ipynb
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore file
└── README.md              # Project documentation
```

## How to Use

1. Clone the repository.
2. Install dependencies:  
   ```
   pip install -r requirements.txt
   ```
3. Configure paths and settings in `config/` (for codecarbon) and `src/config.py` (for project folders, LLM configs, and prompts).
4. Place your log files and ground truth templates in the `logs/` folder.
5. Run the notebooks in `src/` to reproduce experiments and results.



## How to run Vuln Detection scripts

No Agent Usage 

```
python script/no_agent_vuln.py

```

Single Agent Usage
```
python script/single_agent_vuln.py sa-few    # run with few-shot
python script/single_agent_vuln.py sa-zero   # run with zero-shot

```

Dual Agent Usage 
```
python script/dual_agent_vuln.py

```

Multi Agent Usage
```
python script/multi_agent_vuln.py

```



## How to run Code Generation scripts

No Agent Usage 

```
python script/no_agent_code_generation.py

```

Single Agent Usage
```
python script/single_agent_code_generation.py SA-few    # run with few-shot
python script/single_agent_code_generation.py SA-zero   # run with zero-shot

```

Dual Agent Usage 
```
python script/dual_agent_code_generation.py

```

Multi Agent Usage
```
python script/multi_agent_code_generation.py

```

