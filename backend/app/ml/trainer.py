import json
import sys
from pathlib import Path
import numpy as np
from sklearn.model_selection import KFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
from app.utils.logger import logger
from app.services.anomaly_service import AnomalyService
from app.utils.helpers import extract_features


def get_backend_dir():
    return Path(__file__).parent.parent.parent


def train_model(train_data_path: str = "data/train_data.json") -> bool:
    logger.info("="*60)
    logger.info("HYBRID TRAINING PHASE")
    logger.info("="*60)
    
    try:
        backend_dir = get_backend_dir()
        train_file = backend_dir / train_data_path
        
        if not train_file.exists():
            logger.error(f"Training file not found: {train_file}")
            return False
        
        logger.info(f"Loading training data from {train_file.relative_to(backend_dir)}")
        with open(train_file, 'r') as f:
            train_events = json.load(f)
        
        logger.info(f"Loaded {len(train_events)} training events")
        
        normal = sum(1 for e in train_events if not e['is_anomalous'])
        anomalous = sum(1 for e in train_events if e['is_anomalous'])
        logger.info(f"Normal: {normal} ({normal/len(train_events)*100:.1f}%)")
        logger.info(f"Anomalous: {anomalous} ({anomalous/len(train_events)*100:.1f}%)")
        
        logger.info("Initializing Hybrid Anomaly Detection Service...")
        anomaly_svc = AnomalyService()
        
        logger.info("Training Isolation Forest + Gradient Boosting ensemble...")
        success = anomaly_svc.train(train_events)
        
        if not success:
            logger.error("Training failed")
            return False
        
        model_info = anomaly_svc.get_model_info()
        logger.info(f"Hybrid model trained successfully")
        logger.info(f"Type: {model_info.get('model_type')}")
        logger.info(f"Weights: {model_info.get('ensemble_weights')}")
        logger.info(f"Models saved to: {model_info.get('model_path')}")
        
        logger.info("="*60)
        logger.info("TRAINING COMPLETE")
        logger.info("="*60)
        
        return True
    
    except Exception as e:
        logger.error(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        return False


def evaluate_with_kfold(train_data_path: str = "data/train_data.json") -> dict:
    """Evaluate using K-Fold Cross-Validation (detects overfitting!)"""
    logger.info("="*60)
    logger.info("TESTING PHASE (5-Fold Cross-Validation)")
    logger.info("="*60)
    
    try:
        backend_dir = get_backend_dir()
        train_file = backend_dir / train_data_path
        
        if not train_file.exists():
            logger.error(f"Training file not found: {train_file}")
            return {}
        
        logger.info(f"Loading data from {train_file.relative_to(backend_dir)}")
        with open(train_file, 'r') as f:
            train_events = json.load(f)
        
        logger.info(f"Loaded {len(train_events)} events for cross-validation")
        
        # Extract features and labels
        X = np.array([extract_features(event) for event in train_events])
        y = np.array([1 if event['is_anomalous'] else 0 for event in train_events])
        
        logger.info("Running 5-Fold Cross-Validation...")
        logger.info("(Each fold uses 4 folds for training, 1 fold for testing)")
        
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        
        all_accuracies = []
        all_precisions = []
        all_recalls = []
        all_f1s = []
        all_roc_aucs = []
        
        fold = 1
        for train_idx, test_idx in kfold.split(X):
            logger.info(f"\n--- Fold {fold}/5 ---")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Train fresh model on this fold
            fold_events = [train_events[i] for i in train_idx]
            anomaly_svc = AnomalyService()
            anomaly_svc.train(fold_events)
            
            # Test on holdout fold
            test_events = [train_events[i] for i in test_idx]
            scores = []
            for event in test_events:
                score = anomaly_svc.detect_anomaly(event)
                scores.append(score)
            
            # Find optimal threshold
            threshold = np.median(scores)
            predictions = [1 if score > threshold else 0 for score in scores]
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, predictions)
            precision = precision_score(y_test, predictions, zero_division=0)
            recall = recall_score(y_test, predictions, zero_division=0)
            f1 = f1_score(y_test, predictions, zero_division=0)
            try:
                roc_auc = roc_auc_score(y_test, scores)
            except:
                roc_auc = 0.0
            
            all_accuracies.append(accuracy)
            all_precisions.append(precision)
            all_recalls.append(recall)
            all_f1s.append(f1)
            all_roc_aucs.append(roc_auc)
            
            logger.info(f"  Accuracy: {accuracy:.3f}")
            logger.info(f"  Precision: {precision:.3f}")
            logger.info(f"  Recall: {recall:.3f}")
            logger.info(f"  F1: {f1:.3f}")
            logger.info(f"  ROC-AUC: {roc_auc:.3f}")
            
            fold += 1
        
        # Calculate average metrics across all folds
        avg_accuracy = np.mean(all_accuracies)
        avg_precision = np.mean(all_precisions)
        avg_recall = np.mean(all_recalls)
        avg_f1 = np.mean(all_f1s)
        avg_roc_auc = np.mean(all_roc_aucs)
        
        std_accuracy = np.std(all_accuracies)
        std_f1 = np.std(all_f1s)
        
        # Print final results
        logger.info("="*60)
        logger.info("CROSS-VALIDATION RESULTS")
        logger.info("="*60)
        
        logger.info("\n Average Metrics (across 5 folds):")
        logger.info(f"Accuracy:    {avg_accuracy:.3f} ± {std_accuracy:.3f} ({avg_accuracy*100:.1f}%)")
        logger.info(f"Precision:   {avg_precision:.3f}")
        logger.info(f"Recall:      {avg_recall:.3f}")
        logger.info(f"F1 Score:    {avg_f1:.3f} ± {std_f1:.3f}")
        logger.info(f"ROC-AUC:     {avg_roc_auc:.3f}")
        
        logger.info("\n Per-Fold Results:")
        for i, (acc, f1) in enumerate(zip(all_accuracies, all_f1s)):
            logger.info(f"  Fold {i+1}: Accuracy={acc:.3f}, F1={f1:.3f}")
        
        # Check for overfitting
        logger.info("\n Overfitting Analysis:")
        if std_accuracy > 0.1:
            logger.warning(f"HIGH VARIANCE: {std_accuracy:.3f} (model unstable across folds)")
        else:
            logger.info(f"LOW VARIANCE: {std_accuracy:.3f} (model stable)")
        
        if avg_accuracy > 0.95:
            logger.warning("VERY HIGH ACCURACY: Check if data has data leakage")
        elif avg_accuracy > 0.90:
            logger.info("EXCELLENT: 90-95% accuracy (good generalization)")
        elif avg_accuracy > 0.85:
            logger.info("GOOD: 85-90% accuracy (acceptable)")
        else:
            logger.warning("LOW: <85% accuracy (model needs improvement)")
        
        logger.info("="*60)
        logger.info("TESTING COMPLETE")
        logger.info("="*60)
        
        return {
            "accuracy": avg_accuracy,
            "accuracy_std": std_accuracy,
            "precision": avg_precision,
            "recall": avg_recall,
            "f1_score": avg_f1,
            "f1_std": std_f1,
            "roc_auc": avg_roc_auc,
            "fold_accuracies": all_accuracies,
            "fold_f1s": all_f1s,
        }
    
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return {}


def main():
    logger.info("\n")

    train_success = train_model("data/train_data.json")
    
    if not train_success:
        logger.error("Training failed. Exiting.")
        return False
    
    logger.info("\n")
    
    # Evaluate with K-Fold CV
    cv_results = evaluate_with_kfold("data/train_data.json")
    
    if not cv_results:
        logger.error("Cross-validation failed.")
        return False
    
    # Final summary
    logger.info("\n")
    logger.info("Model trained and validated successfully!")
    logger.info(f"Accuracy: {cv_results.get('accuracy', 0):.1%} ± {cv_results.get('accuracy_std', 0):.1%}")
    logger.info(f"Recall: {cv_results.get('recall', 0):.1%}")
    logger.info(f"Precision: {cv_results.get('precision', 0):.1%}")
    logger.info(f"F1 Score: {cv_results.get('f1_score', 0):.1%} ± {cv_results.get('f1_std', 0):.1%}")
    logger.info(f"ROC-AUC: {cv_results.get('roc_auc', 0):.1%}")
    logger.info("\n Ready to use! Start the backend:")
    logger.info("uvicorn app.main:app --reload\n")
    
    return True


if __name__ == "__main__":
    import os
    
    backend_dir = get_backend_dir()
    os.chdir(backend_dir)
    logger.info(f"Working directory set to: {backend_dir}")
    
    success = main()
    sys.exit(0 if success else 1)