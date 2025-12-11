import logging

from settings import settings
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(settings.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables_if_not_exist()

    def _create_tables_if_not_exist(self):
        inspector = inspect(self.engine)
        with self.engine.connect() as connection:
            if not inspector.has_table("prompts"):
                logger.info("Creating database tables.")
                connection.execute(
                    text(
                        """
                    CREATE TABLE prompts (
                        id SERIAL PRIMARY KEY,
                        source VARCHAR(255),
                        text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE chatbot_responses (
                        id SERIAL PRIMARY KEY,
                        prompt_id INTEGER REFERENCES prompts(id),
                        response_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE rule_eval (
                        id SERIAL PRIMARY KEY,
                        response_id INTEGER REFERENCES chatbot_responses(id),
                        crisis_detected BOOLEAN,
                        helpline_detected BOOLEAN,
                        toxicity_score FLOAT
                    );
                    CREATE TABLE llm_eval (
                        id SERIAL PRIMARY KEY,
                        response_id INTEGER REFERENCES chatbot_responses(id),
                        safety_score INTEGER,
                        empathy_score INTEGER,
                        helpfulness_score INTEGER,
                        rationale TEXT
                    );
                    CREATE TABLE failure_log (
                        id SERIAL PRIMARY KEY,
                        response_id INTEGER REFERENCES chatbot_responses(id),
                        routed_to VARCHAR(255),
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE clusters (
                        id SERIAL PRIMARY KEY,
                        response_id INTEGER REFERENCES chatbot_responses(id),
                        cluster_id INTEGER,
                        cluster_prob FLOAT
                    );
                    CREATE TABLE psych_tests (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255),
                        description TEXT,
                        scoring_rubric TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                     CREATE TABLE test_results (
                        id SERIAL PRIMARY KEY,
                        test_id INTEGER REFERENCES psych_tests(id),
                        prompt_id INTEGER REFERENCES prompts(id),
                        score INTEGER,
                        rationale TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
                    )
                )
                connection.commit()

    def insert_prompt(self, source, text):
        with self.Session() as session:
            session.execute(
                text("INSERT INTO prompts (source, text) VALUES (:source, :text)"),
                {"source": source, "text": text},
            )
            session.commit()

    def fetch_prompts(self, source, limit):
        with self.Session() as session:
            result = session.execute(
                text(
                    "SELECT id, text FROM prompts WHERE source = :source LIMIT :limit"
                ),
                {"source": source, "limit": limit},
            )
            return result.fetchall()

    def insert_response(self, prompt_id, response_text):
        with self.Session() as session:
            result = session.execute(
                text(
                    "INSERT INTO chatbot_responses (prompt_id, response_text) VALUES (:prompt_id, :response_text) RETURNING id"
                ),
                {"prompt_id": prompt_id, "response_text": response_text},
            )
            session.commit()
            return result.scalar_one()

    def insert_rule_eval(
        self, response_id, crisis_detected, helpline_detected, toxicity_score
    ):
        with self.Session() as session:
            session.execute(
                text(
                    "INSERT INTO rule_eval (response_id, crisis_detected, helpline_detected, toxicity_score) VALUES (:response_id, :crisis_detected, :helpline_detected, :toxicity_score)"
                ),
                {
                    "response_id": response_id,
                    "crisis_detected": crisis_detected,
                    "helpline_detected": helpline_detected,
                    "toxicity_score": toxicity_score,
                },
            )
            session.commit()

    def insert_llm_eval(
        self, response_id, safety_score, empathy_score, helpfulness_score, rationale
    ):
        with self.Session() as session:
            session.execute(
                text(
                    "INSERT INTO llm_eval (response_id, safety_score, empathy_score, helpfulness_score, rationale) VALUES (:response_id, :safety_score, :empathy_score, :helpfulness_score, :rationale)"
                ),
                {
                    "response_id": response_id,
                    "safety_score": safety_score,
                    "empathy_score": empathy_score,
                    "helpfulness_score": helpfulness_score,
                    "rationale": rationale,
                },
            )
            session.commit()

    def insert_failure(self, response_id, routed_to, reason):
        with self.Session() as session:
            session.execute(
                text(
                    "INSERT INTO failure_log (response_id, routed_to, reason) VALUES (:response_id, :routed_to, :reason)"
                ),
                {"response_id": response_id, "routed_to": routed_to, "reason": reason},
            )
            session.commit()

    def save_cluster_assignments(self, batch):
        with self.Session() as session:
            for record in batch:
                session.execute(
                    text(
                        "INSERT INTO clusters (response_id, cluster_id, cluster_prob) VALUES (:response_id, :cluster_id, :cluster_prob)"
                    ),
                    record,
                )
            session.commit()

    def insert_test(self, name, description, scoring_rubric):
        with self.Session() as session:
            session.execute(
                text(
                    "INSERT INTO psych_tests (name, description, scoring_rubric) VALUES (:name, :description, :scoring_rubric)"
                ),
                {
                    "name": name,
                    "description": description,
                    "scoring_rubric": scoring_rubric,
                },
            )
            session.commit()

    def fetch_unscored_prompts_for_tests(self, test_id, prompt_ids):
        with self.Session() as session:
            result = session.execute(
                text(
                    "SELECT id, text FROM prompts WHERE id IN :prompt_ids AND id NOT IN (SELECT prompt_id FROM test_results WHERE test_id = :test_id)"
                ),
                {"prompt_ids": tuple(prompt_ids), "test_id": test_id},
            )
            return result.fetchall()

    def mark_test_scored(self, test_id, prompt_id, score, rationale):
        with self.Session() as session:
            session.execute(
                text(
                    "INSERT INTO test_results (test_id, prompt_id, score, rationale) VALUES (:test_id, :prompt_id, :score, :rationale)"
                ),
                {
                    "test_id": test_id,
                    "prompt_id": prompt_id,
                    "score": score,
                    "rationale": rationale,
                },
            )
            session.commit()
