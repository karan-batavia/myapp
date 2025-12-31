"""
Generate professional patent drawings for RVO submission
Creates PDF with proper diagrams following RVO requirements:
- A4 paper size
- Margins: Left 2.5cm, Top/Right/Bottom 2.0cm
- Black and white only (no colors)
- Clear line art
- Reference numbers for parts
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

# A4 size in inches (210mm x 297mm)
A4_WIDTH_INCHES = 8.27
A4_HEIGHT_INCHES = 11.69

# Margins in inches (converted from cm)
MARGIN_LEFT = 2.5 / 2.54  # 2.5cm
MARGIN_RIGHT = 2.0 / 2.54  # 2.0cm
MARGIN_TOP = 2.0 / 2.54  # 2.0cm
MARGIN_BOTTOM = 2.0 / 2.54  # 2.0cm

def setup_a4_figure():
    """Create A4 sized figure with proper margins"""
    fig = plt.figure(figsize=(A4_WIDTH_INCHES, A4_HEIGHT_INCHES))
    
    # Calculate usable area
    left = MARGIN_LEFT / A4_WIDTH_INCHES
    bottom = MARGIN_BOTTOM / A4_HEIGHT_INCHES
    width = 1 - (MARGIN_LEFT + MARGIN_RIGHT) / A4_WIDTH_INCHES
    height = 1 - (MARGIN_TOP + MARGIN_BOTTOM) / A4_HEIGHT_INCHES
    
    ax = fig.add_axes([left, bottom, width, height])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    return fig, ax

def create_figure_1():
    """FIGUUR 1: Systeemarchitectuuroverzicht"""
    fig, ax = setup_a4_figure()
    
    # Title at top
    ax.text(5.0, 11.5, 'FIGUUR 1', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Systeemarchitectuuroverzicht', ha='center', va='center', fontsize=11)
    
    # Box 100: AI-MODEL INVOER
    box1 = FancyBboxPatch((0.5, 6), 2.5, 3, boxstyle="square,pad=0",
                           facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(box1)
    ax.text(1.75, 8.7, 'AI-MODEL', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(1.75, 8.3, 'INVOER', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(1.75, 7.4, '- PyTorch\n- TensorFlow\n- ONNX\n- scikit-learn', ha='center', va='center', fontsize=8)
    ax.text(0.3, 9.2, '100', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Box 200: ANALYSE-ENGINE
    box2 = FancyBboxPatch((3.75, 6), 2.5, 3, boxstyle="square,pad=0",
                           facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(box2)
    ax.text(5.0, 8.7, 'ANALYSE-', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 8.3, 'ENGINE', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 7.2, '- Framework Analyse\n- Bias Detectie\n- EU AI Act Check\n- NL Compliance', ha='center', va='center', fontsize=8)
    ax.text(3.55, 9.2, '200', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Box 300: COMPLIANCE UITVOER
    box3 = FancyBboxPatch((7.0, 6), 2.5, 3, boxstyle="square,pad=0",
                           facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(box3)
    ax.text(8.25, 8.7, 'COMPLIANCE', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(8.25, 8.3, 'UITVOER', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(8.25, 7.4, '- Risicoscore\n- Rapport\n- Aanbevelingen', ha='center', va='center', fontsize=8)
    ax.text(6.8, 9.2, '300', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Arrows
    ax.annotate('', xy=(3.65, 7.5), xytext=(3.1, 7.5),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    ax.annotate('', xy=(6.9, 7.5), xytext=(6.35, 7.5),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    return fig

def create_figure_2():
    """FIGUUR 2: Multi-framework Analysemodule"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 2', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Multi-framework Analysemodule', ha='center', va='center', fontsize=11)
    
    # Outer box 210
    outer_box = FancyBboxPatch((0.5, 6), 9, 3, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(5.0, 8.7, 'FRAMEWORK ANALYSEMODULE', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(0.3, 9.2, '210', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Inner boxes with reference numbers
    frameworks = [
        ('PyTorch\n.pt, .pth', 1.0, '211'),
        ('TensorFlow\n.h5, .pb', 3.2, '212'),
        ('ONNX\n.onnx', 5.4, '213'),
        ('scikit-learn\n.pkl, .joblib', 7.4, '214')
    ]
    
    for name, x, ref in frameworks:
        box = FancyBboxPatch((x, 6.3), 1.8, 1.2, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 0.9, 6.9, name, ha='center', va='center', fontsize=7)
        ax.text(x - 0.15, 7.6, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Arrow down
    ax.annotate('', xy=(5.0, 4.8), xytext=(5.0, 5.9),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    # Result box 220
    result_box = FancyBboxPatch((3.5, 3.8), 3, 1, boxstyle="square,pad=0",
                                 facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(result_box)
    ax.text(5.0, 4.3, 'Parameter Analyse\nComplexiteit Score', ha='center', va='center', fontsize=9)
    ax.text(3.3, 4.9, '220', ha='center', va='center', fontsize=10, fontweight='bold')
    
    return fig

def create_figure_3():
    """FIGUUR 3: Bias-detectie-engine"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 3', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Bias-detectie-engine', ha='center', va='center', fontsize=11)
    
    # Outer box 230
    outer_box = FancyBboxPatch((0.5, 5), 9, 4.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(5.0, 9.2, 'BIAS-DETECTIE-ENGINE', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(0.3, 9.7, '230', ha='center', va='center', fontsize=10, fontweight='bold')
    
    formulas = [
        ('231', 'Demographic Parity:     P(Y=1|A=0) = P(Y=1|A=1)'),
        ('232', 'Equalized Odds:         TPR(A=0) = TPR(A=1)'),
        ('233', 'Calibration Score:      P(Y=1|Score=s,A=0) = P(Y=1|Score=s,A=1)'),
        ('234', 'Individual Fairness:    d(f(x1),f(x2)) <= L*d(x1,x2)')
    ]
    
    y_pos = 8.5
    for ref, formula in formulas:
        ax.text(0.8, y_pos, ref, ha='left', va='center', fontsize=8, fontweight='bold')
        ax.text(1.5, y_pos, formula, ha='left', va='center', fontsize=9, family='monospace')
        y_pos -= 0.8
    
    return fig

def create_figure_4():
    """FIGUUR 4: EU AI Act Compliancebeoordelaar"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 4', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'EU AI Act Compliancebeoordelaar', ha='center', va='center', fontsize=11)
    
    # Outer box 240
    outer_box = FancyBboxPatch((0.5, 5.5), 9, 3.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(5.0, 8.7, 'EU AI ACT COMPLIANCEBEOORDELAAR', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(0.3, 9.2, '240', ha='center', va='center', fontsize=10, fontweight='bold')
    
    articles = [
        ('Artikel 5\nVerboden\nPraktijken', 1.2, '241'),
        ('Artikelen 19-24\nHoog-risico\nSystemen', 4.0, '242'),
        ('Art. 51-55\nGPAI\nModellen', 6.8, '243')
    ]
    
    for name, x, ref in articles:
        box = FancyBboxPatch((x, 5.8), 2.2, 2, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.1, 6.8, name, ha='center', va='center', fontsize=8)
        ax.text(x - 0.15, 7.9, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    return fig

def create_figure_5():
    """FIGUUR 5: Nederlandse Specialisatiemodule"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 5', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Nederlandse Specialisatiemodule', ha='center', va='center', fontsize=11)
    
    # Outer box 250
    outer_box = FancyBboxPatch((0.5, 5.5), 9, 3.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(5.0, 8.7, 'NEDERLANDSE SPECIALISATIEMODULE', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(0.3, 9.2, '250', ha='center', va='center', fontsize=10, fontweight='bold')
    
    modules = [
        ('BSN-Detectie\nmet 11-proef', 1.2, '251'),
        ('UAVG-Compliance\nVerificatie', 4.0, '252'),
        ('Regionale\nBoetes', 6.8, '253')
    ]
    
    for name, x, ref in modules:
        box = FancyBboxPatch((x, 5.8), 2.2, 2, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.1, 6.8, name, ha='center', va='center', fontsize=9)
        ax.text(x - 0.15, 7.9, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    return fig

def create_figure_6():
    """FIGUUR 6: BSN Checksumvalidatie"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 6', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'BSN Checksumvalidatie (Nederlandse 11-proef)', ha='center', va='center', fontsize=11)
    
    # Outer box 260
    outer_box = FancyBboxPatch((0.5, 5), 9, 4.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(0.3, 9.7, '260', ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.text(5.0, 8.8, 'Formule:', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(5.0, 7.8, 'checksum = (d0 x 9) + (d1 x 8) + (d2 x 7) + (d3 x 6) + (d4 x 5) +', ha='center', va='center', fontsize=9, family='monospace')
    ax.text(5.0, 7.2, '           (d5 x 4) + (d6 x 3) + (d7 x 2) - (d8 x 1)', ha='center', va='center', fontsize=9, family='monospace')
    ax.text(5.0, 6.0, 'Geldigheid: BSN is geldig indien checksum mod 11 = 0', ha='center', va='center', fontsize=10, style='italic')
    
    return fig

def create_figure_7():
    """FIGUUR 7: Systeemflowdiagram"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 7', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Systeemflowdiagram', ha='center', va='center', fontsize=11)
    
    # Top row boxes
    steps_top = [
        ('Model\nAnalyse', 0.5, '270'),
        ('Bias\nDetectie', 3.5, '271'),
        ('EU AI Act\nBeoordeling', 6.5, '272')
    ]
    
    for name, x, ref in steps_top:
        box = FancyBboxPatch((x, 7.5), 2.5, 1.5, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 1.25, 8.25, name, ha='center', va='center', fontsize=9)
        ax.text(x - 0.15, 9.1, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Bottom row boxes
    steps_bottom = [
        ('Rapport\nGeneratie', 3.5, '274'),
        ('NL Privacy\nControle', 6.5, '273')
    ]
    
    for name, x, ref in steps_bottom:
        box = FancyBboxPatch((x, 5), 2.5, 1.5, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 1.25, 5.75, name, ha='center', va='center', fontsize=9)
        ax.text(x - 0.15, 6.6, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Arrows
    ax.annotate('', xy=(3.4, 8.25), xytext=(3.1, 8.25), arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    ax.annotate('', xy=(6.4, 8.25), xytext=(6.1, 8.25), arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    ax.annotate('', xy=(7.75, 7.4), xytext=(7.75, 6.6), arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    ax.annotate('', xy=(6.0, 5.75), xytext=(6.4, 5.75), arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    return fig

def create_figure_8():
    """FIGUUR 8: Verwerkingspipeline"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 8', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Verwerkingspipeline', ha='center', va='center', fontsize=11)
    
    steps = [
        ('Upload', 0.2, '280'),
        ('Architectuur', 1.8, '281'),
        ('Bias', 3.6, '282'),
        ('EU AI Act', 5.0, '283'),
        ('NL Check', 6.6, '284'),
        ('Rapport', 8.2, '285')
    ]
    
    for name, x, ref in steps:
        box = FancyBboxPatch((x, 7), 1.4, 1.2, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 0.7, 7.6, name, ha='center', va='center', fontsize=8)
        ax.text(x - 0.1, 8.3, ref, ha='center', va='center', fontsize=7, fontweight='bold')
    
    # Arrows between boxes
    arrow_positions = [1.6, 3.4, 4.8, 6.4, 8.0]
    for x in arrow_positions:
        ax.annotate('', xy=(x + 0.2, 7.6), xytext=(x, 7.6), arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    return fig

def create_figure_9():
    """FIGUUR 9: Deploymentarchitectuur"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 9', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Deploymentarchitectuur', ha='center', va='center', fontsize=11)
    
    # Outer box 290
    outer_box = FancyBboxPatch((0.5, 5.5), 9, 3.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(5.0, 8.7, 'CONTAINERINFRASTRUCTUUR', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(0.3, 9.2, '290', ha='center', va='center', fontsize=10, fontweight='bold')
    
    containers = [
        ('Frontend\nStreamlit', 0.8, '291'),
        ('Database\nPostgreSQL', 3.0, '292'),
        ('Caching\nRedis', 5.2, '293'),
        ('AI-Analyse\nComponenten', 7.3, '294')
    ]
    
    for name, x, ref in containers:
        box = FancyBboxPatch((x, 5.8), 2.0, 2, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.0, 6.8, name, ha='center', va='center', fontsize=8)
        ax.text(x - 0.15, 7.9, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    return fig

def create_figure_10():
    """FIGUUR 10: Vergelijkingsmatrix"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 10', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Vergelijkingsmatrix', ha='center', va='center', fontsize=11)
    
    # Table headers
    headers = ['Functie', 'Systeem', 'Handmatig', 'Concurrent']
    col_widths = [3.0, 1.8, 1.8, 1.8]
    x_positions = [0.8, 3.9, 5.8, 7.7]
    
    # Draw header row
    for i, (header, x, w) in enumerate(zip(headers, x_positions, col_widths)):
        box = FancyBboxPatch((x, 8.5), w, 0.7, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + w/2, 8.85, header, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Table rows
    rows = [
        ['Multi-framework', 'Ja', 'Nee', 'Deels'],
        ['Bias-detectie', 'Ja', 'Beperkt', 'Beperkt'],
        ['EU AI Act 2025', 'Ja', 'Nee', 'Nee'],
        ['Nederlandse module', 'Ja', 'Nee', 'Nee']
    ]
    
    for row_idx, row in enumerate(rows):
        y = 7.7 - row_idx * 0.7
        for col_idx, (cell, x, w) in enumerate(zip(row, x_positions, col_widths)):
            box = FancyBboxPatch((x, y), w, 0.7, boxstyle="square,pad=0",
                                  facecolor='white', edgecolor='black', linewidth=1)
            ax.add_patch(box)
            ax.text(x + w/2, y + 0.35, cell, ha='center', va='center', fontsize=8)
    
    ax.text(0.5, 9.4, '300', ha='center', va='center', fontsize=10, fontweight='bold')
    
    return fig

def create_figure_11():
    """FIGUUR 11: Waardepropositie"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 11', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Waardepropositie', ha='center', va='center', fontsize=11)
    
    # Outer box 310
    outer_box = FancyBboxPatch((0.5, 5), 9, 4.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(outer_box)
    ax.text(0.3, 9.7, '310', ha='center', va='center', fontsize=10, fontweight='bold')
    
    propositions = [
        ('311', 'Kostenbesparing:    90% reductie vs handmatige audit'),
        ('312', 'Risicoreductie:     Proactieve compliance'),
        ('313', 'Snelheid:           <60 seconden per model'),
        ('314', 'EU AI Act:          100% artikeldekking')
    ]
    
    y_pos = 8.8
    for ref, prop in propositions:
        ax.text(0.8, y_pos, ref, ha='left', va='center', fontsize=8, fontweight='bold')
        ax.text(1.5, y_pos, prop, ha='left', va='center', fontsize=10, family='monospace')
        y_pos -= 0.9
    
    return fig

def save_all_figures():
    """Save all figures as individual PDFs and one combined PDF"""
    output_dir = 'attached_assets'
    
    figures = [
        (create_figure_1, 'RVO_Figuur_01_Systeemarchitectuur.pdf'),
        (create_figure_2, 'RVO_Figuur_02_Framework_Analyse.pdf'),
        (create_figure_3, 'RVO_Figuur_03_Bias_Detectie.pdf'),
        (create_figure_4, 'RVO_Figuur_04_EU_AI_Act.pdf'),
        (create_figure_5, 'RVO_Figuur_05_NL_Module.pdf'),
        (create_figure_6, 'RVO_Figuur_06_BSN_Validatie.pdf'),
        (create_figure_7, 'RVO_Figuur_07_Flowdiagram.pdf'),
        (create_figure_8, 'RVO_Figuur_08_Verwerkingspipeline.pdf'),
        (create_figure_9, 'RVO_Figuur_09_Deploymentarchitectuur.pdf'),
        (create_figure_10, 'RVO_Figuur_10_Vergelijkingsmatrix.pdf'),
        (create_figure_11, 'RVO_Figuur_11_Waardepropositie.pdf'),
    ]
    
    for create_func, filename in figures:
        fig = create_func()
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, format='pdf', dpi=300)
        plt.close(fig)
        print(f"Created: {filepath}")
    
    from PyPDF2 import PdfMerger
    
    merger = PdfMerger()
    for _, filename in figures:
        filepath = os.path.join(output_dir, filename)
        merger.append(filepath)
    
    combined_path = os.path.join(output_dir, 'RVO_TEKENINGEN_COMPLEET.pdf')
    merger.write(combined_path)
    merger.close()
    print(f"\nCombined PDF: {combined_path}")
    
    print("\n=== RVO Requirements Checklist ===")
    print("[X] A4 Paper Size")
    print("[X] Margins: Left 2.5cm, Top/Right/Bottom 2.0cm")
    print("[X] Black and white only (no colors)")
    print("[X] Clear line art (not ASCII text)")
    print("[X] Reference numbers for parts (100, 200, 300...)")
    print("[X] Figure titles at top")
    
    return combined_path

if __name__ == "__main__":
    print("Generating RVO Patent Drawings (11 Figures)...")
    print("Following RVO requirements:")
    print("- A4 paper size")
    print("- Margins: Left 2.5cm, Top/Right/Bottom 2.0cm")
    print("- Black and white only")
    print("- Reference numbers for components")
    print("=" * 50)
    save_all_figures()
    print("=" * 50)
    print("Done! Submit 'RVO_TEKENINGEN_COMPLEET.pdf' to RVO.")
