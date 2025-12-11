import logging

import hdbscan
import numpy as np
import pandas as pd
import umap.umap_ as umap
from sentence_transformers import SentenceTransformer
from settings import settings
from sklearn.cluster import KMeans
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(settings.embeddings_model_name)

    def encode(self, texts):
        return self.model.encode(texts)


class TemporalClusterer:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder

    def fit_assign(self, df, method="auto"):
        df["embedding"] = list(self.embedder.encode(df["text"].tolist()))

        # Time-decay weighting
        df["timestamp"] = pd.to_datetime(df["created_at"])
        time_diff = (df["timestamp"].max() - df["timestamp"]).dt.total_seconds()
        weights = np.exp(-settings.clustering_params["alpha"] * time_diff)
        weighted_embeddings = (
            np.array(df["embedding"].tolist()) * weights[:, np.newaxis]
        )

        reduced_embeddings = umap.UMAP(n_components=2).fit_transform(
            weighted_embeddings
        )

        if method == "auto":
            try:
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=settings.clustering_params["min_cluster_size"],
                    min_samples=settings.clustering_params["min_samples"],
                )
                df["cluster_id"] = clusterer.fit_predict(reduced_embeddings)
                df["cluster_prob"] = clusterer.probabilities_
            except Exception as e:
                logger.warning(f"HDBSCAN failed: {e}. Falling back to KMeans.")
                clusterer = KMeans(n_clusters=10)
                df["cluster_id"] = clusterer.fit_predict(reduced_embeddings)
                df["cluster_prob"] = 1.0
        else:  # fallback
            clusterer = KMeans(n_clusters=10)
            df["cluster_id"] = clusterer.fit_predict(reduced_embeddings)
            df["cluster_prob"] = 1.0

        df["x"] = reduced_embeddings[:, 0]
        df["y"] = reduced_embeddings[:, 1]
        return df


class ConversationTracker:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def get_cluster_trajectory(self, conversation_id):
        # This is a simplified implementation. A real one would need conversation IDs.
        query = "SELECT cluster_id FROM clusters ORDER BY response_id"
        with self.db_handler.Session() as session:
            result = session.execute(text(query))
            return [row[0] for row in result]

    def detect_common_trajectories(self, min_count):
        # Placeholder for more complex analysis
        return {"trajectory_1": 10, "trajectory_2": 5}

    def export_trajectories_csv(self, path):
        # Placeholder
        pd.DataFrame([{"conversation_id": 1, "trajectory": "1,2,3"}]).to_csv(
            path, index=False
        )
        logger.info(f"Exported trajectories to {path}")


class ClusterEngine:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self.embedder = Embedder()
        self.clusterer = TemporalClusterer(self.embedder)
        self.tracker = ConversationTracker(self.db_handler)

    def cluster_and_save(self, time_window=None, limit=1000, method="auto"):
        query = "SELECT id, response_text as text, created_at FROM chatbot_responses ORDER BY created_at DESC LIMIT :limit"
        with self.db_handler.Session() as session:
            df = pd.read_sql(text(query), session.connection(), params={"limit": limit})

        if not df.empty:
            df_clustered = self.clusterer.fit_assign(df, method=method)

            cluster_assignments = []
            for _, row in df_clustered.iterrows():
                cluster_assignments.append(
                    {
                        "response_id": row["id"],
                        "cluster_id": row["cluster_id"],
                        "cluster_prob": row["cluster_prob"],
                    }
                )
            self.db_handler.save_cluster_assignments(cluster_assignments)
            logger.info(f"Saved {len(cluster_assignments)} cluster assignments.")
            return df_clustered
        return pd.DataFrame()
