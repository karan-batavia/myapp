"""
Compliance score visualization utilities for DataGuardian Pro.
Provides interactive components for visualizing compliance scores in real-time.
"""
import streamlit as st
# Disable plotly and numpy to resolve dependency conflicts
# import plotly.express as px
# import plotly.graph_objects as go
# import pandas as pd
# import numpy as np
px = None
go = None
pd = None
np = None
from typing import Dict, List, Any, Optional, Tuple
import random
import json

# Constants for compliance scoring
COMPLIANCE_CATEGORIES = {
    "data_minimization": "Data Minimization",
    "purpose_limitation": "Purpose Limitation",
    "storage_limitation": "Storage Limitation", 
    "accuracy": "Accuracy",
    "transparency": "Transparency",
    "security": "Security & Integrity",
    "accountability": "Accountability",
    "lawfulness": "Lawfulness"
}

COMPLIANCE_WEIGHTS = {
    "data_minimization": 1.2,
    "purpose_limitation": 1.0,
    "storage_limitation": 1.0,
    "accuracy": 0.8,
    "transparency": 1.0,
    "security": 1.5,
    "accountability": 0.7,
    "lawfulness": 1.3
}

# Compliance colors based on score ranges
SCORE_COLORS = {
    "critical": "#d73027",  # Red (0-20%)
    "serious": "#fc8d59",   # Orange (20-40%)
    "moderate": "#fee090",  # Yellow (40-60%)
    "fair": "#91bfdb",      # Light Blue (60-80%)
    "excellent": "#4575b4"  # Dark Blue (80-100%)
}

def calculate_compliance_score(scan_results: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Calculate compliance score based on scan results.
    
    Args:
        scan_results: Dictionary containing scan results
        weights: Optional custom weights for compliance categories
        
    Returns:
        Dictionary with overall score and category scores
    """
    # Default to standard weights if not provided
    if weights is None:
        weights = COMPLIANCE_WEIGHTS
    
    # Extract relevant metrics from scan results
    total_pii = scan_results.get('total_pii_found', 0)
    high_risk = scan_results.get('high_risk_count', 0)
    medium_risk = scan_results.get('medium_risk_count', 0)
    low_risk = scan_results.get('low_risk_count', 0)
    
    # Initialize scores (base values ensure minimum compliance levels)
    category_scores = {
        "data_minimization": max(10, 100 - (total_pii * 0.5)),
        "purpose_limitation": random.uniform(60, 95),  # In a real system, derive from purpose documentation
        "storage_limitation": random.uniform(50, 95),  # In a real system, derive from retention policies
        "accuracy": max(25, 100 - (high_risk * 2) - (medium_risk * 1)),
        "transparency": random.uniform(40, 90),  # In a real system, derive from documentation analysis
        "security": max(20, 100 - (high_risk * 5) - (medium_risk * 2)),
        "accountability": random.uniform(30, 85),  # In a real system, derive from audit capability
        "lawfulness": max(30, 100 - (high_risk * 3) - (medium_risk * 1.5))
    }
    
    # Apply improvements based on remediation actions (if any)
    if scan_results.get('remediation_actions_taken', 0) > 0:
        remediation_impact = min(30, scan_results.get('remediation_actions_taken', 0) * 3)
        for category in category_scores:
            category_scores[category] = min(100, category_scores[category] + remediation_impact * 0.2)
    
    # Apply weights to calculate overall score
    weighted_scores = [
        score * weights.get(category, 1.0) 
        for category, score in category_scores.items()
    ]
    weight_sum = sum(weights.get(category, 1.0) for category in category_scores.keys())
    overall_score = sum(weighted_scores) / weight_sum if weight_sum > 0 else 0
    
    # Clamp scores to 0-100 range and round to nearest integer
    overall_score = round(max(0, min(100, overall_score)))
    category_scores = {k: round(max(0, min(100, v))) for k, v in category_scores.items()}
    
    # Determine score label based on range AND findings
    total_findings = scan_results.get('total_findings', high_risk + medium_risk + low_risk)
    if total_findings > 0:
        # Cannot be "Excellent" with any findings
        score_label = "Good" if overall_score >= 80 else \
                     "Acceptable" if overall_score >= 60 else \
                     "Moderate" if overall_score >= 40 else \
                     "Poor" if overall_score >= 20 else "Critical"
    else:
        # No findings - can be Excellent
        score_label = "Excellent" if overall_score >= 90 else \
                     "Very Good" if overall_score >= 80 else \
                     "Good" if overall_score >= 60 else \
                     "Moderate" if overall_score >= 40 else \
                     "Poor" if overall_score >= 20 else "Critical"
    
    # Get score color based on range
    score_color = SCORE_COLORS["excellent"] if overall_score >= 80 else \
                 SCORE_COLORS["fair"] if overall_score >= 60 else \
                 SCORE_COLORS["moderate"] if overall_score >= 40 else \
                 SCORE_COLORS["serious"] if overall_score >= 20 else SCORE_COLORS["critical"]
    
    return {
        "overall_score": overall_score,
        "score_label": score_label,
        "score_color": score_color,
        "category_scores": category_scores
    }

def display_compliance_gauge(score: int, title: str = "Compliance Score", size: int = 200, 
                            show_label: bool = True, key_suffix: str = None,
                            total_findings: int = 0) -> None:
    """
    Display an animated gauge chart for compliance score.
    
    Args:
        score: Compliance score (0-100)
        title: Title for the gauge
        size: Size of the gauge in pixels
        show_label: Whether to show the score label
        key_suffix: Optional suffix for unique keys
        total_findings: Number of findings (affects label)
    """
    # Determine color based on score
    color = SCORE_COLORS["excellent"] if score >= 80 else \
            SCORE_COLORS["fair"] if score >= 60 else \
            SCORE_COLORS["moderate"] if score >= 40 else \
            SCORE_COLORS["serious"] if score >= 20 else SCORE_COLORS["critical"]
    
    # Determine label - cannot be "Excellent" with findings
    if total_findings > 0:
        label = "Good" if score >= 80 else \
                "Acceptable" if score >= 60 else \
                "Moderate" if score >= 40 else \
                "Poor" if score >= 20 else "Critical"
    else:
        label = "Excellent" if score >= 90 else \
                "Very Good" if score >= 80 else \
                "Good" if score >= 60 else \
                "Moderate" if score >= 40 else \
                "Poor" if score >= 20 else "Critical"
    
    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 18}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 20], 'color': SCORE_COLORS["critical"]},
                {'range': [20, 40], 'color': SCORE_COLORS["serious"]},
                {'range': [40, 60], 'color': SCORE_COLORS["moderate"]},
                {'range': [60, 80], 'color': SCORE_COLORS["fair"]},
                {'range': [80, 100], 'color': SCORE_COLORS["excellent"]}
            ],
        }
    ))
    
    # Make it responsive and clean
    fig.update_layout(
        height=size,
        width=size,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#444", 'family': "Arial, sans-serif"}
    )
    
    # Create container with appropriate styling
    with st.container():
        # Display the gauge
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Display label if requested
        if show_label:
            st.markdown(
                f'<div style="text-align: center; font-size: 16px; color: {color}; font-weight: bold;">{label}</div>',
                unsafe_allow_html=True
            )

def display_compliance_radar(category_scores: Dict[str, int], title: str = "Compliance Categories",
                           show_legend: bool = True, size: Tuple[int, int] = (600, 400),
                           key_suffix: str = None) -> None:
    """
    Display a radar chart for compliance category scores.
    
    Args:
        category_scores: Dictionary mapping category keys to scores (0-100)
        title: Title for the radar chart
        show_legend: Whether to show the legend
        size: Size of the chart as (width, height)
        key_suffix: Optional suffix for unique keys
    """
    # Prepare data for the radar chart
    categories = []
    scores = []
    colors = []
    
    for category, score in category_scores.items():
        # Use readable category name if available
        readable_name = COMPLIANCE_CATEGORIES.get(category, category.replace('_', ' ').title())
        categories.append(readable_name)
        scores.append(score)
        
        # Determine color based on score
        color = SCORE_COLORS["excellent"] if score >= 80 else \
                SCORE_COLORS["fair"] if score >= 60 else \
                SCORE_COLORS["moderate"] if score >= 40 else \
                SCORE_COLORS["serious"] if score >= 20 else SCORE_COLORS["critical"]
        colors.append(color)
    
    # Create the radar chart
    fig = go.Figure()
    
    # Add the radar trace
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        line=dict(color='rgba(32, 84, 147, 0.8)', width=2),
        fillcolor='rgba(32, 84, 147, 0.4)',
        name='Compliance Score'
    ))
    
    # Add reference level at 60% (minimum acceptable compliance)
    fig.add_trace(go.Scatterpolar(
        r=[60] * len(categories),
        theta=categories,
        line=dict(color='rgba(232, 66, 58, 0.7)', width=1, dash='dash'),
        fill=None,
        name='Minimum Target (60%)'
    ))
    
    # Configure the layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[0, 20, 40, 60, 80, 100],
                ticktext=['0%', '20%', '40%', '60%', '80%', '100%'],
                tickfont=dict(size=10)
            )
        ),
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=18)
        ),
        showlegend=show_legend,
        width=size[0],
        height=size[1],
        margin=dict(l=60, r=60, t=60, b=30),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def display_compliance_score_card(compliance_score: Dict[str, Any], 
                               show_details: bool = True,
                               animate: bool = True,
                               key_suffix: str = None) -> None:
    """
    Display a comprehensive compliance score card with multiple visualizations.
    
    Args:
        compliance_score: Compliance score dictionary from calculate_compliance_score()
        show_details: Whether to show detailed category breakdown
        animate: Whether to animate the visualizations
        key_suffix: Optional suffix for unique keys
    """
    overall_score = compliance_score['overall_score']
    score_label = compliance_score['score_label']
    score_color = compliance_score['score_color']
    category_scores = compliance_score['category_scores']
    
    # Set up a key suffix if none provided
    if key_suffix is None:
        import uuid
        key_suffix = str(uuid.uuid4())[:8]
    
    # Create main card container with gradient background
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #f7f9fc 0%, #e4ebf5 100%);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        ">
            <h3 style="
                color: #2c3e50;
                margin: 0 0 15px 0;
                text-align: center;
                font-weight: 600;
            ">Real-Time Compliance Status</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Display score with two columns layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Animated gauge visualization
        display_compliance_gauge(
            overall_score, 
            title="Compliance Score", 
            size=250, 
            show_label=False,
            key_suffix=f"{key_suffix}_gauge"
        )
        
        # Score label with appropriate color
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: -15px;">
                <div style="
                    font-size: 16px;
                    font-weight: 600;
                    color: #555;
                    margin-bottom: 5px;
                ">Overall Rating</div>
                <div style="
                    font-size: 22px;
                    font-weight: 700;
                    color: {score_color};
                    margin-bottom: 5px;
                ">{score_label}</div>
                <div style="
                    font-size: 14px;
                    color: #555;
                    font-style: italic;
                ">Updated in real-time</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        # Radar chart for category breakdown
        display_compliance_radar(
            category_scores,
            title="Compliance Category Breakdown",
            show_legend=True,
            size=(None, 300),
            key_suffix=f"{key_suffix}_radar"
        )
    
    # Display detailed category breakdown if requested
    if show_details:
        st.markdown("#### Detailed Category Scores")
        
        # Create 4 columns for category cards
        cols = st.columns(4)
        
        # Display each category score in a card
        for i, (category, score) in enumerate(category_scores.items()):
            with cols[i % 4]:
                # Determine color based on score
                color = SCORE_COLORS["excellent"] if score >= 80 else \
                        SCORE_COLORS["fair"] if score >= 60 else \
                        SCORE_COLORS["moderate"] if score >= 40 else \
                        SCORE_COLORS["serious"] if score >= 20 else SCORE_COLORS["critical"]
                
                # Get readable category name
                readable_name = COMPLIANCE_CATEGORIES.get(category, category.replace('_', ' ').title())
                
                # Display score card
                st.markdown(
                    f"""
                    <div style="
                        background-color: white;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                        margin-bottom: 15px;
                        border-left: 5px solid {color};
                    ">
                        <div style="
                            font-size: 14px;
                            color: #555;
                            margin-bottom: 5px;
                        ">{readable_name}</div>
                        <div style="
                            font-size: 18px;
                            font-weight: 700;
                            color: {color};
                        ">{score}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Add recommendations section
    st.markdown("#### Compliance Recommendations")
    
    # Generate recommendations based on lowest scoring categories
    lowest_categories = sorted(
        [(COMPLIANCE_CATEGORIES.get(cat, cat.replace('_', ' ').title()), score) 
         for cat, score in category_scores.items()], 
        key=lambda x: x[1]
    )[:3]
    
    # Display recommendations in an expandable container
    with st.expander("View Recommended Actions", expanded=False):
        for category, score in lowest_categories:
            st.markdown(
                f"""
                <div style="
                    background-color: #f0f7ff;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                ">
                    <div style="font-weight: 600; color: #1e3a8a; margin-bottom: 5px;">
                        Improve {category} ({score}%)
                    </div>
                    <div style="color: #444;">
                        {generate_recommendation(category.lower(), score)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

def generate_recommendation(category: str, score: int) -> str:
    """
    Generate a compliance recommendation based on category and score.
    
    Args:
        category: The compliance category
        score: The current score for that category
        
    Returns:
        A recommendation string
    """
    recommendations = {
        "data minimization": [
            "Review and purge unnecessary PII data in your codebase and documents",
            "Implement data aggregation and anonymization techniques",
            "Create clear guidelines on what PII should and should not be collected"
        ],
        "purpose limitation": [
            "Document specific purposes for all PII collection and processing",
            "Review data usage to ensure it aligns with stated purposes",
            "Implement technical controls to prevent use beyond stated purposes"
        ],
        "storage limitation": [
            "Define and implement data retention policies for all PII",
            "Set up automated deletion of data that exceeds retention periods",
            "Review existing data stores for unnecessarily retained information"
        ],
        "accuracy": [
            "Implement validation controls for user-provided information",
            "Create processes for regular data quality reviews",
            "Provide easy mechanisms for users to update their personal data"
        ],
        "transparency": [
            "Update privacy policies to clearly explain all data processing",
            "Implement just-in-time notifications when collecting sensitive data",
            "Create a data inventory that maps all PII usage in your systems"
        ],
        "security": [
            "Encrypt all sensitive data at rest and in transit",
            "Implement proper access controls and authentication for all PII",
            "Conduct regular security assessments of systems with PII"
        ],
        "accountability": [
            "Document all compliance decisions and their justifications",
            "Maintain detailed data processing logs",
            "Implement regular compliance reviews and assign clear responsibilities"
        ],
        "lawfulness": [
            "Ensure valid legal basis exists for all processing activities",
            "Implement proper consent management where needed",
            "Review cross-border data transfers for compliance with regulations"
        ]
    }
    
    # Find closest matching category
    matched_category = None
    for key in recommendations.keys():
        if key in category.lower():
            matched_category = key
            break
    
    if matched_category is None:
        # Default recommendation if no match found
        return "Review your compliance approach for this category and implement necessary controls."
    
    # Select recommendations based on score
    if score < 30:
        # Critical issues - return all recommendations
        return " 1. " + "<br>2. ".join(recommendations[matched_category])
    elif score < 60:
        # Moderate issues - return top 2 recommendations
        return " 1. " + "<br>2. ".join(recommendations[matched_category][:2])
    else:
        # Minor issues - return top recommendation
        return recommendations[matched_category][0]