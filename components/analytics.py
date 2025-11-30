# components/analytics.py
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt

class GuardianAnalytics:
    def __init__(self):
        self.analytics_file = "analytics/performance.json"
        os.makedirs("analytics", exist_ok=True)
    
    def record_scan_result(self, was_correct, confidence, threat_level):
        """Record each scan result for accuracy tracking"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'was_correct': was_correct,
            'confidence': confidence,
            'threat_level': threat_level
        }
        
        # Load existing data
        if os.path.exists(self.analytics_file):
            with open(self.analytics_file, 'r') as f:
                data = json.load(f)
        else:
            data = []
        
        data.append(entry)
        
        # Save updated data
        with open(self.analytics_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📊 Analytics recorded: Correct={was_correct}, Confidence={confidence}")
    
    def calculate_accuracy(self):
        """Calculate current accuracy rate"""
        if not os.path.exists(self.analytics_file):
            return 0.0
        
        with open(self.analytics_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            return 0.0
        
        correct_predictions = sum(1 for entry in data if entry['was_correct'])
        return correct_predictions / len(data)
    
    def generate_accuracy_chart(self):
        """Create visual proof of learning"""
        if not os.path.exists(self.analytics_file):
            return
        
        with open(self.analytics_file, 'r') as f:
            data = json.load(f)
        
        # Calculate rolling accuracy
        accuracies = []
        for i in range(len(data)):
            slice_data = data[:i+1]
            correct = sum(1 for entry in slice_data if entry['was_correct'])
            accuracies.append(correct / len(slice_data))
        
        # Create chart
        plt.figure(figsize=(10, 6))
        plt.plot(accuracies, marker='o', linewidth=2)
        plt.title('GUARDIAN AI Learning Progress')
        plt.xlabel('Number of Scans')
        plt.ylabel('Accuracy Rate')
        plt.grid(True, alpha=0.3)
        plt.savefig('analytics/learning_progress.png')
        print("✅ Accuracy chart saved: analytics/learning_progress.png")
        
        return accuracies[-1]  # Return current accuracy

# Global instance
analytics = GuardianAnalytics()