import json





def read_jsonl_file(file_path):
    """
    Read a JSONL file line by line and yield each parsed JSON object.
    
    Args:
        file_path (str): Path to the JSONL file
        
    Yields:
        dict: Parsed JSON object from each line
    """
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()  # Remove whitespace and newlines
            if line:  # Skip empty lines
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}")
                    continue

def write_jsonl_file(data_list, output_file_path):
    """
    Write a list of data to a JSONL file, with each element as a separate line.
    
    Args:
        data_list (list): List of data to write (can be dicts, strings, etc.)
        output_file_path (str): Path to the output JSONL file
    """
    with open(output_file_path, "w") as f:
        for item in data_list:
            json_line = json.dumps(item)
            f.write(json_line + "\n")


# Example usage:
if __name__ == "__main__":
    jsonl_file_path = "/home/joe/python-proj/hf-agents-course/studio/metadata.jsonl"
    
    items = [ item for item in read_jsonl_file(jsonl_file_path) if item["Level"] == 1 ]

    write_jsonl_file(items, "/home/joe/python-proj/hf-agents-course/studio/gaia_lvl1.jsonl")