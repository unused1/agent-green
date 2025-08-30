# %%
import csv
import json
import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# %%
# To eliminate unnecessary parts from the response
def format_response(response):
    reg = re.compile("`([^`]+)`")
    template = reg.findall(response)
    if len(template) > 0:
        print(template[-1])
        return template[-1]
    else:
        if "\n" in response.strip():
            logger.warning(response)
            logger.warning("=" * 20)
        return response.strip() 

# %%
# save output in json format
def save_json_output(file_path, output):
    logger.info("output will be saved into " + str(file_path) + " in json format")
    with open(file_path, 'w') as file:
        json.dump(output, file)
    logger.info("the ouput has been saved in json format!")

# %%
# save raw output
def save_raw_output(file_path, output_list):
    logger.info("raw output will be saved into " + str(file_path))
    with open(file_path, 'w') as file:
        file.write('\n'.join(output_list))
    logger.info("raw output has been saved!")

# %%
# save prompt used to generate that results
def save_prompt(file_path, prompt):
    logger.info("Prompt: " + prompt)
    logger.info("will be saved into " + str(file_path))
    with open(file_path, 'w') as file:
        file.write(prompt)
    logger.info("Prompt has been saved!")

# %%
# post-processing: change {} => <*>
# change regex with <[^>]*>* to convert <> => <*>
def format_string(unformatted):
    logger.info("Unformatted string: " + unformatted)
    formatted = re.sub(r'{[^}]*}*', '<*>', unformatted)
    logger.info("Formatted string: " + formatted)
    return formatted

# %%
# convert raw output into formatted csv file
def format_output_file_into_csv(raw_file_path, formatted_file_path):
    with open(raw_file_path, 'r') as raw_file:
        with open(formatted_file_path, 'w', newline = '') as formatted_file:
            writer = csv.writer(formatted_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            header = ['LLM_output']
            # write the header
            writer.writerow(header)
            # Writing each line from raw input file to formatted csv file after post-processing
            for line in raw_file:
                formatted_log_line = format_string(line)
                formatted_file.write(str(formatted_log_line)) 
    logger.info("the formatted csv file path: " + formatted_file_path)
    logger.info("the output has been formatted!") 

# %%
# add index as LineIds to formatted output file
def add_index(formatted_output_file_path):
    logger.info("add index as LineIDs to formatted output file...")
    df = pd.read_csv(formatted_output_file_path)
    df['Line_ID'] = df.index + 1
    df.to_csv(formatted_output_file_path, index=False)

# %%
# save int output
def save_int_output(file_path, output_list):
    logger.info("int output will be saved into " + str(file_path))
    with open(file_path, 'w') as file:
        file.write('\n'.join(str(output) for output in output_list))
    logger.info("int output has been saved!")
