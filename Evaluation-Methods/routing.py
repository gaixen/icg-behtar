from database import dataStorage

def route_failure(response_id, failure_type, severity):
    if failure_type == "safety" and severity == "critical":
        routed_to = "safety_guardrails"
    elif failure_type == "empathy":
        routed_to = "persona_update"
    elif failure_type in ["cultural","style"]:
        routed_to = "prompt_patch"
    else:
        routed_to = "clinician_review"
    dataStorage.insert_failure(response_id, failure_type)
    return routed_to
