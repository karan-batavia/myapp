"""
Generate professional patent drawings for RVO submission
Creates PDF with proper diagrams (not ASCII art)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
import os

def create_figure_1():
    """System Architecture Overview"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    box1 = FancyBboxPatch((0.5, 1.5), 2.5, 3, boxstyle="round,pad=0.05", 
                           facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(box1)
    ax.text(1.75, 4.2, 'AI-MODEL\nINVOER', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(1.75, 3.0, '• PyTorch\n• TensorFlow\n• ONNX\n• scikit-learn', ha='center', va='center', fontsize=8)
    
    box2 = FancyBboxPatch((3.75, 1.5), 2.5, 3, boxstyle="round,pad=0.05",
                           facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(box2)
    ax.text(5.0, 4.2, 'ANALYSE-\nENGINE', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.0, 2.8, '• Framework Analyse\n• Bias Detectie\n• EU AI Act Check\n• NL Compliance', ha='center', va='center', fontsize=8)
    
    box3 = FancyBboxPatch((7.0, 1.5), 2.5, 3, boxstyle="round,pad=0.05",
                           facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(box3)
    ax.text(8.25, 4.2, 'COMPLIANCE\nUITVOER', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(8.25, 2.8, '• Risicoscore\n• Rapport\n• Aanbevelingen', ha='center', va='center', fontsize=8)
    
    ax.annotate('', xy=(3.65, 3), xytext=(3.1, 3),
                arrowprops=dict(arrowstyle='->', lw=2))
    ax.annotate('', xy=(6.9, 3), xytext=(6.35, 3),
                arrowprops=dict(arrowstyle='->', lw=2))
    
    ax.text(5.0, 5.5, 'FIGUUR 1: Systeemarchitectuuroverzicht', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_figure_2():
    """Multi-framework Analysis Module"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    outer_box = FancyBboxPatch((0.5, 2.5), 9, 2.5, boxstyle="round,pad=0.05",
                                facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(outer_box)
    ax.text(5.0, 4.7, 'FRAMEWORK ANALYSEMODULE', ha='center', va='center', fontsize=11, fontweight='bold')
    
    frameworks = [
        ('PyTorch\n.pt, .pth', 1.3),
        ('TensorFlow\n.h5, .pb', 3.4),
        ('ONNX\n.onnx', 5.5),
        ('scikit-learn\n.pkl, .joblib', 7.6)
    ]
    
    for name, x in frameworks:
        box = FancyBboxPatch((x, 2.8), 1.8, 1.2, boxstyle="round,pad=0.03",
                              facecolor='lightgray', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 0.9, 3.4, name, ha='center', va='center', fontsize=8)
    
    ax.annotate('', xy=(5.0, 1.8), xytext=(5.0, 2.4),
                arrowprops=dict(arrowstyle='->', lw=2))
    
    result_box = FancyBboxPatch((3.5, 0.8), 3, 1, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(result_box)
    ax.text(5.0, 1.3, 'Parameter Analyse\nComplexiteit Score', ha='center', va='center', fontsize=9)
    
    ax.text(5.0, 5.5, 'FIGUUR 2: Multi-framework Analysemodule', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_figure_3():
    """Bias Detection Engine"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    outer_box = FancyBboxPatch((0.5, 1), 9, 4, boxstyle="round,pad=0.05",
                                facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(outer_box)
    ax.text(5.0, 4.7, 'BIAS-DETECTIE-ENGINE', ha='center', va='center', fontsize=11, fontweight='bold')
    
    formulas = [
        'Demographic Parity:     P(Y=1|A=0) ≈ P(Y=1|A=1)',
        'Equalized Odds:         TPR₀ ≈ TPR₁  en  FPR₀ ≈ FPR₁',
        'Calibration Score:      P(Y=1|Score=s,A=0) ≈ P(Y=1|Score=s,A=1)',
        'Individual Fairness:    d(f(x₁),f(x₂)) ≤ L·d(x₁,x₂)'
    ]
    
    y_pos = 4.0
    for formula in formulas:
        ax.text(1.0, y_pos, formula, ha='left', va='center', fontsize=9, family='monospace')
        y_pos -= 0.7
    
    ax.text(5.0, 5.5, 'FIGUUR 3: Bias-detectie-engine', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_figure_4():
    """EU AI Act Compliance Assessor"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    outer_box = FancyBboxPatch((0.5, 1.5), 9, 3, boxstyle="round,pad=0.05",
                                facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(outer_box)
    ax.text(5.0, 4.2, 'EU AI ACT COMPLIANCEBEOORDELAAR', ha='center', va='center', fontsize=11, fontweight='bold')
    
    articles = [
        ('Artikel 5\nVerboden\nPraktijken', 1.5),
        ('Artikelen 19-24\nHoog-risico\nSystemen', 4.25),
        ('Art. 51-55\nGPAI\nModellen', 7.0)
    ]
    
    for name, x in articles:
        box = FancyBboxPatch((x, 1.8), 2.2, 1.8, boxstyle="round,pad=0.03",
                              facecolor='lightgray', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.1, 2.7, name, ha='center', va='center', fontsize=9)
    
    ax.text(5.0, 5.5, 'FIGUUR 4: EU AI Act Compliancebeoordelaar', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_figure_5():
    """Netherlands Specialization Module"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    outer_box = FancyBboxPatch((0.5, 1.5), 9, 3, boxstyle="round,pad=0.05",
                                facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(outer_box)
    ax.text(5.0, 4.2, 'NEDERLANDSE SPECIALISATIEMODULE', ha='center', va='center', fontsize=11, fontweight='bold')
    
    modules = [
        ('BSN-Detectie\nmet 11-proef', 1.5),
        ('UAVG-Compliance\nVerificatie', 4.25),
        ('Regionale\nBoetes', 7.0)
    ]
    
    for name, x in modules:
        box = FancyBboxPatch((x, 1.8), 2.2, 1.8, boxstyle="round,pad=0.03",
                              facecolor='lightgray', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.1, 2.7, name, ha='center', va='center', fontsize=9)
    
    ax.text(5.0, 5.5, 'FIGUUR 5: Nederlandse Specialisatiemodule', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_figure_6():
    """BSN Checksum Validation"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    outer_box = FancyBboxPatch((0.5, 1), 9, 4, boxstyle="round,pad=0.05",
                                facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(outer_box)
    ax.text(5.0, 4.7, 'BSN CHECKSUMVALIDATIE (NEDERLANDSE 11-PROEF)', ha='center', va='center', fontsize=11, fontweight='bold')
    
    ax.text(5.0, 3.5, 'Formule:', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.0, 2.7, 'checksum = (d₀×9) + (d₁×8) + (d₂×7) + (d₃×6) + (d₄×5) +', ha='center', va='center', fontsize=9, family='monospace')
    ax.text(5.0, 2.2, '           (d₅×4) + (d₆×3) + (d₇×2) - (d₈×1)', ha='center', va='center', fontsize=9, family='monospace')
    ax.text(5.0, 1.5, 'Geldigheid: BSN is geldig indien checksum mod 11 = 0', ha='center', va='center', fontsize=10, style='italic')
    
    ax.text(5.0, 5.5, 'FIGUUR 6: BSN Checksumvalidatie', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_figure_7():
    """System Flow Diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    steps_top = [
        ('Model\nAnalyse', 0.5),
        ('Bias\nDetectie', 3.25),
        ('EU AI Act\nBeoordeling', 6.0)
    ]
    
    steps_bottom = [
        ('Rapport\nGeneratie', 3.25),
        ('NL Privacy\nControle', 6.0)
    ]
    
    for name, x in steps_top:
        box = FancyBboxPatch((x, 3.5), 2.2, 1.2, boxstyle="round,pad=0.03",
                              facecolor='white', edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x + 1.1, 4.1, name, ha='center', va='center', fontsize=9)
    
    for name, x in steps_bottom:
        box = FancyBboxPatch((x, 1.5), 2.2, 1.2, boxstyle="round,pad=0.03",
                              facecolor='white', edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x + 1.1, 2.1, name, ha='center', va='center', fontsize=9)
    
    ax.annotate('', xy=(3.15, 4.1), xytext=(2.8, 4.1), arrowprops=dict(arrowstyle='->', lw=1.5))
    ax.annotate('', xy=(5.9, 4.1), xytext=(5.55, 4.1), arrowprops=dict(arrowstyle='->', lw=1.5))
    ax.annotate('', xy=(7.1, 3.4), xytext=(7.1, 2.8), arrowprops=dict(arrowstyle='->', lw=1.5))
    ax.annotate('', xy=(5.45, 2.1), xytext=(5.9, 2.1), arrowprops=dict(arrowstyle='->', lw=1.5))
    
    ax.text(5.0, 5.5, 'FIGUUR 7: Systeemflowdiagram', ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def save_all_figures():
    """Save all figures as individual PDFs and one combined PDF"""
    output_dir = 'attached_assets'
    
    figures = [
        (create_figure_1, 'RVO_Figuur_1_Systeemarchitectuur.pdf'),
        (create_figure_2, 'RVO_Figuur_2_Framework_Analyse.pdf'),
        (create_figure_3, 'RVO_Figuur_3_Bias_Detectie.pdf'),
        (create_figure_4, 'RVO_Figuur_4_EU_AI_Act.pdf'),
        (create_figure_5, 'RVO_Figuur_5_NL_Module.pdf'),
        (create_figure_6, 'RVO_Figuur_6_BSN_Validatie.pdf'),
        (create_figure_7, 'RVO_Figuur_7_Flowdiagram.pdf'),
    ]
    
    for create_func, filename in figures:
        fig = create_func()
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, format='pdf', bbox_inches='tight', dpi=300)
        plt.close(fig)
        print(f"✓ Created: {filepath}")
    
    from PyPDF2 import PdfMerger
    
    merger = PdfMerger()
    for _, filename in figures:
        filepath = os.path.join(output_dir, filename)
        merger.append(filepath)
    
    combined_path = os.path.join(output_dir, 'RVO_TEKENINGEN_COMPLEET.pdf')
    merger.write(combined_path)
    merger.close()
    print(f"\n✓ Combined PDF: {combined_path}")
    
    return combined_path

if __name__ == "__main__":
    print("Generating RVO Patent Drawings...")
    print("=" * 50)
    save_all_figures()
    print("=" * 50)
    print("Done! Submit 'RVO_TEKENINGEN_COMPLEET.pdf' to RVO.")
