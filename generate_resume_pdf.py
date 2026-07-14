import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def draw_accent_border(canvas, doc):
    canvas.saveState()
    # Draw a nice thin emerald border at the top
    canvas.setFillColor(colors.HexColor('#10B981')) # Emerald green
    canvas.rect(0, 11 * inch - 6, 8.5 * inch, 6, fill=True, stroke=False)
    canvas.restoreState()

def create_resume_pdf(filename="Madhura_Joshi_Resume_Reference_RD.pdf"):
    # 0.5 in margins (36 pt) for tight 1-page fit
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#0F172A') # Slate
    accent_color = colors.HexColor('#059669')  # Deep Emerald
    text_color = colors.HexColor('#334155')    # Charcoal
    
    # Typography Styles
    name_style = ParagraphStyle(
        'ResumeName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=2,
        alignment=1 # Centered
    )
    
    contact_style = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=text_color,
        spaceAfter=10,
        alignment=1 # Centered
    )
    
    section_h_style = ParagraphStyle(
        'ResumeSecHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=accent_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    item_header_style = ParagraphStyle(
        'ResumeItemHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=primary_color,
        keepWithNext=True
    )
    
    item_right_style = ParagraphStyle(
        'ResumeItemRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=primary_color,
        alignment=2 # Right aligned
    )
    
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=text_color,
        spaceAfter=4
    )
    
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    story = []
    
    # ------------------ HEADER ------------------
    story.append(Paragraph("MADHURA JOSHI", name_style))
    story.append(Paragraph(
        "Mumbai, India &nbsp;|&nbsp; email@yourdomain.com &nbsp;|&nbsp; +91-XXXXXXXXXX &nbsp;|&nbsp; "
        "<font color='#0284C7'>linkedin.com/in/madhurajoshi</font> &nbsp;|&nbsp; "
        "<font color='#0284C7'>github.com/Madhurajoshi0704</font>",
        contact_style
    ))
    
    # Divider helper function
    def add_section_header(title):
        story.append(Paragraph(title.upper(), section_h_style))
        # Draw a horizontal line under the heading
        line_data = [[""]]
        line_table = Table(line_data, colWidths=[7.5 * inch])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1, accent_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 4))

    # ------------------ EDUCATION ------------------
    add_section_header("Education")
    
    edu_data = [
        [
            Paragraph("<b>B.Tech, Chemical Engineering</b> | Indian Institute of Technology (IIT), Madras", item_header_style),
            Paragraph("<b>CGPA: 7.87/10</b> | 2024 - 2028*", item_right_style)
        ]
    ]
    edu_table = Table(edu_data, colWidths=[5.5 * inch, 2.0 * inch])
    edu_table.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(edu_table)
    
    story.append(Paragraph("• <b>Academic achievements:</b> Secured **99.63 percentile** in JEE-Mains 2024 (AIR 5950); Placed in the top tier of JEE Advanced (AIR 9060) out of 1.5L+ candidates.", bullet_style))
    story.append(Paragraph("• <b>Relevant Coursework:</b> Programming and Data Structures in Python, Machine Learning Foundations, Computational Techniques, Probability & Statistics, Kinetics & Catalysis, Chemical Engineering Thermodynamics.", bullet_style))
    
    # ------------------ TECHNICAL SKILLS ------------------
    add_section_header("Technical Skills")
    
    skills_data = [
        [Paragraph("<b>Programming Languages:</b>", body_style), Paragraph("Python (Expert), SQL, MATLAB, JavaScript, Java", body_style)],
        [Paragraph("<b>Libraries & Frameworks:</b>", body_style), Paragraph("PySpark, Scikit-Learn, Pandas, NumPy, Plotly, PyTorch, Matplotlib, Seaborn", body_style)],
        [Paragraph("<b>Tools & Enterprise Systems:</b>", body_style), Paragraph("Streamlit, SQLite (LIMS Simulator), Git, GitHub, Microsoft Excel, Power BI", body_style)],
        [Paragraph("<b>Core Competencies:</b>", body_style), Paragraph("Formulation Science Modeling, Property Simulation, AI Agent Workflows, Process Mapping, Multi-Output Regression", body_style)]
    ]
    skills_table = Table(skills_data, colWidths=[1.8 * inch, 5.7 * inch])
    skills_table.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 4))

    # ------------------ PROFESSIONAL EXPERIENCE ------------------
    add_section_header("Professional Experience")
    
    exp_data = [
        [
            Paragraph("<b>Machine Learning Intern</b> | [Company / Research Lab]", item_header_style),
            Paragraph("May 2025 - June 2025", item_right_style)
        ]
    ]
    exp_table = Table(exp_data, colWidths=[5.5 * inch, 2.0 * inch])
    exp_table.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(exp_table)
    story.append(Paragraph("• <b>R&D Data Pipelines:</b> Designed Python data pipelines to clean, preprocess, and structure experimental measurements, streamlining exploratory data analysis (EDA) for new formulations.", bullet_style))
    story.append(Paragraph("• <b>Predictive Modeling:</b> Trained and evaluated predictive machine learning models in Scikit-Learn to reduce physical lab trial-and-error cycles.", bullet_style))
    story.append(Paragraph("• <b>Data Storytelling:</b> Visualized multi-variable experimental correlations and key physical trends, communicating findings to senior R&D team leads.", bullet_style))
    
    story.append(Spacer(1, 4))
    
    exp_data2 = [
        [
            Paragraph("<b>Co-Founder & Business Lead</b> | #DotConnect (DotEco Founding Circle)", item_header_style),
            Paragraph("Dec 2025 - Present", item_right_style)
        ]
    ]
    exp_table2 = Table(exp_data2, colWidths=[5.5 * inch, 2.0 * inch])
    exp_table2.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(exp_table2)
    story.append(Paragraph("• <b>Process Mapping:</b> Mapped business workflows and established key performance indicators (KPIs) to track user growth metrics.", bullet_style))
    story.append(Paragraph("• <b>Visual Analytics:</b> Built interactive business performance tracking dashboards, supporting executive decision-making.", bullet_style))

    # ------------------ TECHNICAL PROJECTS ------------------
    add_section_header("Technical Projects")
    
    proj_data1 = [
        [
            Paragraph("<b>FormuAI: Formulation Optimizer & Digital Lab Agent (FMCG R&D)</b>", item_header_style),
            Paragraph("June 2026", item_right_style)
        ]
    ]
    proj_table1 = Table(proj_data1, colWidths=[5.5 * inch, 2.0 * inch])
    proj_table1.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 0)]))
    story.append(proj_table1)
    story.append(Paragraph("• <b>Formulation Modeling:</b> Trained a multi-output RandomForestRegressor model on synthetic ingredient ratios (surfactants, co-surfactants, thickeners, actives) to predict critical shampoo properties (viscosity, pH, foam volume, stability), reducing trial-and-error cycles from days to &lt; 10ms.", bullet_style))
    story.append(Paragraph("• <b>AI Lab Copilot Agent:</b> Developed an NLP search and optimization agent that translates chemist instructions (e.g. <i>'Show experiments with stability &gt; 300 days'</i>) into SQLite SQL commands or simulation parameters.", bullet_style))
    story.append(Paragraph("• <b>LIMS & BI Integration:</b> Set up a relational SQLite database simulating LIMS/ELN records and built an interactive Streamlit dashboard mapping ingredient correlations, mimicking enterprise Power BI reports.", bullet_style))
    
    story.append(Spacer(1, 4))
    
    proj_data_lf = [
        [
            Paragraph("<b>LumiFoam: Computer Vision Foam & Emulsion Analyzer</b>", item_header_style),
            Paragraph("May 2026", item_right_style)
        ]
    ]
    proj_table_lf = Table(proj_data_lf, colWidths=[5.5 * inch, 2.0 * inch])
    proj_table_lf.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 0)]))
    story.append(proj_table_lf)
    story.append(Paragraph("• <b>Computer Vision Pipeline:</b> Built OpenCV image processing pipelines using Hough Circle Transforms to automate droplet size measurements of surfactant emulsions.", bullet_style))
    story.append(Paragraph("• <b>Decay Curve Fitting:</b> Applied SciPy exponential curve-fitting models to calculate shampoo foam volume decay half-life, automating physical lab measurements.", bullet_style))
    
    story.append(Spacer(1, 4))
    
    proj_data2 = [
        [
            Paragraph("<b>Adsorption Modeling in Porous Solids & Heterogeneous Systems</b>", item_header_style),
            Paragraph("May 2026", item_right_style)
        ]
    ]
    proj_table2 = Table(proj_data2, colWidths=[5.5 * inch, 2.0 * inch])
    proj_table2.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 0)]))
    story.append(proj_table2)
    story.append(Paragraph("• <b>Numerical Solvers:</b> Formulated a MATLAB mathematical model solving coupled partial differential equations (PDEs) for mass and energy transport in heterogeneous catalyst pellets.", bullet_style))
    story.append(Paragraph("• <b>Optimization:</b> Analyzed internal reactant distributions and Thiele modulus across complex geometries to prevent starvation regimes.", bullet_style))

    # ------------------ POSITIONS OF RESPONSIBILITY ------------------
    add_section_header("Positions of Responsibility")
    
    por_data = [
        [
            Paragraph("<b>Club Head - Fine Arts</b> | Sangam, IIT Madras", item_header_style),
            Paragraph("May 2025 - June 2026", item_right_style)
        ]
    ]
    por_table = Table(por_data, colWidths=[5.5 * inch, 2.0 * inch])
    por_table.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 0)]))
    story.append(por_table)
    story.append(Paragraph("• <b>Cross-Functional Leadership:</b> Governed financial budgeting and led a multi-tiered team of 9 coordinators and a 35-member contingent.", bullet_style))
    story.append(Paragraph("• <b>Process & Documentation:</b> Drafted operational blueprint reports and financial decks, coordinating event marketing campaigns that increased engagement by <b>20%</b>.", bullet_style))
    
    doc.build(story, onFirstPage=draw_accent_border, onLaterPages=draw_accent_border)
    print(f"PDF Successfully compiled: {filename}")

if __name__ == "__main__":
    create_resume_pdf()
