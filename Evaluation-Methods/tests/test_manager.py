import logging

from bot_api import ChatbotAPI
from db import DatabaseHandler
from evaluator import LLMJudge
from prompt_ingestor import PromptIngestor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestManager:
    def __init__(self, db_handler: DatabaseHandler, bot_api: ChatbotAPI):
        self.db_handler = db_handler
        self.prompt_ingestor = PromptIngestor(db_handler)
        self.llm_judge = LLMJudge(bot_api)

    def add_test(self, name, description, scoring_rubric):
        self.db_handler.insert_test(name, description, scoring_rubric)
        logger.info(f"Added test: {name}")

    def run_tests_on_prompts(self, test_id, prompt_ids):
        prompts_to_score = self.db_handler.fetch_unscored_prompts_for_tests(
            test_id, prompt_ids
        )

        with self.db_handler.Session() as session:
            test_info = session.execute(
                text("SELECT scoring_rubric FROM psych_tests WHERE id = :test_id"),
                {"test_id": test_id},
            ).fetchone()
            if not test_info:
                logger.error(f"Test with id {test_id} not found.")
                return

        scoring_rubric = test_info[0]

        for prompt_id, prompt_text in prompts_to_score:
            web_context = self.prompt_ingestor.fetch_web_context(prompt_text)

            # This is a simplification. A real implementation would use the bot to get a response first.
            # Here we just score the prompt directly.

            eval_prompt = f"Score the following text based on this rubric: {scoring_rubric}\n\nText: {prompt_text}"
            if web_context:
                eval_prompt += "\n\nWeb Context:\n" + "\n".join(web_context)

            evaluation = self.llm_judge.evaluate(
                "N/A", eval_prompt
            )  # No real response to evaluate

            self.db_handler.mark_test_scored(
                test_id,
                prompt_id,
                evaluation["helpfulness_score"],
                evaluation["rationale"],
            )
            logger.info(f"Scored prompt {prompt_id} for test {test_id}")
