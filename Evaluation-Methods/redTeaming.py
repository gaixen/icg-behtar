import os
import json
from database import dataStorage
from mockBot import queryGemini, rule_based_eval, llm_eval
from routing import route_failure
from datasets import load_dataset

dataset = load_dataset("ShenLab/MentalChat16K")

DATASET_PATHS = {}

# DATASET_PATHS = {
#     # "hh-rlhf": "path/to/hh-rlhf.jsonl",
#     # "crisisnlp": "path/to/crisisnlp.jsonl",
#     # "clpsych": "path/to/clpsych.jsonl",
#     "mentalchat": "path/to/mentalchat.jsonl"
# }

def load_redteam_prompts():
    prompts = []
    for source, path in DATASET_PATHS.items():
        if os.path.exists(path):
            with open(path, 'r') as file:
                for line in file:
                    data = json.loads(line)
                    prompt = data.get('prompt') or data.get('text') or data.get('message')
                    if prompt:
                        prompts.append((prompt, source))
    return prompts

def ingest_redteam_prompts():
    prompts = load_redteam_prompts()
    for prompt_text, source in prompts:
        dataStorage.insert_prompt(prompt_text=prompt_text, source=source, persona="adversarial")

def run_redteam_pipeline(limit=10):
    prompts = dataStorage.get_prompts(source="redteam", limit=limit)
    for p in prompts:
        response_text = queryGemini(p["prompt_text"])
        response_id = dataStorage.insert_response(p["id"], response_text)
        crisis_flag, helpline_flag, toxicity_score = rule_based_eval(response_text)
        dataStorage.insert_rule_eval(response_id, crisis_flag, helpline_flag, toxicity_score)
        llm_result = llm_eval(response_text)
        dataStorage.insert_llm_eval(response_id, llm_result["safety"], llm_result["empathy"], llm_result["helpfulness"], llm_result["rationale"])
        if llm_result["safety"] == 0 or crisis_flag:
            severity = "critical"
            failure_type = "safety"
            route_failure(response_id, failure_type, severity)

# if __name__ == "__main__":
#     ingest_redteam_prompts()
#     run_redteam_pipeline(limit=10)
