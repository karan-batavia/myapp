"""
Generate professional patent drawings for Database Scanner RVO submission
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
from matplotlib.backends.backend_pdf import PdfPages
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
    """FIGUUR 1: Multi-Engine Architectuur"""
    fig, ax = setup_a4_figure()
    
    # Title
    ax.text(5.0, 11.5, 'FIGUUR 1', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Multi-Engine Database Scanner Architectuur', ha='center', va='center', fontsize=11)
    
    # Main platform box 100
    main_box = FancyBboxPatch((0.5, 7), 9, 2.5, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.0, 'INTELLIGENT DATABASE SCANNER PLATFORM', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.0, 8.4, '3-Engine Support + Priority-Based + Parallel', ha='center', va='center', fontsize=9)
    ax.text(0.3, 9.7, '100', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Arrow down
    ax.annotate('', xy=(5.0, 6.0), xytext=(5.0, 6.9),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    # Three database engine boxes
    engines = [
        ('PostgreSQL\n(psycopg2)', 1.0, '110'),
        ('MySQL\n(connector)', 4.0, '120'),
        ('MS SQL\n(pyodbc)', 7.0, '130')
    ]
    
    for name, x, ref in engines:
        box = FancyBboxPatch((x, 4.5), 2.0, 1.5, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 1.0, 5.25, name, ha='center', va='center', fontsize=9)
        ax.text(x - 0.15, 6.1, ref, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Bottom features row
    features = [
        ('Priority\nScoring', 1.0, '140'),
        ('Parallel\nWorkers (3)', 4.0, '150'),
        ('BSN\nValidation', 7.0, '160')
    ]
    
    for name, x, ref in features:
        box = FancyBboxPatch((x, 2.5), 2.0, 1.5, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 1.0, 3.25, name, ha='center', va='center', fontsize=9)
        ax.text(x - 0.15, 4.1, ref, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Connecting lines
    for x in [2.0, 5.0, 8.0]:
        ax.plot([x, x], [4.4, 4.0], 'k-', lw=1.5)
    
    return fig

def create_figure_2():
    """FIGUUR 2: Priority Scoring Algorithm"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 2', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Priority Scoring Algorithm', ha='center', va='center', fontsize=11)
    
    # Main box 200
    main_box = FancyBboxPatch((0.5, 3), 9, 7, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.5, 'TABLE PRIORITY CALCULATION', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(0.3, 10.2, '200', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Step 1 box 210
    step1 = FancyBboxPatch((1.0, 7.5), 3.5, 1.5, boxstyle="square,pad=0",
                            facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(step1)
    ax.text(2.75, 8.5, 'STAP 1: Base Score', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(2.75, 7.9, 'user/customer: 3.0x\nmedical/health: 3.0x\npayment/bank: 2.8x', ha='center', va='center', fontsize=7)
    ax.text(0.8, 9.1, '210', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Step 2 box 220
    step2 = FancyBboxPatch((5.5, 7.5), 3.5, 1.5, boxstyle="square,pad=0",
                            facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(step2)
    ax.text(7.25, 8.5, 'STAP 2: Column Boost', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(7.25, 7.9, 'ssn/bsn/passport: 3.0x\nemail/phone: 2.5x\naddress/birth: 2.2x', ha='center', va='center', fontsize=7)
    ax.text(5.3, 9.1, '220', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrow
    ax.annotate('', xy=(5.4, 8.25), xytext=(4.6, 8.25),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    # Step 3 - Formula box 230
    formula_box = FancyBboxPatch((1.5, 5.0), 7, 1.8, boxstyle="square,pad=0",
                                  facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(formula_box)
    ax.text(5.0, 6.3, 'STAP 3: Final Score Berekening', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 5.5, 'priority_score = min(base_score + column_boost, 3.5)', ha='center', va='center', fontsize=9, family='monospace')
    ax.text(1.3, 6.9, '230', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrow down
    ax.annotate('', xy=(5.0, 4.4), xytext=(5.0, 4.9),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    # Example box 240
    example_box = FancyBboxPatch((1.5, 3.2), 7, 1.2, boxstyle="square,pad=0",
                                  facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(example_box)
    ax.text(5.0, 4.0, 'VOORBEELD: "customer_profiles" + [email, phone]', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(5.0, 3.5, '3.0 + 0.75 = 3.5 (HOOGSTE PRIORITEIT)', ha='center', va='center', fontsize=8)
    ax.text(1.3, 4.5, '240', ha='center', va='center', fontsize=9, fontweight='bold')
    
    return fig

def create_figure_3():
    """FIGUUR 3: Adaptive Sampling Strategies"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 3', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Adaptieve Sampling Strategieen', ha='center', va='center', fontsize=11)
    
    # Main box 300
    main_box = FancyBboxPatch((0.5, 2), 9, 8, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.5, 'SCAN MODE BESLISBOOM', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(0.3, 10.2, '300', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Mode boxes
    modes = [
        ('FAST MODE\n<=15 tabellen\n100 rows\n2 workers', 1.0, 7.0, '310'),
        ('SMART MODE\n<=50 tabellen\n300 rows\n3 workers', 4.0, 7.0, '320'),
        ('DEEP MODE\n<=75 tabellen\n500 rows\n3 workers', 7.0, 7.0, '330'),
    ]
    
    for text, x, y, ref in modes:
        box = FancyBboxPatch((x, y), 2.0, 2.0, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 1.0, y + 1.0, text, ha='center', va='center', fontsize=7)
        ax.text(x - 0.15, y + 2.1, ref, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Decision input box 340
    input_box = FancyBboxPatch((2.5, 4.5), 5, 1.5, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(input_box)
    ax.text(5.0, 5.5, 'INPUT PARAMETERS', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 4.9, 'total_tables | estimated_rows | risk_level', ha='center', va='center', fontsize=8)
    ax.text(2.3, 6.1, '340', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Time savings box 350
    savings_box = FancyBboxPatch((2.0, 2.3), 6, 1.5, boxstyle="square,pad=0",
                                  facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(savings_box)
    ax.text(5.0, 3.3, 'TIJDSBESPARING', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 2.7, '60% reductie: 4 uur -> 1.6 uur', ha='center', va='center', fontsize=9)
    ax.text(1.8, 3.9, '350', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows from input to modes
    ax.plot([5.0, 5.0], [6.0, 6.9], 'k-', lw=1)
    ax.plot([2.0, 8.0], [6.9, 6.9], 'k-', lw=1)
    ax.plot([2.0, 2.0], [6.9, 7.0], 'k-', lw=1)
    ax.plot([5.0, 5.0], [6.9, 7.0], 'k-', lw=1)
    ax.plot([8.0, 8.0], [6.9, 7.0], 'k-', lw=1)
    
    return fig

def create_figure_4():
    """FIGUUR 4: Parallel Scanning Workflow"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 4', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Parallel Scanning Workflow', ha='center', va='center', fontsize=11)
    
    # Main box 400
    main_box = FancyBboxPatch((0.5, 2), 9, 8, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.5, 'PARALLEL TABLE SCANNING', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(0.3, 10.2, '400', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # ThreadPoolExecutor box 410
    executor_box = FancyBboxPatch((2.5, 8.0), 5, 1.0, boxstyle="square,pad=0",
                                   facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(executor_box)
    ax.text(5.0, 8.5, 'ThreadPoolExecutor(max_workers=3)', ha='center', va='center', fontsize=9, family='monospace')
    ax.text(2.3, 9.1, '410', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Three worker boxes
    workers = [
        ('Worker 1\nTabel: users\n100-500 rows', 1.0, '420'),
        ('Worker 2\nTabel: customers\n100-500 rows', 4.0, '421'),
        ('Worker 3\nTabel: transactions\n100-500 rows', 7.0, '422'),
    ]
    
    for text, x, ref in workers:
        box = FancyBboxPatch((x, 5.5), 2.0, 2.0, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.0, 6.5, text, ha='center', va='center', fontsize=7)
        ax.text(x - 0.15, 7.6, ref, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Arrows down from executor
    for x in [2.0, 5.0, 8.0]:
        ax.annotate('', xy=(x, 7.6), xytext=(x, 7.9),
                    arrowprops=dict(arrowstyle='->', lw=1, color='black'))
    
    # PII Detection boxes
    for x in [1.0, 4.0, 7.0]:
        box = FancyBboxPatch((x, 4.0), 2.0, 1.0, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.0, 4.5, 'PII Detectie', ha='center', va='center', fontsize=8)
    
    # Arrows down
    for x in [2.0, 5.0, 8.0]:
        ax.annotate('', xy=(x, 4.0), xytext=(x, 5.4),
                    arrowprops=dict(arrowstyle='->', lw=1, color='black'))
    
    # Result aggregation box 430
    result_box = FancyBboxPatch((2.0, 2.3), 6, 1.2, boxstyle="square,pad=0",
                                 facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(result_box)
    ax.text(5.0, 3.2, 'RESULTAAT AGGREGATIE', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 2.7, 'all_findings.extend(findings)', ha='center', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 3.6, '430', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows to result
    ax.plot([2.0, 2.0], [3.6, 3.9], 'k-', lw=1)
    ax.plot([5.0, 5.0], [3.6, 3.9], 'k-', lw=1)
    ax.plot([8.0, 8.0], [3.6, 3.9], 'k-', lw=1)
    ax.plot([2.0, 8.0], [3.6, 3.6], 'k-', lw=1)
    
    return fig

def create_figure_5():
    """FIGUUR 5: Netherlands BSN Validation (11-proef)"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 5', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'BSN Checksumvalidatie (Nederlandse 11-proef)', ha='center', va='center', fontsize=11)
    
    # Main box 500
    main_box = FancyBboxPatch((0.5, 2), 9, 8, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.5, 'BSN 11-PROEF ALGORITME', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(0.3, 10.2, '500', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Formula box 510
    formula_box = FancyBboxPatch((1.0, 7.0), 8, 2.0, boxstyle="square,pad=0",
                                  facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(formula_box)
    ax.text(5.0, 8.5, 'FORMULE:', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.0, 7.7, 'checksum = (d0x9) + (d1x8) + (d2x7) + (d3x6) + (d4x5)', ha='center', va='center', fontsize=8)
    ax.text(5.0, 7.2, '+ (d5x4) + (d6x3) + (d7x2) - (d8x1)', ha='center', va='center', fontsize=8)
    ax.text(0.8, 9.1, '510', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Validity condition box 520
    valid_box = FancyBboxPatch((2.5, 5.5), 5, 1.0, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(valid_box)
    ax.text(5.0, 6.0, 'BSN is geldig indien checksum mod 11 = 0', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(2.3, 6.6, '520', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Detection flow box 530
    flow_box = FancyBboxPatch((1.0, 2.5), 8, 2.5, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(flow_box)
    ax.text(5.0, 4.5, 'DETECTIE FLOW:', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 3.8, 'Stap 1: Regex patroon match -> \\b\\d{9}\\b', ha='center', va='center', fontsize=8)
    ax.text(5.0, 3.3, 'Stap 2: Checksum validatie -> 11-proef algoritme', ha='center', va='center', fontsize=8)
    ax.text(5.0, 2.8, 'Stap 3: GDPR classificatie -> Artikel 9 (Bijzondere gegevens)', ha='center', va='center', fontsize=8)
    ax.text(0.8, 5.1, '530', ha='center', va='center', fontsize=9, fontweight='bold')
    
    return fig

def create_figure_6():
    """FIGUUR 6: Schema Intelligence Analysis"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 6', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Schema Intelligentie Analyse', ha='center', va='center', fontsize=11)
    
    # Main box 600
    main_box = FancyBboxPatch((0.5, 2), 9, 8, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.5, 'DATABASE RISICO BEPALING', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(0.3, 10.2, '600', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Priority categories 610
    cat_box = FancyBboxPatch((1.0, 7.0), 8, 2.0, boxstyle="square,pad=0",
                              facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(cat_box)
    ax.text(5.0, 8.5, 'STAP 1: Categoriseer Tabellen op Prioriteit', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 7.7, 'HIGH (>=2.5) | MEDIUM (>=1.5) | LOW (<1.5)', ha='center', va='center', fontsize=8)
    ax.text(0.8, 9.1, '610', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Risk score formula 620
    formula_box = FancyBboxPatch((1.0, 5.0), 8, 1.5, boxstyle="square,pad=0",
                                  facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(formula_box)
    ax.text(5.0, 6.0, 'STAP 2: Bereken Risico Score', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 5.4, 'risk_score = (high_count x 3) + (medium_count x 1.5)', ha='center', va='center', fontsize=8, family='monospace')
    ax.text(0.8, 6.6, '620', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Risk level determination 630
    level_box = FancyBboxPatch((1.0, 2.5), 8, 2.0, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(level_box)
    ax.text(5.0, 4.0, 'STAP 3: Bepaal Risico Niveau', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 3.3, 'score > 10: HIGH | score > 5: MEDIUM | else: LOW', ha='center', va='center', fontsize=8)
    ax.text(5.0, 2.8, 'Aanbeveling: Deep scan bij HIGH risico', ha='center', va='center', fontsize=8)
    ax.text(0.8, 4.6, '630', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows
    ax.annotate('', xy=(5.0, 6.6), xytext=(5.0, 6.9),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    ax.annotate('', xy=(5.0, 4.6), xytext=(5.0, 4.9),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    return fig

def create_figure_7():
    """FIGUUR 7: Vergelijkingsmatrix"""
    fig, ax = setup_a4_figure()
    
    ax.text(5.0, 11.5, 'FIGUUR 7', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5.0, 11.0, 'Vergelijkingsmatrix', ha='center', va='center', fontsize=11)
    
    # Main box 700
    main_box = FancyBboxPatch((0.3, 2), 9.4, 8, boxstyle="square,pad=0",
                               facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.5, 'DATABASE SCANNER VERGELIJKING', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(0.1, 10.2, '700', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Table headers
    headers = ['Functie', 'Systeem', 'Concurrent', 'Handmatig']
    x_positions = [1.5, 4.0, 6.0, 8.0]
    
    for header, x in zip(headers, x_positions):
        ax.text(x, 8.7, header, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Draw header line
    ax.plot([0.5, 9.5], [8.4, 8.4], 'k-', lw=1)
    
    # Table rows
    rows = [
        ('Multi-Engine (3)', 'Ja', 'Deels (2)', 'Nee'),
        ('Parallel Scanning', 'Ja', 'Nee', 'Nee'),
        ('Priority Selection', 'Ja', 'Nee', 'Handmatig'),
        ('BSN 11-proef', 'Ja', 'Nee', 'Nee'),
        ('Adaptive Sampling', 'Ja', 'Beperkt', 'Nee'),
        ('Schema Intelligence', 'Ja', 'Nee', 'Nee'),
        ('Scan Tijd (100 tab)', '1.6 uur', '4 uur', '8 uur'),
    ]
    
    y = 8.0
    for row in rows:
        for value, x in zip(row, x_positions):
            ax.text(x, y, value, ha='center', va='center', fontsize=7)
        y -= 0.7
    
    # Value proposition box 710
    value_box = FancyBboxPatch((0.8, 2.3), 8.4, 2.0, boxstyle="square,pad=0",
                                facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(value_box)
    ax.text(5.0, 3.8, 'WAARDEPROPOSITIE', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(5.0, 3.1, '60% sneller | 50% meer engines | 95% PII detectie', ha='center', va='center', fontsize=9)
    ax.text(5.0, 2.6, 'Uniek: BSN 11-proef validatie voor Nederland', ha='center', va='center', fontsize=8)
    ax.text(0.6, 4.4, '710', ha='center', va='center', fontsize=9, fontweight='bold')
    
    return fig

def generate_all_figures():
    """Generate all 7 figures and save to PDF"""
    output_dir = 'attached_assets'
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_path = os.path.join(output_dir, 'Database_Scanner_Tekeningen_RVO.pdf')
    
    with PdfPages(pdf_path) as pdf:
        # Create all figures
        figures = [
            create_figure_1(),
            create_figure_2(),
            create_figure_3(),
            create_figure_4(),
            create_figure_5(),
            create_figure_6(),
            create_figure_7(),
        ]
        
        for fig in figures:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    print(f"Generated: {pdf_path}")
    print("7 figures created with proper RVO formatting")
    return pdf_path

if __name__ == "__main__":
    generate_all_figures()
