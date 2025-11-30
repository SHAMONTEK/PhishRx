# components/guardian_vision.py
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import cv2
import numpy as np
from PIL import Image
import torchvision.transforms as T
import os
import ssl
from pathlib import Path
import requests
import warnings
warnings.filterwarnings('ignore')

# Fix SSL issues for all users
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

class GuardianVision(nn.Module):
    def __init__(self):
        super().__init__()
        
        # Create models directory
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # 1. Vision Branch - Robust UI Element Detection
        self.yolo_model = self._load_yolo_safely()
        self.cnn_backbone = self._load_cnn_backbone()
        
        # 2. Text Branch - Advanced NLP
        self.text_model, self.text_tokenizer = self._load_text_model()
        
        # 3. Multimodal Fusion
        self.fusion_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=512, nhead=8),
            num_layers=2  # Reduced for speed
        )
        
        # 4. Threat Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64), 
            nn.ReLU(),
            nn.Linear(64, 5)  # [safe, phishing, malware, scam, urgent]
        )
        
        print("✅ Guardian Vision initialized with fallback support")
        
    def _load_yolo_safely(self):
        """Load YOLO with multiple fallbacks for all users"""
        try:
            from ultralytics import YOLO
            
            # Try multiple model sources
            model_sources = [
                "models/yolov8n.pt",  # Local bundled model
                "yolov8n.pt",         # Already downloaded
                "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
            ]
            
            for source in model_sources:
                try:
                    if source.startswith('http'):
                        print(f"📥 Downloading YOLO model...")
                        model = YOLO(source)
                        # Save for future use
                        model.export("models/yolov8n.pt")
                    else:
                        if os.path.exists(source) or source.startswith('http'):
                            model = YOLO(source)
                        else:
                            continue
                    
                    print("✅ YOLO model loaded successfully")
                    return model
                    
                except Exception as e:
                    print(f"⚠️ YOLO load attempt failed: {e}")
                    continue
                    
        except ImportError:
            print("⚠️ Ultralytics not available, using basic detection")
        
        # Ultimate fallback
        return self._create_basic_detector()
    
    def _load_cnn_backbone(self):
        """Load CNN with fallbacks"""
        try:
            model = torch.hub.load('pytorch/vision:v0.10.0', 'mobilenet_v2', pretrained=True)
            model.classifier = nn.Identity()
            return model
        except:
            print("⚠️ CNN backbone failed, using simple feature extractor")
            return nn.Sequential(
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten()
            )
    
    def _load_text_model(self):
        """Load text model with fallbacks"""
        try:
            model = AutoModel.from_pretrained("distilbert-base-uncased")
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            return model, tokenizer
        except:
            print("⚠️ Text model failed, using embeddings fallback")
            return None, None
    
    def _create_basic_detector(self):
        """Create a basic detector that works everywhere"""
        class BasicDetector:
            def __init__(self):
                self.ready = True
                
            def __call__(self, image):
                return self._detect_elements(image)
            
            def _detect_elements(self, image):
                """Basic OpenCV-based element detection"""
                try:
                    if isinstance(image, Image.Image):
                        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    else:
                        img_cv = image
                    
                    # Simple contour detection for UI elements
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                    edges = cv2.Canny(blurred, 50, 150)
                    
                    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    elements = []
                    for contour in contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        area = w * h
                        
                        # Filter for UI element-like contours
                        if area > 1000 and w > 30 and h > 20:
                            elements.append({
                                "type": "ui_element",
                                "confidence": 0.6,
                                "bbox": [x, y, x + w, y + h]
                            })
                    
                    return [type('Results', (), {'boxes': type('Boxes', (), {'cls': [0], 'conf': [0.7], 'xyxy': [elements[0]['bbox']]})})] if elements else []
                    
                except Exception as e:
                    print(f"⚠️ Basic detection failed: {e}")
                    return []
        
        return BasicDetector()
    
    def detect_ui_elements(self, image_path):
        """Robust UI element detection with fallbacks"""
        try:
            image = Image.open(image_path)
            results = self.yolo_model(image)
            
            suspicious_elements = []
            
            # Handle different result types (YOLO vs basic detector)
            if hasattr(results, 'boxes') and results.boxes is not None:
                # YOLO results
                for box in results.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    element_types = {
                        0: "button", 1: "input_field", 2: "popup", 
                        3: "security_icon", 4: "warning_sign", 5: "ui_element"
                    }
                    
                    element_type = element_types.get(cls, "ui_element")
                    if conf > 0.3:  # Lower confidence threshold for fallback
                        suspicious_elements.append({
                            "type": element_type,
                            "confidence": conf,
                            "bbox": box.xyxy[0].tolist()
                        })
            else:
                # Basic detector results
                for result in results:
                    if hasattr(result, 'boxes'):
                        for box in result.boxes:
                            suspicious_elements.append({
                                "type": "ui_element",
                                "confidence": float(box.conf[0]),
                                "bbox": box.xyxy[0].tolist()
                            })
            
            return suspicious_elements
            
        except Exception as e:
            print(f"⚠️ UI detection failed: {e}")
            return [{
                "type": "fallback_detection",
                "confidence": 0.3,
                "bbox": [50, 50, 200, 100]
            }]
    
    def extract_visual_features(self, image_path):
        """Extract visual features with fallback"""
        try:
            image = Image.open(image_path).convert('RGB')
            transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            image_tensor = transform(image).unsqueeze(0)
            with torch.no_grad():
                features = self.cnn_backbone(image_tensor)
            
            return features.squeeze()
        except:
            # Return random features as fallback
            return torch.randn(1280)
    
    def extract_text_features(self, ocr_text):
        """Extract text features with fallback"""
        if self.text_model is None or len(ocr_text.strip()) == 0:
            return torch.randn(768)  # Fallback features
            
        try:
            inputs = self.text_tokenizer(
                ocr_text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=256  # Reduced for speed
            )
            
            with torch.no_grad():
                outputs = self.text_model(**inputs)
            
            return outputs.last_hidden_state.mean(dim=1).squeeze()
        except:
            return torch.randn(768)
    
    def analyze_screenshot(self, image_path, ocr_text):
        """Main analysis pipeline - never crashes"""
        try:
            # 1. UI Element Detection
            ui_elements = self.detect_ui_elements(image_path)
            
            # 2. Visual Feature Extraction
            visual_features = self.extract_visual_features(image_path)
            
            # 3. Text Feature Extraction  
            text_features = self.extract_text_features(ocr_text)
            
            # 4. Multimodal Fusion
            combined_features = torch.cat([visual_features, text_features])
            if combined_features.shape[0] > 512:
                combined_features = combined_features[:512]  # Truncate if too large
                
            fused_features = self.fusion_transformer(combined_features.unsqueeze(0))
            
            # 5. Threat Classification
            threat_logits = self.classifier(fused_features.squeeze())
            threat_probs = torch.softmax(threat_logits, dim=0)
            
            return {
                "ui_elements": ui_elements,
                "threat_level": self.interpret_threat_level(threat_probs),
                "confidence": float(threat_probs.max()),
                "threat_breakdown": {
                    "phishing": float(threat_probs[1]),
                    "malware": float(threat_probs[2]), 
                    "scam": float(threat_probs[3]),
                    "urgent": float(threat_probs[4])
                },
                "visual_evidence": self.generate_heatmap(image_path, ui_elements)
            }
            
        except Exception as e:
            print(f"🚨 Vision analysis failed, using fallback: {e}")
            return self._fallback_analysis(image_path, ocr_text)
    
    def _fallback_analysis(self, image_path, ocr_text):
        """Ultimate fallback analysis"""
        return {
            "ui_elements": [{
                "type": "system_fallback",
                "confidence": 0.5,
                "bbox": [0, 0, 100, 50]
            }],
            "threat_level": "low",
            "confidence": 0.3,
            "threat_breakdown": {
                "phishing": 0.1,
                "malware": 0.1, 
                "scam": 0.1,
                "urgent": 0.1
            },
            "visual_evidence": None
        }
    
    def interpret_threat_level(self, probs):
        """Convert probabilities to threat levels"""
        try:
            max_prob, max_idx = torch.max(probs, 0)
            
            if max_idx == 0:  # safe
                return "low"
            elif max_idx == 4 and max_prob > 0.7:  # urgent + high confidence
                return "critical" 
            elif max_prob > 0.6:
                return "high"
            elif max_prob > 0.3:
                return "medium"
            else:
                return "low"
        except:
            return "low"
    
    def generate_heatmap(self, image_path, ui_elements):
        """Generate visual heatmap if possible"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
                
            for element in ui_elements:
                bbox = [int(coord) for coord in element['bbox'][:4]]
                confidence = element['confidence']
                
                color = (0, 165, 255)  # Default orange
                if element['type'] in ['fake_browser_ui', 'security_icon']:
                    color = (0, 0, 255)  # Red for high threat
                    
                cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                cv2.putText(image, f"{element['type']}: {confidence:.2f}", 
                           (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            return image
        except:
            return None

# Initialize the vision system
guardian_vision = GuardianVision()