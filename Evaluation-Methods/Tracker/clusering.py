import os
# import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Base = declarative_base()


class EvaluationLog(Base):
    __tablename__ = 'evaluation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String, nullable=False)
    question_text = Column(String, nullable=False)
    response_text = Column(String, nullable=False)
    scores = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    question_embedding = Column(JSON, nullable=True)
    response_embedding = Column(JSON, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    temporal_order = Column(Integer, nullable=True)


@dataclass
class ConversationEntry:
    question_id: str
    question_text: str
    response_text: str
    scores: Dict[str, int]
    timestamp: datetime
    question_embedding: Optional[np.ndarray] = None
    response_embedding: Optional[np.ndarray] = None
    cluster_id: Optional[int] = None
    temporal_order: Optional[int] = None


class DatabaseHandler:
    def __init__(self, connection_string: str) -> None:
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("Database connection established")
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def fetch_logs(self, limit: Optional[int] = None) -> List[ConversationEntry]:
        session = self.get_session()
        try:
            query = session.query(EvaluationLog).order_by(EvaluationLog.timestamp)
            if limit:
                query = query.limit(limit)
            
            logs = query.all()
            entries = []
            for log in logs:
                entry = ConversationEntry(
                    question_id=log.question_id,
                    question_text=log.question_text,
                    response_text=log.response_text,
                    scores=log.scores,
                    timestamp=log.timestamp,
                    question_embedding=np.array(log.question_embedding) if log.question_embedding is not None else None,
                    response_embedding=np.array(log.response_embedding) if log.response_embedding is not None else None,
                    cluster_id=log.cluster_id,
                    temporal_order=log.temporal_order
                )
                
                entries.append(entry)
            
            logger.info(f"Fetched {len(entries)} evaluation logs")
            return entries
        finally:
            session.close()
    
    def insert_log(self, entry: ConversationEntry) -> None:
        session = self.get_session()
        try:
            log = EvaluationLog(
                question_id=entry.question_id,
                question_text=entry.question_text,
                response_text=entry.response_text,
                scores=entry.scores,
                timestamp=entry.timestamp,
                question_embedding=entry.question_embedding.tolist() if entry.question_embedding is not None else None,
                response_embedding=entry.response_embedding.tolist() if entry.response_embedding is not None else None,
                cluster_id=entry.cluster_id,
                temporal_order=entry.temporal_order
            )
            session.add(log)
            session.commit()
            logger.info(f"Inserted log for question_id: {entry.question_id}")
        finally:
            session.close()
    
    def update_cluster_assignments(self, assignments: List[Tuple[str, int, int]]) -> None:
        session = self.get_session()
        try:
            for question_id, cluster_id, temporal_order in assignments:
                session.query(EvaluationLog).filter(
                    EvaluationLog.question_id == question_id
                ).update({
                    'cluster_id': cluster_id,
                    'temporal_order': temporal_order
                })
            session.commit()
            logger.info(f"Updated {len(assignments)} cluster assignments")
        finally:
            session.close()
    
    def update_embeddings(self, question_id: str, q_emb: np.ndarray, r_emb: np.ndarray) -> None:
        session = self.get_session()
        try:
            session.query(EvaluationLog).filter(
                EvaluationLog.question_id == question_id
            ).update({
                'question_embedding': q_emb.tolist(),
                'response_embedding': r_emb.tolist()
            })
            session.commit()
        finally:
            session.close()


class ChatbotAPI:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"ChatbotAPI initialized with model: {model_name}")
    
    def generate_response(self, question: str) -> str:
        try:
            response = self.model.generate_content(question)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise


class Embedder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        logger.info(f"Embedder initialized with model: {model_name}")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings
    
    def embed_single(self, text: str) -> np.ndarray:
        return self.model.encode([text], show_progress_bar=False)[0]


class ClusterEngine:
    def __init__(self, use_transformer: bool = True, n_clusters: int = 5):
        self.use_transformer = use_transformer
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        logger.info(f"ClusterEngine initialized (transformer={use_transformer}, n_clusters={n_clusters})")
    
    def cluster_with_temporal(
        self, 
        embeddings: np.ndarray, 
        temporal_weights: np.ndarray,
        method: str = 'kmeans'
    ) -> np.ndarray:
        temporal_weights_normalized = temporal_weights.reshape(-1, 1) / np.max(temporal_weights)
        combined_features = np.hstack([embeddings, temporal_weights_normalized])
        scaled_features = self.scaler.fit_transform(combined_features)
        
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        elif method == 'hierarchical':
            clusterer = AgglomerativeClustering(n_clusters=self.n_clusters)
        else:
            raise ValueError(f"Unknown clustering method: {method}")
        
        cluster_labels = clusterer.fit_predict(scaled_features)
        logger.info(f"Clustering completed using {method}")
        return cluster_labels
    
    def cluster_entries(
        self, 
        entries: List[ConversationEntry],
        use_questions: bool = True,
        method: str = 'kmeans'
    ) -> List[ConversationEntry]:
        if use_questions:
            embeddings = np.array([e.question_embedding for e in entries])
        else:
            embeddings = np.array([e.response_embedding for e in entries])
        
        temporal_order = np.arange(len(entries))
        cluster_labels = self.cluster_with_temporal(embeddings, temporal_order, method)
        
        for idx, entry in enumerate(entries):
            entry.cluster_id = int(cluster_labels[idx])
            entry.temporal_order = idx
        
        return entries


class ConversationTracker:
    def __init__(self, db_handler: DatabaseHandler, embedder: Embedder, cluster_engine: ClusterEngine):
        self.db_handler = db_handler
        self.embedder = embedder
        self.cluster_engine = cluster_engine
        logger.info("ConversationTracker initialized")
    
    def process_new_question(
        self, 
        question_id: str, 
        question_text: str,
        chatbot_api: ChatbotAPI,
        scores: Optional[Dict[str, int]] = None
    ) -> ConversationEntry:
        response_text = chatbot_api.generate_response(question_text)
        
        q_embedding = self.embedder.embed_single(question_text)
        r_embedding = self.embedder.embed_single(response_text)
        
        if scores is None:
            scores = {"safety": 0, "empathy": 0, "helpfulness": 0}
        
        entry = ConversationEntry(
            question_id=question_id,
            question_text=question_text,
            response_text=response_text,
            scores=scores,
            timestamp=datetime.now(),
            question_embedding=q_embedding,
            response_embedding=r_embedding
        )
        
        self.db_handler.insert_log(entry)
        logger.info(f"Processed new question: {question_id}")
        return entry
    
    def recompute_clusters(self, use_questions: bool = True, method: str = 'kmeans') -> None:
        entries = self.db_handler.fetch_logs()
        
        missing_embeddings = [e for e in entries if e.question_embedding is None or e.response_embedding is None]
        if missing_embeddings:
            logger.info(f"Computing embeddings for {len(missing_embeddings)} entries")
            for entry in missing_embeddings:
                entry.question_embedding = self.embedder.embed_single(entry.question_text)
                entry.response_embedding = self.embedder.embed_single(entry.response_text)
                self.db_handler.update_embeddings(
                    entry.question_id, 
                    entry.question_embedding, 
                    entry.response_embedding
                )
        
        clustered_entries = self.cluster_engine.cluster_entries(entries, use_questions, method)
        
        assignments = [(e.question_id, e.cluster_id, e.temporal_order) for e in clustered_entries]
        self.db_handler.update_cluster_assignments(assignments)
        
        logger.info("Cluster recomputation completed")
    
    def get_cluster_patterns(self) -> pd.DataFrame:
        entries = self.db_handler.fetch_logs()
        
        data = {
            'question_id': [e.question_id for e in entries],
            'temporal_order': [e.temporal_order for e in entries],
            'cluster_id': [e.cluster_id for e in entries],
            'timestamp': [e.timestamp for e in entries]
        }
        
        df = pd.DataFrame(data).sort_values('temporal_order')
        logger.info("Generated cluster patterns dataframe")
        return df
    
    def get_cluster_transitions(self) -> List[Tuple[int, int]]:
        df = self.get_cluster_patterns()
        if len(df) < 2:
            return []
        
        transitions = []
        for i in range(len(df) - 1):
            current_cluster = df.iloc[i]['cluster_id']
            next_cluster = df.iloc[i + 1]['cluster_id']
            transitions.append((current_cluster, next_cluster))
        
        return transitions


class EvaluationPipeline:
    def __init__(
        self,
        db_connection_string: str,
        gemini_api_key: str,
        n_clusters: int = 5,
        embedding_model: str = 'all-MiniLM-L6-v2'
    ):
        self.db_handler = DatabaseHandler(db_connection_string)
        self.chatbot_api = ChatbotAPI(gemini_api_key)
        self.embedder = Embedder(embedding_model)
        self.cluster_engine = ClusterEngine(use_transformer=True, n_clusters=n_clusters)
        self.tracker = ConversationTracker(self.db_handler, self.embedder, self.cluster_engine)
        logger.info("EvaluationPipeline initialized")
    
    def run_full_pipeline(self, questions: List[Dict[str, Any]]) -> None:
        for q in questions:
            self.tracker.process_new_question(
                question_id=q['question_id'],
                question_text=q['question_text'],
                chatbot_api=self.chatbot_api,
                scores=q.get('scores')
            )
        
        self.tracker.recompute_clusters(use_questions=True, method='kmeans')
        
        patterns = self.tracker.get_cluster_patterns()
        logger.info(f"Cluster patterns:\n{patterns}")
        
        transitions = self.tracker.get_cluster_transitions()
        logger.info(f"Cluster transitions: {transitions}")


if __name__ == "__main__":
    DB_CONNECTION = "postgresql://user:password@localhost:5432/chatbot_eval"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
    
    pipeline = EvaluationPipeline(
        db_connection_string=DB_CONNECTION,
        gemini_api_key=GEMINI_API_KEY,
        n_clusters=5
    )
    
    sample_questions = [
        {
            "question_id": "q1",
            "question_text": "How do I reset my password?",
            "scores": {"safety": 1, "empathy": 2, "helpfulness": 3}
        },
        {
            "question_id": "q2",
            "question_text": "What are your business hours?",
            "scores": {"safety": 1, "empathy": 2, "helpfulness": 3}
        }
    ]
    
    pipeline.run_full_pipeline(sample_questions)