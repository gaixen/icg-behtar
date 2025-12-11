import logging

from bot_api import ChatbotAPI
from cluster_engine import ClusterEngine
from db import DatabaseHandler
from evaluator import Evaluator
from langgraph_pipeline import LangGraphRouter
from prompt_ingestor import PromptIngestor
from settings import Settings
from test_manager import TestManager
from visualizer import Visualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedRunner:
    def __init__(self):
        self.settings = Settings()
        self.db_handler = DatabaseHandler()
        self.bot_api = ChatbotAPI()
        self.prompt_ingestor = PromptIngestor(self.db_handler)
        self.evaluator = Evaluator(self.db_handler, self.bot_api)
        self.router = LangGraphRouter(self.db_handler, self.bot_api)
        self.cluster_engine = ClusterEngine(self.db_handler)
        self.test_manager = TestManager(self.db_handler, self.bot_api)
        self.visualizer = Visualizer()

    def ingest_and_run_redteam(self, redteam_source_paths):
        for path in redteam_source_paths:
            self.prompt_ingestor.ingest_from_file(path, "redteam")
        self.run_evaluation_cycle("redteam", 100)

    def run_evaluation_cycle(self, source, limit):
        prompts = self.db_handler.fetch_prompts(source, limit)
        for prompt_id, prompt_text in prompts:
            response_text = self.bot_api.get_response(prompt_text)
            response_id = self.db_handler.insert_response(prompt_id, response_text)

            initial_state = {
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
                "response_id": response_id,
                "response_text": response_text,
            }
            final_state = self.router.run(initial_state)

            self.evaluator.evaluate_response(
                prompt_id, prompt_text, response_id, final_state["response_text"]
            )
            logger.info(f"Processed and evaluated prompt {prompt_id}")

    def cluster_and_analyze(self, time_window=None, limit=1000, method="auto"):
        df_clustered = self.cluster_engine.cluster_and_save(time_window, limit, method)
        if not df_clustered.empty:
            self.visualizer.plot_clusters(df_clustered)
            self.visualizer.plot_cluster_timeline(df_clustered)
            self.visualizer.plot_cluster_frequencies(df_clustered)
            self.visualizer.save_cluster_csv(df_clustered)

    def run_psych_tests_sequential(self, test_ids, prompt_source):
        prompts = self.db_handler.fetch_prompts(prompt_source, 10000)  # Large limit
        prompt_ids = [p[0] for p in prompts]
        for test_id in test_ids:
            self.test_manager.run_tests_on_prompts(test_id, prompt_ids)
