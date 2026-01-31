"""
Sample AI Model Code for EU AI Act Compliance Testing
This file contains patterns that should trigger various EU AI Act article detections.
"""

import torch
import torch.nn as nn

# This is an AI system using deep learning for biometric identification
# Training data includes personal data from EU citizens

class BiometricIdentificationModel(nn.Module):
    """
    High-risk AI system for facial recognition and biometric identification.
    Uses neural networks for automated decision making about individuals.
    """
    
    def __init__(self):
        super().__init__()
        self.facial_recognition = nn.Sequential(
            nn.Conv2d(3, 64, 3),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3),
            nn.ReLU(),
        )
        # No human oversight implemented
        # No DPIA conducted
        # No transparency measures
        
    def forward(self, x):
        # Automated decision making for employment screening
        # Uses machine learning for social scoring
        return self.facial_recognition(x)

# GPAI Model - General Purpose AI with systemic risk
class LargeLanguageModel(nn.Module):
    """
    General purpose AI model - transformer architecture
    10^25 FLOP training compute - systemic risk classification
    """
    def __init__(self):
        super().__init__()
        self.transformer = nn.Transformer()
        # Foundation model for downstream tasks
        # No model documentation provided
        # No copyright compliance policy

# Training configuration
training_config = {
    'personal_data': True,
    'eu_citizens_data': True,
    'training_data_governance': None,  # Missing data governance
    'human_oversight': False,  # No human oversight
    'risk_management_system': None,  # Missing risk management
    'technical_documentation': None,  # Missing documentation
    'quality_management_system': None,  # Missing QMS
}
