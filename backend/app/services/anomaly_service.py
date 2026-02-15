import numpy as np
import joblib
from typing import Dict, Any, Optional, List
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from app.config import settings
from app.utils.logger import logger
from app.utils.helpers import extract_features


class AnomalyService:
   
    
    def __init__(self, model_path: str = settings.MODEL_PATH):
    
        self.model_path = model_path
        self.iso_forest = None
        self.logistic_reg = None
        self.is_trained = False
        self.load_models()
    
    def load_models(self) -> bool:
        
        try:
            iso_path = Path(str(self.model_path).replace('.pkl', '_iso.pkl'))
            lr_path = Path(str(self.model_path).replace('.pkl', '_lr.pkl'))
            
            iso_exists = iso_path.exists()
            lr_exists = lr_path.exists()
            
            if iso_exists:
                self.iso_forest = joblib.load(iso_path)
                logger.info(f"Isolation Forest loaded from {iso_path}")
            
            if lr_exists:
                self.logistic_reg = joblib.load(lr_path)
                logger.info(f"Logistic Regression loaded from {lr_path}")
            
            self.is_trained = iso_exists and lr_exists
            
            if self.is_trained:
                logger.info("Both models loaded successfully")
                return True
            else:
                logger.warning("Models not found, initializing untrained")
                self.iso_forest = IsolationForest(
                    contamination=0.5,
                    random_state=42,
                    n_estimators=50  
                )
                self.logistic_reg = LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    C=0.1,  
                    solver='lbfgs'
                )
                return False
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.is_trained = False
            return False
    
    def save_models(self) -> bool:
        
        try:
            if self.iso_forest is None or self.logistic_reg is None:
                logger.error("No models to save")
                return False
            
            iso_path = Path(str(self.model_path).replace('.pkl', '_iso.pkl'))
            lr_path = Path(str(self.model_path).replace('.pkl', '_lr.pkl'))
            
            iso_path.parent.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.iso_forest, iso_path)
            joblib.dump(self.logistic_reg, lr_path)
            
            logger.info(f"Isolation Forest saved to {iso_path}")
            logger.info(f"Logistic Regression saved to {lr_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
    
    def train(self, login_events: List[Dict[str, Any]]) -> bool:
        
        try:
            if len(login_events) < 10:
                logger.error("Need at least 10 samples to train")
                return False
            
            logger.info(f"Training conservative hybrid detector on {len(login_events)} samples")
            
            # Extract features from all events
            X = np.array([extract_features(event) for event in login_events])
            y = np.array([1 if event['is_anomalous'] else 0 for event in login_events])
            
            # Train weak Isolation Forest
            logger.info("Training Isolation Forest (weak, 50 estimators)...")
            self.iso_forest = IsolationForest(
                contamination=0.5,
                random_state=42,
                n_estimators=50,  
                max_samples='auto'
            )
            self.iso_forest.fit(X)
            logger.info("Isolation Forest trained (conservative)")
            
            # Train Logistic Regression with STRONG regularization
            logger.info("Training Logistic Regression (strong regularization, C=0.1)...")
            self.logistic_reg = LogisticRegression(
                max_iter=1000,
                random_state=42,
                C=0.1,  
                solver='lbfgs',
                penalty='l2'
            )
            self.logistic_reg.fit(X, y)
            logger.info("Logistic Regression trained (conservative)")
            
            # Get training accuracy
            train_score = self.logistic_reg.score(X, y)
            logger.info(f"   Training accuracy: {train_score:.3f}")
            
            if train_score > 0.99:
                logger.warning("Training accuracy >99% - may overfit")
            elif train_score > 0.95:
                logger.info("Training accuracy 95-99% (good)")
            else:
                logger.info("Training accuracy <95% (conservative)")
            
            self.is_trained = True
            
            # Save models
            self.save_models()
            
            logger.info("Conservative hybrid detector training completed")
            return True
        
        except Exception as e:
            logger.error(f"Error training hybrid detector: {e}")
            import traceback
            traceback.print_exc()
            self.is_trained = False
            return False
    
    def detect_anomaly(self, login_event: Dict[str, Any]) -> float:
       
        try:
            if not self.is_trained or self.iso_forest is None or self.logistic_reg is None:
                logger.warning("Models not trained, returning neutral score")
                return 0.5
            
            # Extract features
            features = extract_features(login_event)
            features = features.reshape(1, -1)
            
            # Score 1: Isolation Forest (unsupervised)
            iso_score = self.iso_forest.score_samples(features)[0]
            iso_normalized = (iso_score - (-1.0)) / (0.5 - (-1.0))
            iso_normalized = max(0.0, min(1.0, iso_normalized))
            
            # Score 2: Logistic Regression (supervised, regularized)
            lr_proba = self.logistic_reg.predict_proba(features)[0]
            lr_score = lr_proba[1]
            
            ensemble_score = (0.5 * lr_score) + (0.5 * iso_normalized)
            
            logger.debug(f"IF: {iso_normalized:.3f}, LR: {lr_score:.3f}, Ensemble: {ensemble_score:.3f}")
            
            return float(ensemble_score)
        
        except Exception as e:
            logger.error(f"Error detecting anomaly: {e}")
            return 0.5
    
    def batch_detect(self, login_events: List[Dict[str, Any]]) -> List[float]:
        
        try:
            if not self.is_trained:
                logger.warning("Models not trained")
                return [0.5] * len(login_events)
            
            # Extract features
            X = np.array([extract_features(event) for event in login_events])
            
            # Isolation Forest scores
            iso_scores = self.iso_forest.score_samples(X)
            iso_normalized = (iso_scores - (-1.0)) / (0.5 - (-1.0))
            iso_normalized = np.clip(iso_normalized, 0.0, 1.0)
            
            # Logistic Regression scores
            lr_probas = self.logistic_reg.predict_proba(X)
            lr_scores = lr_probas[:, 1]
            
            # Conservative ensemble scores
            ensemble_scores = (0.5 * lr_scores) + (0.5 * iso_normalized)
            
            return [float(s) for s in ensemble_scores]
        
        except Exception as e:
            logger.error(f"Error in batch detection: {e}")
            return [0.5] * len(login_events)
    
    def get_model_info(self) -> Dict[str, Any]:
        try:
            return {
                "is_trained": self.is_trained,
                "model_type": "Conservative Hybrid (Isolation Forest + Logistic Regression)",
                "iso_forest_estimators": self.iso_forest.n_estimators if self.iso_forest else None,
                "iso_forest_contamination": self.iso_forest.contamination if self.iso_forest else None,
                "logistic_reg_C": self.logistic_reg.C if self.logistic_reg else None,
                "logistic_reg_penalty": "L2",
                "ensemble_weights": "50% LR + 50% IF",
                "model_path": str(self.model_path),
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}