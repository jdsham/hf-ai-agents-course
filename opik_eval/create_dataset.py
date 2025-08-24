from opik import Opik

# Get or create a dataset

client = Opik()

dataset = client.get_or_create_dataset(name="GAIA Level 1 Dataset")
dataset.read_jsonl_from_file("/home/joe/python-proj/hf-ai-agents-course/test_harness/gaia_lvl1.jsonl")
