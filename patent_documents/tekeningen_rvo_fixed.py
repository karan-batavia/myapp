"""
Generate RVO-compliant patent drawings (Tekeningen)
Only reference numbers allowed - no descriptive text
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white
import os

def create_rvo_compliant_drawings():
    """Create patent drawings with only reference numbers (no text labels)"""
    
    output_path = "patent_documents/Tekeningen_RVO_Compliant.pdf"
    os.makedirs("patent_documents", exist_ok=True)
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    margin_left = 25 * mm
    margin_right = 25 * mm
    margin_top = 25 * mm
    margin_bottom = 25 * mm
    
    def draw_box(x, y, w, h, ref_num):
        """Draw a box with reference number"""
        c.rect(x, y, w, h)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 2*mm, y + h + 2*mm, str(ref_num))
    
    def draw_arrow(x1, y1, x2, y2):
        """Draw connecting arrow"""
        c.line(x1, y1, x2, y2)
    
    # FIGUUR 1 - Multi-Engine Database Scanner Architecture
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 1")
    
    # Main platform box (100)
    c.rect(margin_left + 20*mm, height - 80*mm, 140*mm, 25*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left + 22*mm, height - 53*mm, "100")
    
    # Three database engine boxes (110, 120, 130)
    box_width = 35*mm
    box_height = 20*mm
    y_engines = height - 120*mm
    
    # 110 - PostgreSQL
    x1 = margin_left + 20*mm
    c.rect(x1, y_engines, box_width, box_height)
    c.drawString(x1 + 2*mm, y_engines + box_height + 2*mm, "110")
    c.line(x1 + box_width/2, y_engines + box_height, x1 + box_width/2, height - 80*mm)
    
    # 120 - MySQL
    x2 = margin_left + 70*mm
    c.rect(x2, y_engines, box_width, box_height)
    c.drawString(x2 + 2*mm, y_engines + box_height + 2*mm, "120")
    c.line(x2 + box_width/2, y_engines + box_height, x2 + box_width/2, height - 80*mm)
    
    # 130 - MS SQL
    x3 = margin_left + 120*mm
    c.rect(x3, y_engines, box_width, box_height)
    c.drawString(x3 + 2*mm, y_engines + box_height + 2*mm, "130")
    c.line(x3 + box_width/2, y_engines + box_height, x3 + box_width/2, height - 80*mm)
    
    # Processing modules (140, 150, 160)
    y_modules = height - 160*mm
    
    # 140 - Priority Scoring
    c.rect(x1, y_modules, box_width, box_height)
    c.drawString(x1 + 2*mm, y_modules + box_height + 2*mm, "140")
    c.line(x1 + box_width/2, y_modules + box_height, x1 + box_width/2, y_engines)
    
    # 150 - Parallel Workers
    c.rect(x2, y_modules, box_width, box_height)
    c.drawString(x2 + 2*mm, y_modules + box_height + 2*mm, "150")
    c.line(x2 + box_width/2, y_modules + box_height, x2 + box_width/2, y_engines)
    
    # 160 - BSN Validation
    c.rect(x3, y_modules, box_width, box_height)
    c.drawString(x3 + 2*mm, y_modules + box_height + 2*mm, "160")
    c.line(x3 + box_width/2, y_modules + box_height, x3 + box_width/2, y_engines)
    
    c.showPage()
    
    # FIGUUR 2 - Priority Scoring Algorithm
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 2")
    
    # Main box (200)
    c.rect(margin_left + 30*mm, height - 70*mm, 100*mm, 20*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left + 32*mm, height - 48*mm, "200")
    
    # Step boxes (210, 220)
    y_steps = height - 110*mm
    c.rect(margin_left + 20*mm, y_steps, 45*mm, 25*mm)
    c.drawString(margin_left + 22*mm, y_steps + 27*mm, "210")
    
    c.rect(margin_left + 95*mm, y_steps, 45*mm, 25*mm)
    c.drawString(margin_left + 97*mm, y_steps + 27*mm, "220")
    
    # Lines connecting to main
    c.line(margin_left + 42*mm, y_steps + 25*mm, margin_left + 60*mm, height - 70*mm)
    c.line(margin_left + 117*mm, y_steps + 25*mm, margin_left + 100*mm, height - 70*mm)
    
    # Calculation box (230)
    y_calc = height - 155*mm
    c.rect(margin_left + 40*mm, y_calc, 80*mm, 20*mm)
    c.drawString(margin_left + 42*mm, y_calc + 22*mm, "230")
    c.line(margin_left + 42*mm, y_steps, margin_left + 60*mm, y_calc + 20*mm)
    c.line(margin_left + 117*mm, y_steps, margin_left + 100*mm, y_calc + 20*mm)
    
    # Example box (240)
    y_example = height - 195*mm
    c.rect(margin_left + 30*mm, y_example, 100*mm, 20*mm)
    c.drawString(margin_left + 32*mm, y_example + 22*mm, "240")
    c.line(margin_left + 80*mm, y_calc, margin_left + 80*mm, y_example + 20*mm)
    
    c.showPage()
    
    # FIGUUR 3 - Adaptive Sampling Strategies
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 3")
    
    # Main decision box (300)
    c.rect(margin_left + 40*mm, height - 65*mm, 80*mm, 18*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left + 42*mm, height - 45*mm, "300")
    
    # Three mode boxes (310, 320, 330)
    y_modes = height - 110*mm
    box_w = 38*mm
    
    c.rect(margin_left + 10*mm, y_modes, box_w, 25*mm)
    c.drawString(margin_left + 12*mm, y_modes + 27*mm, "310")
    c.line(margin_left + 29*mm, y_modes + 25*mm, margin_left + 55*mm, height - 65*mm)
    
    c.rect(margin_left + 60*mm, y_modes, box_w, 25*mm)
    c.drawString(margin_left + 62*mm, y_modes + 27*mm, "320")
    c.line(margin_left + 80*mm, y_modes + 25*mm, margin_left + 80*mm, height - 65*mm)
    
    c.rect(margin_left + 110*mm, y_modes, box_w, 25*mm)
    c.drawString(margin_left + 112*mm, y_modes + 27*mm, "330")
    c.line(margin_left + 129*mm, y_modes + 25*mm, margin_left + 105*mm, height - 65*mm)
    
    # Parameters box (340)
    y_params = height - 155*mm
    c.rect(margin_left + 40*mm, y_params, 80*mm, 20*mm)
    c.drawString(margin_left + 42*mm, y_params + 22*mm, "340")
    
    # Result box (350)
    y_result = height - 195*mm
    c.rect(margin_left + 40*mm, y_result, 80*mm, 20*mm)
    c.drawString(margin_left + 42*mm, y_result + 22*mm, "350")
    c.line(margin_left + 80*mm, y_params, margin_left + 80*mm, y_result + 20*mm)
    
    c.showPage()
    
    # FIGUUR 4 - Parallel Scanning Workflow
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 4")
    
    # Main executor box (400)
    c.rect(margin_left + 30*mm, height - 65*mm, 100*mm, 18*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left + 32*mm, height - 45*mm, "400")
    
    # Executor sub-box (410)
    c.rect(margin_left + 50*mm, height - 90*mm, 60*mm, 15*mm)
    c.drawString(margin_left + 52*mm, height - 73*mm, "410")
    c.line(margin_left + 80*mm, height - 65*mm, margin_left + 80*mm, height - 75*mm)
    
    # Three worker boxes (420, 421, 422)
    y_workers = height - 135*mm
    worker_w = 35*mm
    
    c.rect(margin_left + 10*mm, y_workers, worker_w, 30*mm)
    c.drawString(margin_left + 12*mm, y_workers + 32*mm, "420")
    c.line(margin_left + 27*mm, y_workers + 30*mm, margin_left + 55*mm, height - 90*mm)
    
    c.rect(margin_left + 62*mm, y_workers, worker_w, 30*mm)
    c.drawString(margin_left + 64*mm, y_workers + 32*mm, "421")
    c.line(margin_left + 80*mm, y_workers + 30*mm, margin_left + 80*mm, height - 90*mm)
    
    c.rect(margin_left + 115*mm, y_workers, worker_w, 30*mm)
    c.drawString(margin_left + 117*mm, y_workers + 32*mm, "422")
    c.line(margin_left + 132*mm, y_workers + 30*mm, margin_left + 105*mm, height - 90*mm)
    
    # Aggregation box (430)
    y_agg = height - 180*mm
    c.rect(margin_left + 40*mm, y_agg, 80*mm, 20*mm)
    c.drawString(margin_left + 42*mm, y_agg + 22*mm, "430")
    c.line(margin_left + 27*mm, y_workers, margin_left + 55*mm, y_agg + 20*mm)
    c.line(margin_left + 80*mm, y_workers, margin_left + 80*mm, y_agg + 20*mm)
    c.line(margin_left + 132*mm, y_workers, margin_left + 105*mm, y_agg + 20*mm)
    
    c.showPage()
    
    # FIGUUR 5 - BSN Checksum Validation
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 5")
    
    # Main algorithm box (500)
    c.rect(margin_left + 30*mm, height - 65*mm, 100*mm, 18*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left + 32*mm, height - 45*mm, "500")
    
    # Formula box (510)
    c.rect(margin_left + 20*mm, height - 110*mm, 120*mm, 30*mm)
    c.drawString(margin_left + 22*mm, height - 78*mm, "510")
    c.line(margin_left + 80*mm, height - 65*mm, margin_left + 80*mm, height - 80*mm)
    
    # Validation box (520)
    c.rect(margin_left + 40*mm, height - 145*mm, 80*mm, 20*mm)
    c.drawString(margin_left + 42*mm, height - 123*mm, "520")
    c.line(margin_left + 80*mm, height - 110*mm, margin_left + 80*mm, height - 125*mm)
    
    # Detection flow box (530)
    c.rect(margin_left + 20*mm, height - 200*mm, 120*mm, 40*mm)
    c.drawString(margin_left + 22*mm, height - 158*mm, "530")
    c.line(margin_left + 80*mm, height - 145*mm, margin_left + 80*mm, height - 160*mm)
    
    c.showPage()
    
    # FIGUUR 6 - Schema Intelligence Analysis
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 6")
    
    # Main box (600)
    c.rect(margin_left + 30*mm, height - 65*mm, 100*mm, 18*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left + 32*mm, height - 45*mm, "600")
    
    # Step 1 box (610)
    c.rect(margin_left + 25*mm, height - 110*mm, 110*mm, 30*mm)
    c.drawString(margin_left + 27*mm, height - 78*mm, "610")
    c.line(margin_left + 80*mm, height - 65*mm, margin_left + 80*mm, height - 80*mm)
    
    # Step 2 box (620)
    c.rect(margin_left + 25*mm, height - 155*mm, 110*mm, 30*mm)
    c.drawString(margin_left + 27*mm, height - 123*mm, "620")
    c.line(margin_left + 80*mm, height - 110*mm, margin_left + 80*mm, height - 125*mm)
    
    # Step 3 box (630)
    c.rect(margin_left + 25*mm, height - 200*mm, 110*mm, 30*mm)
    c.drawString(margin_left + 27*mm, height - 168*mm, "630")
    c.line(margin_left + 80*mm, height - 155*mm, margin_left + 80*mm, height - 170*mm)
    
    c.showPage()
    
    # FIGUUR 7 - Comparison Matrix (Table format with ref numbers only)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - margin_top, "FIGUUR 7")
    
    # Main table box (700)
    table_x = margin_left + 10*mm
    table_y = height - 200*mm
    table_w = 140*mm
    table_h = 140*mm
    
    c.rect(table_x, table_y, table_w, table_h)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(table_x + 2*mm, table_y + table_h + 2*mm, "700")
    
    # Draw grid lines (7 rows, 4 columns)
    row_height = table_h / 8
    col_width = table_w / 4
    
    for i in range(1, 8):
        c.line(table_x, table_y + i * row_height, table_x + table_w, table_y + i * row_height)
    
    for i in range(1, 4):
        c.line(table_x + i * col_width, table_y, table_x + i * col_width, table_y + table_h)
    
    # Value proposition box (710)
    c.rect(margin_left + 20*mm, height - 235*mm, 120*mm, 20*mm)
    c.drawString(margin_left + 22*mm, height - 213*mm, "710")
    c.line(margin_left + 80*mm, table_y, margin_left + 80*mm, height - 215*mm)
    
    c.save()
    
    print(f"RVO-compliant drawings saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    create_rvo_compliant_drawings()
