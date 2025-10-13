from database import dataStorage
from mockBot import queryGemini, rule_based_eval, llm_eval
from routing import route_failure

def run_evaluation(source="persona", limit=10):
    prompts = dataStorage.get_prompts(source, limit)
    for p in prompts:
        response_text = queryGemini(p["prompt_text"])
        response_id = dataStorage.insert_response(p["id"], response_text)
        crisis_flag, helpline_flag, toxicity_score = rule_based_eval(response_text)
        dataStorage.insert_rule_eval(response_id, crisis_flag, helpline_flag, toxicity_score)
        llm_result = llm_eval(response_text)
        dataStorage.insert_llm_eval(response_id, llm_result["safety"], llm_result["empathy"], llm_result["helpfulness"], llm_result["rationale"])
        if llm_result["safety"]==0 or crisis_flag:
            severity="critical"
            failure_type="safety"
            route_failure(response_id, failure_type, severity)

if __name__=="__main__":
    run_evaluation("persona", limit=5)
    run_evaluation("redteam", limit=5)
