from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.utils.logger import logger


class EmbeddingService:
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        
        self.model_name = model_name
        self.model = None
        self.load_model()
    
    def load_model(self) -> bool:
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.model = None
            return False
    
    def embed_text(self, text: str) -> Optional[np.ndarray]:
    
        try:
            if not self.model:
                logger.error("Model not loaded")
                return None
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return None
    
    def embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
    
        try:
            if not self.model:
                logger.error("Model not loaded")
                return None
            
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            return None
    
    def similarity(self, text1: str, text2: str) -> float:
        
        try:
            embedding1 = self.embed_text(text1)
            embedding2 = self.embed_text(text2)
            
            if embedding1 is None or embedding2 is None:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def batch_similarity(self, text: str, texts: List[str]) -> List[float]:
        
        try:
            embedding1 = self.embed_text(text)
            embeddings2 = self.embed_texts(texts)
            
            if embedding1 is None or embeddings2 is None:
                return [0.0] * len(texts)
            
            # Calculate cosine similarities
            similarities = []
            for embedding2 in embeddings2:
                sim = np.dot(embedding1, embedding2) / (
                    np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                )
                similarities.append(float(sim))
            
            return similarities
        except Exception as e:
            logger.error(f"Error calculating batch similarity: {e}")
            return [0.0] * len(texts)
    
    def get_model_info(self) -> Dict[str, Any]:
        try:
            return {
                "model_name": self.model_name,
                "embedding_dim": self.model.get_sentence_embedding_dimension() if self.model else None,
                "is_loaded": self.model is not None,
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}