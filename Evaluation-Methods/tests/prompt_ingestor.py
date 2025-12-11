import csv
import json
import logging

import requests
from db import DatabaseHandler
from settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptIngestor:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def ingest_from_file(self, file_path, source):
        if file_path.endswith(".csv"):
            with open(file_path, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    self.db_handler.insert_prompt(source, row[0])
        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                for item in data:
                    self.db_handler.insert_prompt(source, item["prompt"])
        logger.info(f"Ingested prompts from {file_path}")

    def fetch_web_context(self, query):
        if not settings.mcp_url:
            logger.debug("MCP_URL not set, skipping web context fetch.")
            return None
        try:
            response = requests.post(settings.mcp_url, json={"q": query}, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not fetch web context from MCP: {e}")
            return None
