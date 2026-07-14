import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def draw_header_footer(canvas, doc):
    canvas.saveState()
    # Draw top running header
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(colors.HexColor('#475569'))
    canvas.drawString(54, doc.height + 54 + 10, "FORMUAI — DOE FORMULATION SURROGATE MODEL STACK")
    
    # Draw bottom running footer
    canvas.setFont('Helvetica', 8)
    canvas.drawString(54, 36, "Technical Design & System Architecture Document")
    page_num = canvas.getPageNumber()
    canvas.drawRightString(doc.width + 54, 36, f"Page {page_num}")
    
    # Draw separator line at the top
    canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
    canvas.setLineWidth(0.5)
    canvas.line(54, doc.height + 54 + 5, doc.width + 54, doc.height + 54 + 5)
    canvas.restoreState()

def draw_cover_page(canvas, doc):
    canvas.saveState()
    # Deep Slate Background
    canvas.setFillColor(colors.HexColor('#0F172A'))
    canvas.rect(0, 0, 8.5 * inch, 11 * inch, fill=True, stroke=False)
    
    # Accent color side band
    canvas.setFillColor(colors.HexColor('#10B981')) # Emerald Green accent
    canvas.rect(0, 0, 0.4 * inch, 11 * inch, fill=True, stroke=False)
    canvas.restoreState()

def create_pdf(filename="DOE_Surrogate_Project_Architecture.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#0F172A') # Slate
    accent_color = colors.HexColor('#10B981')  # Emerald
    text_color = colors.HexColor('#334155')    # Charcoal
    code_bg = colors.HexColor('#F8FAFC')
    border_color = colors.HexColor('#E2E8F0')
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=30,
        leading=36,
        textColor=colors.white,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceAfter=30
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#94A3B8'),
        spaceAfter=5
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0369A1'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1E293B'),
        backColor=code_bg,
        borderColor=border_color,
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=5,
        spaceAfter=8
    )

    story = []
    
    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("FormuAI", title_style))
    story.append(Paragraph("DOE-Validated Formulation Surrogate Model Stack (CCD + OLS-RSM vs. RandomForest)", subtitle_style))
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("AUTHOR: Madhura Joshi (IIT Madras)", meta_style))
    story.append(Paragraph("TARGET ROLE: Digital R&D Data Scientist / Digital Transformation", meta_style))
    story.append(Paragraph("DATE: July 2026", meta_style))
    story.append(PageBreak())
    
    # ------------------ PAGE 2: ARCHITECTURE ------------------
    story.append(Paragraph("1. Executive Summary & System Conception", h1_style))
    story.append(Paragraph(
        "FMCG product development traditionally relies on physical trial-and-error laboratory formulations. "
        "FormuAI implements the complete digital R&D workflow stack: it generates a Central Composite Design (CCD) matrix, "
        "logs results to a mock LIMS database, and fits dual modeling algorithms: classical Response Surface Methodology (OLS-RSM) "
        "and modern Random Forest Machine Learning. Visual analysis, ingredient sensitivities, and NLP agent queries are run from the Streamlit app.",
        body_style
    ))
    
    story.append(Paragraph("2. System Architecture & Components", h1_style))
    
    table_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Role in Digital R&D</b>", body_style)],
        [Paragraph("LIMS database", body_style), Paragraph("SQLite (Normalized)", body_style), Paragraph("Simulates laboratory notebook logs of formulation runs.", body_style)],
        [Paragraph("DOE Matrix", body_style), Paragraph("pyDOE2 (CCD)", body_style), Paragraph("Generates 20 balanced runs (factorial, axial, center reps).", body_style)],
        [Paragraph("Dual Solver", body_style), Paragraph("statsmodels & Sklearn", body_style), Paragraph("Fits quadratic polynomials and RF models side-by-side.", body_style)],
        [Paragraph("Interactive UI", body_style), Paragraph("Streamlit & Plotly", body_style), Paragraph("3D factor spaces, sensitivity line charts, and chat agents.", body_style)]
    ]
    t = Table(table_data, colWidths=[1.5 * inch, 1.75 * inch, 3.75 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), border_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ------------------ PAGE 3: ML MODEL & SIMULATION ------------------
    story.append(Paragraph("3. Classical Response Surface Methodology (RSM)", h1_style))
    story.append(Paragraph(
        "Response Surface Methodology is a statistical method used to fit a second-order quadratic polynomial to the experimental data. "
        "This polynomial models interaction terms and squared curvature effects:",
        body_style
    ))
    story.append(Paragraph("• <b>Linear features:</b> SLES, CAPB, NaCl.", bullet_style))
    story.append(Paragraph("• <b>Interaction features:</b> SLES_CAPB, SLES_NaCl, CAPB_NaCl.", bullet_style))
    story.append(Paragraph("• <b>Quadratic features:</b> SLES_sq, CAPB_sq, NaCl_sq.", bullet_style))
    
    story.append(Paragraph("Quadratic Polynomial Fitting Snippet (src/models/dual_modeling.py)", h2_style))
    story.append(Paragraph(
        "df_poly = X.copy()<br/>"
        "df_poly['SLES_CAPB'] = X['SLES_pct'] * X['CAPB_pct']<br/>"
        "df_poly['SLES_sq'] = X['SLES_pct'] ** 2<br/>"
        "df_poly = sm.add_constant(df_poly)<br/>"
        "rsm_model = sm.OLS(y, df_poly).fit()",
        code_style
    ))
    
    story.append(Paragraph("4. Machine Learning & Random Forest Comparison", h1_style))
    story.append(Paragraph(
        "For comparison, the system fits a RandomForestRegressor using 5-fold cross-validation. "
        "On small, smooth datasets like standard CCD designs ($N=20$), classical RSM OLS regression generally outperforms "
        "Random Forest in cross-validation R² metrics because trees cannot model smooth curvature with limited data. "
        "This comparison is a core differentiator for R&D Data Scientists.",
        body_style
    ))
    story.append(PageBreak())
    
    # ------------------ PAGE 4: LIMS & AGENT ------------------
    story.append(Paragraph("5. LIMS & ELN Data Integration", h1_style))
    story.append(Paragraph(
        "The mock LIMS system uses a flat table representing lab records: batch_id, run_number, operator, "
        "SLES_pct, CAPB_pct, NaCl_pct, water_pct, viscosity_sec, foam_height_initial_mm, foam_height_5min_mm, ph, clarity_score, replicate_flag.",
        body_style
    ))
    
    story.append(Paragraph("6. AI Agent Prompt routing & LIMS querying", h1_style))
    story.append(Paragraph(
        "The NLP Lab Copilot parses researcher prompts using regex mapping to route actions:",
        body_style
    ))
    story.append(Paragraph("• <b>LIMS query:</b> translating queries like <i>'Show trials by Madhura'</i> into SQL matching the operator name.", bullet_style))
    story.append(Paragraph("• <b>Predict properties:</b> running OLS-RSM models for user-input ingredient ratios.", bullet_style))
    story.append(Paragraph("• <b>Optimized design:</b> solving the formulation by search metrics given target viscosity and pH.", bullet_style))
    
    story.append(Paragraph("Agent Routing Code Structure (src/agent/lab_copilot.py)", h2_style))
    story.append(Paragraph(
        "if 'design' in p or 'optimize' in p:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;best_in, best_out = self.engine.optimize_formulation(target_visc, target_ph)<br/>"
        "elif 'predict' in p or 'simulate' in p:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;outputs = self.engine.predict('RSM', inputs)<br/>"
        "else:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;columns, results = run_custom_query(query, params)",
        code_style
    ))
    
    story.append(PageBreak())
    
    # New Section 7: Pareto Optimization
    story.append(Paragraph("7. Multi-Objective Cost-Performance Optimization", h1_style))
    story.append(Paragraph(
        "A central challenge in FMCG formulation is balancing performance (e.g. initial foam height) "
        "with the raw material unit costs of ingredients (SLES = 0.12 INR/g, CAPB = 0.15 INR/g, NaCl = 0.02 INR/g). "
        "This system implements a constrained cost optimization algorithm to minimize cost while satisfying physical specs.",
        body_style
    ))
    
    story.append(Paragraph("Differential Evolution Solver", h2_style))
    story.append(Paragraph(
        "Using scipy.optimize.differential_evolution, the system searches the design space boundary for the "
        "lowest-cost formulation. Non-linear constraints (viscosity, pH, foam) are enforced using a penalty function:",
        body_style
    ))
    
    story.append(Paragraph(
        "def penalty_objective(factors):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;sles, capb, nacl = factors<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;cost = (sles * 0.12) + (capb * 0.15) + (nacl * 0.02)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;preds = self.engine.predict('RSM', inputs)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;penalty = 0.0<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;if preds['viscosity_sec'] < min_visc: penalty += (preds['viscosity_sec'] - min_visc)**2 * 50<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;if preds['ph'] < min_ph or preds['ph'] > max_ph: penalty += (preds['ph'] - target_ph)**2 * 1000<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;return cost + penalty",
        code_style
    ))
    
    story.append(Paragraph("Pareto Front Analysis", h2_style))
    story.append(Paragraph(
        "By varying the target foam height constraint using the epsilon-constraint method, the solver generates "
        "a Pareto Front curve of Cost vs. Performance. This allows R&D managers to select a formulation choice "
        "based on target tierings (Budget, Balanced, or Premium Performance), making technical trade-offs clear to business stakeholders.",
        body_style
    ))
    
    doc.build(story, onFirstPage=draw_cover_page, onLaterPages=draw_header_footer)
    print(f"PDF Successfully compiled: {filename}")

if __name__ == "__main__":
    create_pdf()
