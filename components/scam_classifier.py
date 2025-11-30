# components/scam_classifier.py
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, roc_curve
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import os
from datasets import Dataset
import re
from collections import Counter

class ScamClassifier:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.labels = ["safe", "suspicious", "phishing", "urgent", "financial"]
        self.model_path = "models/scam_classifier"
        self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load existing model or train new one"""
        try:
            if os.path.exists(self.model_path):
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                print("✅ Loaded trained scam classifier")
            else:
                self._train_model()
        except Exception as e:
            print(f"❌ Model load failed: {e}")
            self._setup_fallback()
    
    def _train_model(self):
        """Train model on phishing datasets"""
        print("🔄 Training scam classifier...")
        
        # Load and prepare dataset
        dataset = self._create_synthetic_dataset()
        
        # Initialize model
        model_name = "distilbert-base-uncased"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=len(self.labels)
        )
        
        # FIXED: Updated TrainingArguments
        training_args = TrainingArguments(
            output_dir=self.model_path,
            learning_rate=2e-5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            num_train_epochs=1,  # Reduced for speed
            weight_decay=0.01,
            eval_strategy="epoch",  # FIXED: was evaluation_strategy
            save_strategy="epoch",
            load_best_model_at_end=True,
        )
        
        # Train
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            tokenizer=self.tokenizer,
        )
        
        trainer.train()
        trainer.save_model()
        self.tokenizer.save_pretrained(self.model_path)
        print("✅ Model trained and saved")
    
    def _create_synthetic_dataset(self):
        """Create training data from known phishing patterns"""
        phishing_examples = [
            "URGENT: Your account will be locked. Click http://bit.ly/fake-login to verify password.",
            "Dear User, verify your PayPal account now: http://fake-paypal-security.com",
            "IMPORTANT: Your bank account needs verification. Enter credentials at http://bank-security-update.com",
            "Security Alert: Unusual login detected. Confirm your identity: http://secure-verify-now.com",
            "You won $1000! Claim your prize: http://free-prize-winner.com/login"
        ]
        
        safe_examples = [
            "Welcome to our service. Contact support@company.com for assistance.",
            "Your order has been shipped. Tracking number: 123456789",
            "Meeting reminder: Tomorrow at 2 PM in conference room B.",
            "The weather today will be sunny with a high of 75 degrees.",
            "Your subscription will renew automatically next month."
        ]
        
        texts = phishing_examples + safe_examples
        labels = [2] * len(phishing_examples) + [0] * len(safe_examples)
        
        dataset = Dataset.from_dict({"text": texts, "label": labels})
        return dataset.train_test_split(test_size=0.2)
    
    def analyze_scam_risk(self, text: str) -> Dict:
        """ACTORS REE Pipeline: Reason → Evaluate → Execute"""
        if not text.strip():
            return self._empty_result()
        
        # REASON: Extract features and patterns
        features = self._extract_features(text)
        ml_analysis = self._ml_analysis(text)
        
        # EVALUATE: Score and rank threats
        risk_score = self._calculate_risk_score(features, ml_analysis)
        severity, reasons = self._classify_threat(features, ml_analysis, risk_score)
        
        # EXECUTE: Return actionable results
        return {
            "severity": severity,
            "reasons": reasons,
            "confidence": risk_score,
            "risk_score": risk_score,
            "ml_confidence": ml_analysis.get("confidence", 0.0),
            "features": features
        }
    
    def _ml_analysis(self, text: str) -> Dict:
        """Use the actual trained model"""
        if self.model is None:
            return {"confidence": 0.0, "prediction": "fallback"}
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            probs = torch.softmax(outputs.logits, dim=-1)
            confidence, predicted_class = torch.max(probs, dim=-1)
            
            return {
                "confidence": float(confidence),
                "prediction": self.labels[predicted_class],
                "all_probs": probs.numpy().tolist()
            }
        except Exception as e:
            print(f"ML analysis failed: {e}")
            return {"confidence": 0.0, "prediction": "error"}
    
    def _extract_features(self, text: str) -> Dict:
        """Enhanced feature extraction"""
        text_lower = text.lower()
        
        return {
            "urgency_words": self._count_urgency_indicators(text_lower),
            "suspicious_urls": self._find_suspicious_urls(text_lower),
            "password_requests": self._check_password_requests(text_lower),
            "financial_terms": self._check_financial_terms(text_lower),
            "generic_greetings": self._check_generic_greetings(text_lower),
            "length": len(text),
            "entropy": self._calculate_entropy(text),
            "has_popup_keywords": self._check_popup_keywords(text_lower)
        }
    
    def _count_urgency_indicators(self, text: str) -> int:
        urgency_terms = ["urgent", "immediately", "asap", "action required", "verify now"]
        return sum(1 for term in urgency_terms if term in text)
    
    def _find_suspicious_urls(self, text: str) -> int:
        urls = re.findall(r'https?://[^\s]+', text)
        suspicious_domains = ['bit.ly', 'tinyurl', 'click-here', 'verify-account']
        return sum(1 for url in urls if any(domain in url for domain in suspicious_domains))
    
    def _check_password_requests(self, text: str) -> int:
        password_terms = ["password", "login", "credentials", "account verification"]
        return 1 if any(term in text for term in password_terms) else 0
    
    def _check_financial_terms(self, text: str) -> int:
        financial_terms = ["paypal", "bank", "credit card", "ssn", "social security"]
        return 1 if any(term in text for term in financial_terms) else 0
    
    def _check_generic_greetings(self, text: str) -> int:
        greetings = ["dear user", "dear customer", "valued member"]
        return 1 if any(greeting in text for greeting in greetings) else 0
    
    def _check_popup_keywords(self, text: str) -> int:
        popup_terms = ["popup", "modal", "overlay", "dialog", "window", "alert", "notification"]
        return 1 if any(term in text for term in popup_terms) else 0
    
    def _calculate_entropy(self, text: str) -> float:
        if len(text) == 0:
            return 0.0
        counts = Counter(text)
        return -sum((count/len(text)) * np.log2(count/len(text)) for count in counts.values())
    
    def _calculate_risk_score(self, features: Dict, ml_analysis: Dict) -> float:
        """Enhanced risk scoring with ML integration"""
        base_score = 0.0
        
        # Traditional features (40%)
        weights = {
            "urgency_words": 0.10, "suspicious_urls": 0.15, 
            "password_requests": 0.10, "financial_terms": 0.05
        }
        
        for feature, weight in weights.items():
            if features[feature] > 0:
                base_score += weight * min(features[feature] / 3.0, 1.0)
        
        # ML confidence boost (60%)
        ml_boost = ml_analysis.get("confidence", 0.0) * 0.6
        
        # Popup window bonus
        if features["has_popup_keywords"]:
            base_score += 0.2
        
        return min(base_score + ml_boost, 1.0)
    
    def _classify_threat(self, features: Dict, ml_analysis: Dict, risk_score: float) -> Tuple[str, List[str]]:
        """ACTORS: Enhanced threat classification"""
        reasons = []
        
        # ML-based reasons
        ml_prediction = ml_analysis.get("prediction", "")
        if ml_prediction in ["phishing", "urgent", "financial"]:
            reasons.append(f"ml_detected_{ml_prediction}")
        
        # Feature-based reasons
        if features["urgency_words"] > 0:
            reasons.append("urgency_language")
        if features["suspicious_urls"] > 0:
            reasons.append("suspicious_url")
        if features["password_requests"] > 0:
            reasons.append("password_request")
        if features["has_popup_keywords"]:
            reasons.append("suspicious_popup")
        
        # Severity determination
        if risk_score >= 0.8 or ml_prediction == "phishing":
            severity = "critical"
        elif risk_score >= 0.6:
            severity = "high"
        elif risk_score >= 0.4:
            severity = "medium"
        else:
            severity = "low"
        
        return severity, reasons
    
    def _setup_fallback(self):
        """Enhanced fallback"""
        self.model = None
        print("⚠️ Using enhanced rule-based classifier with ACTORS reasoning")
    
    def _empty_result(self):
        return {
            "severity": "low",
            "reasons": [],
            "confidence": 0.0,
            "risk_score": 0.0,
            "features": {}
        }

# Singleton instance
scam_classifier = ScamClassifier()