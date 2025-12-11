import logging

from db import DatabaseHandler
from evaluator import LLMJudge, RuleEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not found. Using fallback GraphRouter.")


class GraphRouter:
    def __init__(self, db_handler: DatabaseHandler):
        self.nodes = {}
        self.edges = {}
        self.db_handler = db_handler

    def add_node(self, name, node):
        self.nodes[name] = node

    def add_conditional_edge(self, start_node, condition, end_nodes):
        self.edges[start_node] = (condition, end_nodes)

    def run(self, initial_state):
        current_node_name = "input"
        state = initial_state
        while current_node_name != "output":
            current_node = self.nodes[current_node_name]
            state = current_node.run(state)
            if current_node_name in self.edges:
                condition, end_nodes = self.edges[current_node_name]
                next_node_name = condition(state)
                if next_node_name in end_nodes:
                    current_node_name = next_node_name
                else:
                    break
            else:
                break
        return state


class InputNode:
    def run(self, state):
        logger.debug("Running InputNode")
        return state


class RuleEvalNode:
    def __init__(self):
        self.evaluator = RuleEvaluator()

    def run(self, state):
        logger.debug("Running RuleEvalNode")
        eval_results = self.evaluator.evaluate(state["response_text"])
        state.update(eval_results)
        return state


class LLMEvalNode:
    def __init__(self, bot_api):
        self.evaluator = LLMJudge(bot_api)

    def run(self, state):
        logger.debug("Running LLMEvalNode")
        eval_results = self.evaluator.evaluate(
            state["prompt_text"], state["response_text"]
        )
        state.update(eval_results)
        return state


class SafetyGuardrailNode:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def run(self, state):
        logger.warning(
            f"Routing to SafetyGuardrailNode for response {state['response_id']}"
        )
        self.db_handler.insert_failure(
            state["response_id"], "safety_guardrail", "Crisis detected"
        )
        state["response_text"] = "I am a helpful and harmless AI assistant."
        return state


class PersonaUpdateNode:
    def run(self, state):
        logger.debug("Running PersonaUpdateNode")
        state["system_prompt"] = "New system prompt based on evaluation."
        return state


class PromptPatchNode:
    def run(self, state):
        logger.debug("Running PromptPatchNode")
        state["patched_instruction"] = "Patched instruction."
        return state


class ClinicianReviewNode:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def run(self, state):
        logger.warning(
            f"Routing to ClinicianReviewNode for response {state['response_id']}"
        )
        self.db_handler.insert_failure(
            state["response_id"],
            "clinician_review",
            "LLM evaluation failed safety check",
        )
        return state


class OutputNode:
    def run(self, state):
        logger.debug("Running OutputNode")
        return state


class LangGraphRouter:
    def __init__(self, db_handler, bot_api):
        self.db_handler = db_handler
        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_langgraph(bot_api)
        else:
            self.graph = self._build_fallback_graph(bot_api)

    def _build_langgraph(self, bot_api):
        workflow = StateGraph(dict)
        workflow.add_node("input", InputNode().run)
        workflow.add_node("rule_eval", RuleEvalNode().run)
        workflow.add_node("llm_eval", LLMEvalNode(bot_api).run)
        workflow.add_node("safety_guardrail", SafetyGuardrailNode(self.db_handler).run)
        workflow.add_node("persona_update", PersonaUpdateNode().run)
        workflow.add_node("prompt_patch", PromptPatchNode().run)
        workflow.add_node("clinician_review", ClinicianReviewNode(self.db_handler).run)
        workflow.add_node("output", OutputNode().run)

        workflow.set_entry_point("input")
        workflow.add_edge("input", "rule_eval")
        workflow.add_conditional_edges(
            "rule_eval",
            lambda state: "safety_guardrail"
            if state.get("crisis_detected")
            else "llm_eval",
            {"safety_guardrail": "output", "llm_eval": "llm_eval"},
        )
        workflow.add_conditional_edges(
            "llm_eval",
            lambda state: "clinician_review"
            if state.get("safety_score") == 0
            else "persona_update",
            {"clinician_review": "output", "persona_update": "prompt_patch"},
        )
        workflow.add_edge("prompt_patch", "output")
        workflow.add_edge("persona_update", "prompt_patch")

        return workflow.compile()

    def _build_fallback_graph(self, bot_api):
        router = GraphRouter(self.db_handler)
        router.add_node("input", InputNode())
        router.add_node("rule_eval", RuleEvalNode())
        router.add_node("llm_eval", LLMEvalNode(bot_api))
        router.add_node("safety_guardrail", SafetyGuardrailNode(self.db_handler))
        router.add_node("persona_update", PersonaUpdateNode())
        router.add_node("prompt_patch", PromptPatchNode())
        router.add_node("clinician_review", ClinicianReviewNode(self.db_handler))
        router.add_node("output", OutputNode())

        router.add_conditional_edge(
            "rule_eval",
            lambda state: "safety_guardrail"
            if state.get("crisis_detected")
            else "llm_eval",
            {"safety_guardrail": "output", "llm_eval": "llm_eval"},
        )
        router.add_conditional_edge(
            "llm_eval",
            lambda state: "clinician_review"
            if state.get("safety_score") == 0
            else "persona_update",
            {"clinician_review": "output", "persona_update": "prompt_patch"},
        )
        return router

    def run(self, state):
        return (
            self.graph.invoke(state) if LANGGRAPH_AVAILABLE else self.graph.run(state)
        )
