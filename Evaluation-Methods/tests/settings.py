import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.db_url = os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost/mydb"
        )
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        self.mcp_url = os.getenv("MCP_URL")
        self.embeddings_model_name = os.getenv(
            "EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2"
        )

        # Clustering parameters
        self.clustering_params = {
            "min_cluster_size": int(os.getenv("MIN_CLUSTER_SIZE", 5)),
            "min_samples": int(os.getenv("MIN_SAMPLES", 5)),
            "alpha": float(os.getenv("ALPHA", 0.5)),
        }

        # File paths
        self.output_dir = os.getenv("OUTPUT_DIR", "output/")

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)


settings = Settings()
