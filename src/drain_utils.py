from logparser.Drain import LogParser
from logparser.utils import evaluator
from typing import List
import regex as re
import hashlib
import logging


# Setup logging
logging.basicConfig(level=logging.INFO)

def parse_logs(
    input_dir: str = "/home/user/Desktop/AgentGreen/logs/",
    log_file: str = "HDFS_200_sampled_CG.log",
    log_format: str = r"<Date> <Time> <Pid> <Level> <Component>: <Content>",
    regex: List[str] = [r"blk_-?\d+", r"(\d+\.){3}\d+(:\d+)?"],
    output_dir: str = "/home/user/Desktop/AgentGreen/results/Drain_result/",
    depth: int = 4,
    similarity_threshold: float = 0.5
) -> str:
    """
    Parse logs using the specified format and parameters.

    Args:
        input_dir (str): Directory containing the input log files.
        output_dir (str): Directory to save the parsed log results.
        log_file (str): The log file to be parsed.
        log_format (str): The format of the log file.
        regex (List[str]): List of regular expressions for preprocessing.
        depth (int, optional): Depth of the parsing tree. Defaults to 4.
        similarity_threshold (float, optional): Similarity threshold for grouping log messages. Defaults to 0.5.
    """

    # Validate the type of the input parameters
    assert isinstance(input_dir, str), "input_dir must be a string."
    assert isinstance(output_dir, str), "output_dir must be a string."
    assert isinstance(log_file, str), "log_file must be a string."
    assert isinstance(log_format, str), "log_format must be a string."
    assert isinstance(depth, int), "depth must be an integer."
    # Similarity threshold must be a float or int
    assert isinstance(similarity_threshold, (float, int)), "similarity_threshold must be a float or an integer."
    # Regex must be list of strings, but if it's a string, it will be converted to a list of strings
    if isinstance(regex, str):
        regex = [regex]
    assert isinstance(regex, list), "regex must be a list of strings."

    # Parse the logs
    parser = LogParser(
        log_format=log_format,
        indir=input_dir,
        outdir=output_dir,
        depth=depth,
        st=similarity_threshold,
        rex=regex
    )
    result = parser.parse(log_file)
    print(f"Parsing completed. Results saved to {output_dir}")
    return result

class Logcluster:
    def __init__(self, logTemplate="", logIDL=None):
        self.logTemplate = logTemplate
        if logIDL is None:
            logIDL = []
        self.logIDL = logIDL


class Node:
    def __init__(self, childD=None, depth=0, digitOrtoken=None):
        if childD is None:
            childD = dict()
        self.childD = childD
        self.depth = depth
        self.digitOrtoken = digitOrtoken

class DrainWrapper:
    def __init__(self, log_format, depth=4, st=0.4, maxChild=100, rex=[], keep_para=True):
        self.parser = LogParser(
            log_format=log_format,
            depth=depth,
            st=st,
            maxChild=maxChild,
            rex=rex,
            keep_para=keep_para
        )
        self.parser.rootNode = Node()
        self.parser.logCluL = []
        self.parser.lineCount = 0
        self.results = []

    def parse_line(self, line):
        self.parser.lineCount += 1
        line_id = self.parser.lineCount

        content = self._extract_content_field(line)
        processed = self.parser.preprocess(content).strip().split()

        match_cluster = self.parser.treeSearch(self.parser.rootNode, processed)
        
        if match_cluster is None:
            new_cluster = Logcluster(logTemplate=processed, logIDL=[line_id])
            self.parser.logCluL.append(new_cluster)
            self.parser.addSeqToPrefixTree(self.parser.rootNode, new_cluster)
            template = " ".join(processed)
        else:
            new_template = self.parser.getTemplate(processed, match_cluster.logTemplate)
            match_cluster.logIDL.append(line_id)
            if " ".join(new_template) != " ".join(match_cluster.logTemplate):
                match_cluster.logTemplate = new_template
            template = " ".join(match_cluster.logTemplate)

        template_id = hashlib.md5(template.encode("utf-8")).hexdigest()[0:8]
        parameters = self._extract_parameters(template, content) if self.parser.keep_para else []

        parsed_result = {
            "LineId": line_id,
            "Content": line.strip(),
            "EventId": template_id,
            "EventTemplate": template,
            "ParameterList": parameters,
        }

        event_template = parsed_result["EventTemplate"]
        print(event_template)

        self.results.append(parsed_result)
        return event_template


    def _extract_parameters(self, template, content):
        temp = re.sub(r"<.{1,5}>", "<*>", template)
        if "<*>" not in temp:
            return []
        temp = re.sub(r"([^A-Za-z0-9])", r"\\\1", temp)
        temp = re.sub(r"\\ +", r"\\s+", temp)
        temp = "^" + temp.replace(r"\<\*\>", "(.*?)") + "$"
        match = re.findall(temp, content)
        if not match:
            return []
        return list(match[0]) if isinstance(match[0], tuple) else [match[0]]
    
    def _extract_content_field(self, line):
        import re
        headers = re.findall(r"<(.*?)>", self.parser.log_format)
        regex_pattern = self.parser.log_format
        for header in headers:
            if header == "Content":
                regex_pattern = regex_pattern.replace(f"<{header}>", "(?P<Content>.*)")
            else:
                regex_pattern = regex_pattern.replace(f"<{header}>", ".*?")
        match = re.match(regex_pattern, line)
        return match.group("Content") if match else line


    def get_all_results(self):
        """Return list of all parsed log results."""
        return self.results

    def get_templates(self):
        """Return list of unique templates with counts."""
        from collections import Counter
        templates = [r["EventTemplate"] for r in self.results]
        counts = Counter(templates)
        return [{"EventTemplate": t, "EventId": hashlib.md5(t.encode("utf-8")).hexdigest()[0:8], "Occurrences": c}
                for t, c in counts.items()]
    def export_results_to_csv(self, path):
        import pandas as pd
        df = pd.DataFrame(self.results)
        df.to_csv(path, index=False)

    def export_templates_to_csv(self, path):
        import pandas as pd
        df = pd.DataFrame(self.get_templates())
        df.to_csv(path, index=False)
    

def parse_log_lines(
    log_line: str,
    log_format: str = r"<Date> <Time> <Pid> <Level> <Component>: <Content>",
    regex: list[str] = [r"blk_-?\d+", r"(\d+\.){3}\d+(:\d+)?"],
    depth: int = 4,
    similarity_threshold: float = 0.5
) -> str:
    """
    Parse logs using the specified format and parameters.
rr
    Args:
        log_line (str): The log line to be parsed.
        log_format (str, optional): The format of the log line.
        regex (List[str], optional): List of regular expressions for preprocessing.
        depth (int, optional): Depth of the parsing tree.
        similarity_threshold (float, optional): Similarity threshold for grouping log messages.
    """

    # Validate the type of the input parameters
    assert isinstance(log_line, str), "log_line must be a string."
    assert isinstance(log_format, str), "log_format must be a string."
    assert isinstance(depth, int), "depth must be an integer."
    # Similarity threshold must be a float or int
    assert isinstance(similarity_threshold, (float, int)), "similarity_threshold must be a float or an integer."
    # Regex must be list of strings, but if it's a string, it will be converted to a list of strings
    if isinstance(regex, str):
        regex = [regex]
    assert isinstance(regex, list), "regex must be a list of strings."


    wrapper = DrainWrapper(
        log_format=log_format,
        depth=depth,
        st=similarity_threshold,
        rex=regex,
        )

    # Parse lines...
    parsed_line = wrapper.parse_line(log_line)
    #print(f"Parsed Line: {parsed_line}")
    # Export results
    #wrapper.export_results_to_csv("parsed_log_line_wrapper.csv")
    #wrapper.export_templates_to_csv("templates_summary_wrapper.csv")

    return parsed_line