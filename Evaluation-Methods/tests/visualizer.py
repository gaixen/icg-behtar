import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
from settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Visualizer:
    def __init__(self):
        self.output_dir = settings.output_dir

    def plot_clusters(self, df: pd.DataFrame):
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            df["x"], df["y"], c=df["cluster_id"], cmap="viridis", s=50, alpha=0.7
        )
        plt.title("UMAP Projection of Embeddings, Colored by Cluster")
        plt.xlabel("UMAP Dimension 1")
        plt.ylabel("UMAP Dimension 2")
        plt.legend(*scatter.legend_elements(), title="Clusters")

        plot_path = os.path.join(self.output_dir, "cluster_plot.png")
        plt.savefig(plot_path)
        logger.info(f"Saved cluster plot to {plot_path}")
        plt.close()

    def plot_cluster_timeline(self, df: pd.DataFrame):
        df_sorted = df.sort_values("created_at")
        plt.figure(figsize=(15, 7))
        plt.plot(
            df_sorted["created_at"], df_sorted["cluster_id"], marker="o", linestyle="-"
        )
        plt.title("Cluster ID Timeline")
        plt.xlabel("Time")
        plt.ylabel("Cluster ID")

        plot_path = os.path.join(self.output_dir, "cluster_timeline.png")
        plt.savefig(plot_path)
        logger.info(f"Saved timeline plot to {plot_path}")
        plt.close()

    def plot_cluster_frequencies(self, df: pd.DataFrame):
        plt.figure(figsize=(10, 6))
        df["cluster_id"].value_counts().sort_index().plot(kind="bar")
        plt.title("Cluster Frequencies")
        plt.xlabel("Cluster ID")
        plt.ylabel("Frequency")

        plot_path = os.path.join(self.output_dir, "cluster_frequencies.png")
        plt.savefig(plot_path)
        logger.info(f"Saved frequency plot to {plot_path}")
        plt.close()

    def save_cluster_csv(self, df: pd.DataFrame, filename="clusters.csv"):
        csv_path = os.path.join(self.output_dir, filename)
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved cluster data to {csv_path}")
