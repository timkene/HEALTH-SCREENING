import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

def create_title(company_name):
    """Creates the title for the report"""
    elements = []
    
    # Try to add company logo
    try:
        logo_path = "Clearline.png"
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=200, height=100)
            elements.append(logo)
            elements.append(Spacer(1, 20))
    except:
        pass  # Skip logo if not found
    
    elements.extend([
        Paragraph(f"{company_name} HEALTH SCREENING REPORT", 
                 ParagraphStyle('Title', 
                              parent=getSampleStyleSheet()['Title'],
                              fontSize=24,
                              spaceAfter=30)),
        Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
                 ParagraphStyle('Subtitle',
                              parent=getSampleStyleSheet()['Normal'],
                              fontSize=12,
                              spaceAfter=30))
    ])
    
    return elements

def create_introduction(company_name, results):
    """Creates the introduction section of the report"""
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph("INTRODUCTION", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Create the list of screening tests dynamically based on available data
    screening_tests = []
    if results.get('has_bp', False):
        screening_tests.append("• Blood pressure monitoring")
    if results.get('has_glucose', False):
        screening_tests.append("• Random blood sugar test / fasting blood sugar")
    if results.get('has_bmi', False):
        screening_tests.append("• Measurement of weight and height to calculate Body Mass Index (BMI)")
    if results.get('has_cholesterol', False):
        screening_tests.append("• Total Cholesterol screening")
    if results.get('has_urine', False):
        screening_tests.append("• Urinalysis for glucose and protein")
    
    intro_text = f"""
    At Clearline HMO, healthcare is not just about treating you when you are ill, it is also about 
    managing health conditions and maintaining a healthy lifestyle. We help you manage your 
    medical condition by teaming up with your doctor to put you on the path to good health. 
    {company_name} has taken a proactive step in ensuring the wellbeing of its staff
    through this comprehensive health screening program.
    
    The health program organized by {company_name} for its employees is very 
    commendable because it gives the opportunity to detect life threatening diseases, which can have 
    serious long-term consequences. It also provides the company with statistical evidence of the 
    health status and indices of the staff, with a view to positively affecting the planning and policy 
    formulations concerning health and other human capital issues.  
    
    The screening tests comprised of:
    {chr(10).join(screening_tests)}
    
    The health screening exercise was carried out at designated centers as instructed by the company. 
    All results were read and explained immediately through written report forms made 
    available on-the-spot.
    """
    
    elements.append(Paragraph(intro_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_pie_chart(data, title, width=400, height=200):
    """Creates a pie chart for the given data"""
    d = Drawing(width, height)
    pc = Pie()
    pc.x = 50
    pc.y = 50
    pc.width = width - 100
    pc.height = height - 100
    
    # Convert data to the format expected by Pie
    pc.data = [float(v) for v in data.values()]
    pc.labels = list(data.keys())
    pc.slices.strokeWidth = 0.5
    pc.slices.strokeColor = colors.black
    
    # Set different colors for different categories
    colors_list = [colors.lightblue, colors.lightgreen, colors.orange, colors.pink, colors.yellow, colors.lightcoral]
    for i, label in enumerate(pc.labels):
        pc.slices[i].fillColor = colors_list[i % len(colors_list)]
    
    d.add(pc)
    return d

def create_bar_chart(data, title, width=400, height=200):
    """Creates a bar chart for the given data"""
    d = Drawing(width, height)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.width = width - 100
    bc.height = height - 100
    
    # Convert data to the format expected by VerticalBarChart
    data_values = [[float(v) for v in data.values()]]
    bc.data = data_values
    bc.categoryAxis.categoryNames = list(data.keys())
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(data.values()) * 1.2 if data.values() else 1
    bc.bars.strokeWidth = 0.5
    bc.bars.strokeColor = colors.black
    bc.bars.fillColor = colors.lightblue
    d.add(bc)
    return d

def create_summary_section(results):
    """Creates the summary section of the report"""
    styles = getSampleStyleSheet()
    elements = []
    
    # Add section title
    elements.append(Paragraph("EXECUTIVE SUMMARY", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Add total staff count
    elements.append(Paragraph(f"Total Number of Staff: {results['total_staff']}", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Create the list of health metrics dynamically
    health_metrics = []
    if results.get('has_bp', False):
        health_metrics.append("blood pressure")
    if results.get('has_glucose', False):
        health_metrics.append("blood sugar")
    if results.get('has_bmi', False):
        health_metrics.append("BMI")
    if results.get('has_cholesterol', False):
        health_metrics.append("cholesterol")
    if results.get('has_urine', False):
        health_metrics.append("urine analysis")
    
    elements.append(Paragraph(
        f"This health screening report provides a comprehensive analysis of the health status of {results['total_staff']} employees at {results['company_name']}. "
        f"The report covers various health metrics including {', '.join(health_metrics)}. "
        "Each section includes detailed analysis, recommendations, and visual representations of the data.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Add gender distribution table
    elements.append(Paragraph("Gender Distribution", styles['Heading2']))
    gender_data = [['Gender', 'Number of Staff', '% of Total']]
    gender_dist = results['gender_distribution']
    for i in range(len(gender_dist['GENDER'])):
        gender_data.append([
            gender_dist['GENDER'][i],
            gender_dist['NO OF STAFF'][i],
            f"{gender_dist['%OF TOTAL'][i]}%"
        ])
    
    gender_table = Table(gender_data)
    gender_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(gender_table)
    elements.append(Spacer(1, 12))
    
    # Add gender distribution pie chart
    gender_pie_data = {gender_dist['GENDER'][i]: gender_dist['NO OF STAFF'][i] 
                      for i in range(len(gender_dist['GENDER']))}
    elements.append(create_pie_chart(gender_pie_data, "Gender Distribution"))
    elements.append(Spacer(1, 20))
    
    return elements

def create_health_metrics_section(results):
    """Creates the health metrics section of the report"""
    styles = getSampleStyleSheet()
    elements = []
    
    # Add section title
    elements.append(Paragraph("DETAILED HEALTH METRICS ANALYSIS", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Blood Pressure Analysis
    if results.get('has_bp') and results.get('blood_pressure'):
        elements.extend(create_blood_pressure_section(results, styles))
    
    # Blood Sugar Analysis
    if results.get('has_glucose') and results.get('blood_sugar'):
        elements.extend(create_blood_sugar_section(results, styles))
    
    # Cholesterol Analysis (only if data is available)
    if results.get('has_cholesterol', False) and results.get('cholesterol'):
        elements.extend(create_cholesterol_section(results, styles))
    
    # BMI Analysis
    if results.get('has_bmi') and results.get('bmi'):
        elements.extend(create_bmi_section(results, styles))
    
    # Urine Analysis (only if data is available)
    if results.get('has_urine', False) and results.get('urine'):
        elements.extend(create_urine_section(results, styles))
    
    return elements

def create_blood_pressure_section(results, styles):
    """Creates the blood pressure analysis section"""
    elements = []
    
    elements.append(Paragraph("Blood Pressure Analysis", styles['Heading2']))
    elements.append(Paragraph(
        "Blood pressure is a critical indicator of cardiovascular health. The analysis below shows the distribution of blood pressure categories among employees based on current medical guidelines.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    bp_data = [['Category', 'Number of Staff', '% of Total']]
    for category, count in results['blood_pressure']['distribution'].items():
        bp_data.append([
            category,
            count,
            f"{results['blood_pressure']['distribution_pct'][category]}%"
        ])
    
    bp_table = Table(bp_data)
    bp_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(bp_table)
    
    # Add blood pressure distribution bar chart
    bp_bar_data = {k: v for k, v in results['blood_pressure']['distribution'].items()}
    elements.append(create_bar_chart(bp_bar_data, "Blood Pressure Distribution"))
    elements.append(Spacer(1, 12))
    
    # Add analysis and recommendations
    normal_pct = results['blood_pressure']['distribution_pct'].get('NORMAL', 0)
    elevated_pct = results['blood_pressure']['distribution_pct'].get('ELEVATED', 0)
    high_pct = results['blood_pressure']['distribution_pct'].get('HIGH', 0) + results['blood_pressure']['distribution_pct'].get('MODERATE HIGH', 0) + results['blood_pressure']['distribution_pct'].get('SEVERE HIGH', 0)
    
    elements.append(Paragraph("Analysis and Recommendations:", styles['Heading3']))
    elements.append(Paragraph(
        f"• {normal_pct}% of employees have normal blood pressure levels, which is encouraging.\n"
        f"• {elevated_pct}% of employees have elevated blood pressure.\n"
        f"• {high_pct}% of employees have high blood pressure levels requiring attention.\n"
        "• Recommendations:\n"
        "  - Implement workplace wellness programs focusing on stress management\n"
        "  - Encourage regular physical activity through company-sponsored fitness initiatives\n"
        "  - Provide healthy eating options in the workplace\n"
        "  - Consider offering blood pressure monitoring stations\n"
        "  - Organize educational sessions on hypertension management",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    
    return elements

def create_blood_sugar_section(results, styles):
    """Creates the blood sugar analysis section"""
    elements = []
    
    elements.append(Paragraph("Blood Sugar Analysis", styles['Heading2']))
    elements.append(Paragraph(
        "Blood sugar levels are crucial indicators of metabolic health and diabetes risk. The following analysis shows the distribution of blood sugar categories based on current medical guidelines.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    bs_data = [['Category', 'Number of Staff', '% of Total']]
    for category, count in results['blood_sugar']['distribution'].items():
        bs_data.append([
            category,
            count,
            f"{results['blood_sugar']['distribution_pct'][category]}%"
        ])
    
    bs_table = Table(bs_data)
    bs_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(bs_table)
    
    # Add blood sugar distribution bar chart
    bs_bar_data = {k: v for k, v in results['blood_sugar']['distribution'].items()}
    elements.append(create_bar_chart(bs_bar_data, "Blood Sugar Distribution"))
    elements.append(Spacer(1, 12))
    
    # Add analysis and recommendations
    normal_pct = results['blood_sugar']['distribution_pct'].get('NORMAL', 0)
    prediabetic_pct = results['blood_sugar']['distribution_pct'].get('PRE_DIABETIC', 0)
    diabetic_pct = results['blood_sugar']['distribution_pct'].get('DIABETIC', 0) + results['blood_sugar']['distribution_pct'].get('PROBABLE DIABETIC', 0)
    
    elements.append(Paragraph("Analysis and Recommendations:", styles['Heading3']))
    elements.append(Paragraph(
        f"• {normal_pct}% of employees have normal blood sugar levels.\n"
        f"• {prediabetic_pct}% of employees are in the pre-diabetic range.\n"
        f"• {diabetic_pct}% of employees show diabetic range readings.\n"
        "• Recommendations:\n"
        "  - Implement diabetes prevention programs\n"
        "  - Provide healthy snack options in the workplace\n"
        "  - Organize educational sessions on blood sugar management\n"
        "  - Encourage regular physical activity\n"
        "  - Consider offering regular blood sugar screening programs",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    
    return elements

def create_cholesterol_section(results, styles):
    """Creates the cholesterol analysis section"""
    elements = []
    
    elements.append(Paragraph("Cholesterol Analysis", styles['Heading2']))
    elements.append(Paragraph(
        "Total cholesterol levels are important indicators of cardiovascular disease risk. The following analysis shows the distribution of cholesterol categories based on established medical guidelines.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    chol_data = [['Category', 'Number of Staff', '% of Total']]
    for category, count in results['cholesterol']['distribution'].items():
        chol_data.append([
            category,
            count,
            f"{results['cholesterol']['distribution_pct'][category]}%"
        ])
    
    chol_table = Table(chol_data)
    chol_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(chol_table)
    
    # Add cholesterol distribution bar chart
    chol_bar_data = {k: v for k, v in results['cholesterol']['distribution'].items()}
    elements.append(create_bar_chart(chol_bar_data, "Cholesterol Distribution"))
    elements.append(Spacer(1, 12))
    
    # Add average cholesterol by gender if available
    if 'avg_by_gender' in results['cholesterol']:
        elements.append(Paragraph("Average Cholesterol by Gender:", styles['Heading3']))
        avg_chol_data = [['Gender', 'Average Cholesterol (mg/dL)']]
        for gender, avg_chol in results['cholesterol']['avg_by_gender'].items():
            avg_chol_data.append([gender, f"{avg_chol}"])
        
        avg_chol_table = Table(avg_chol_data)
        avg_chol_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(avg_chol_table)
        elements.append(Spacer(1, 12))
    
    # Add analysis and recommendations
    normal_pct = results['cholesterol']['distribution_pct'].get('NORMAL', 0)
    borderline_pct = results['cholesterol']['distribution_pct'].get('BORDERLINE HIGH', 0)
    high_pct = results['cholesterol']['distribution_pct'].get('HIGH', 0) + results['cholesterol']['distribution_pct'].get('VERY HIGH', 0)
    
    elements.append(Paragraph("Analysis and Recommendations:", styles['Heading3']))
    elements.append(Paragraph(
        f"• {normal_pct}% of employees have optimal cholesterol levels.\n"
        f"• {borderline_pct}% of employees have borderline high cholesterol.\n"
        f"• {high_pct}% of employees have high cholesterol levels requiring intervention.\n"
        "• Recommendations:\n"
        "  - Implement dietary counseling programs focusing on heart-healthy nutrition\n"
        "  - Encourage regular physical activity to improve cholesterol profiles\n"
        "  - Provide educational sessions on cholesterol management\n"
        "  - Consider partnering with nutritionists for personalized meal planning\n"
        "  - Offer regular cholesterol screening and monitoring",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    
    return elements

def create_bmi_section(results, styles):
    """Creates the BMI analysis section"""
    elements = []
    
    elements.append(Paragraph("Body Mass Index (BMI) Analysis", styles['Heading2']))
    elements.append(Paragraph(
        "Body Mass Index (BMI) is a key indicator of weight-related health risks. The following analysis shows the distribution of BMI categories based on WHO guidelines.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    bmi_data = [['Category', 'Number of Staff', '% of Total']]
    for category, count in results['bmi']['distribution'].items():
        bmi_data.append([
            category,
            count,
            f"{results['bmi']['distribution_pct'][category]}%"
        ])
    
    bmi_table = Table(bmi_data)
    bmi_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(bmi_table)
    
    # Add BMI distribution bar chart
    bmi_bar_data = {k: v for k, v in results['bmi']['distribution'].items()}
    elements.append(create_bar_chart(bmi_bar_data, "BMI Distribution"))
    elements.append(Spacer(1, 12))
    
    # Add analysis and recommendations
    normal_pct = results['bmi']['distribution_pct'].get('NORMAL', 0)
    underweight_pct = results['bmi']['distribution_pct'].get('UNDERWEIGHT', 0)
    overweight_pct = results['bmi']['distribution_pct'].get('OVERWEIGHT', 0)
    obese_pct = results['bmi']['distribution_pct'].get('OBESITY', 0) + results['bmi']['distribution_pct'].get('SEVERE OBESITY', 0)
    
    elements.append(Paragraph("Analysis and Recommendations:", styles['Heading3']))
    elements.append(Paragraph(
        f"• {normal_pct}% of employees have a normal BMI.\n"
        f"• {underweight_pct}% of employees are underweight.\n"
        f"• {overweight_pct}% of employees are overweight.\n"
        f"• {obese_pct}% of employees are in the obesity range.\n"
        "• Recommendations:\n"
        "  - Implement comprehensive workplace wellness programs\n"
        "  - Provide nutrition counseling services\n"
        "  - Organize fitness challenges and group activities\n"
        "  - Offer healthy meal options in the workplace cafeteria\n"
        "  - Consider providing gym memberships or on-site fitness facilities",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    
    return elements

def create_urine_section(results, styles):
    """Creates the urine analysis section"""
    elements = []
    
    elements.append(Paragraph("Urine Analysis", styles['Heading2']))
    elements.append(Paragraph(
        "Urine analysis helps detect various health conditions including diabetes, kidney disease, and urinary tract infections. The analysis includes testing for glucose and protein in urine samples.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Glucose in urine analysis
    elements.append(Paragraph("Glucose in Urine:", styles['Heading3']))
    glucose_data = [['Result', 'Number of Staff', '% of Total']]
    if 'glucose' in results['urine']:
        for result, count in results['urine']['glucose']['distribution'].items():
            glucose_data.append([
                f"Glucose {result}",
                count,
                f"{results['urine']['glucose']['distribution_pct'][result]}%"
            ])
    
    glucose_table = Table(glucose_data)
    glucose_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(glucose_table)
    elements.append(Spacer(1, 12))
    
    # Protein in urine analysis
    elements.append(Paragraph("Protein in Urine:", styles['Heading3']))
    protein_data = [['Result', 'Number of Staff', '% of Total']]
    if 'protein' in results['urine']:
        for result, count in results['urine']['protein']['distribution'].items():
            protein_data.append([
                f"Protein {result}",
                count,
                f"{results['urine']['protein']['distribution_pct'][result]}%"
            ])
    
    protein_table = Table(protein_data)
    protein_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(protein_table)
    elements.append(Spacer(1, 12))
    
    # Add analysis and recommendations
    glucose_positive_pct = results['urine']['glucose']['distribution_pct'].get('POSITIVE', 0) if 'glucose' in results['urine'] else 0
    protein_positive_pct = results['urine']['protein']['distribution_pct'].get('POSITIVE', 0) if 'protein' in results['urine'] else 0
    
    elements.append(Paragraph("Analysis and Recommendations:", styles['Heading3']))
    elements.append(Paragraph(
        f"• {glucose_positive_pct}% of employees tested positive for glucose in urine, which may indicate diabetes or impaired glucose tolerance.\n"
        f"• {protein_positive_pct}% of employees tested positive for protein in urine, which may indicate kidney dysfunction or other health issues.\n"
        "• Recommendations:\n"
        "  - Employees with positive glucose should undergo further diabetes screening\n"
        "  - Employees with positive protein should be referred for kidney function evaluation\n"
        "  - Implement regular urine screening as part of routine health checks\n"
        "  - Provide educational sessions on kidney health and diabetes prevention\n"
        "  - Encourage adequate hydration and healthy lifestyle practices",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    
    return elements

def create_conclusion_section(results):
    """Creates the conclusion section of the report"""
    styles = getSampleStyleSheet()
    elements = []
    
    # Add section title
    elements.append(Paragraph("CONCLUSION", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Get actual data from results for a more accurate conclusion
    bp_normal = results['blood_pressure']['distribution_pct'].get('NORMAL', 0) if results.get('blood_pressure') else 0
    bp_elevated = results['blood_pressure']['distribution_pct'].get('ELEVATED', 0) if results.get('blood_pressure') else 0
    bp_high = (results['blood_pressure']['distribution_pct'].get('HIGH', 0) + 
               results['blood_pressure']['distribution_pct'].get('MODERATE HIGH', 0) + 
               results['blood_pressure']['distribution_pct'].get('SEVERE HIGH', 0)) if results.get('blood_pressure') else 0
    
    conclusion_text = f"""
    The comprehensive health screening exercise conducted for {results['company_name']} was highly successful and provided valuable insights into the health status of the workforce. This proactive approach to employee health management is commendable and demonstrates the company's commitment to employee wellbeing.
    
    Key findings from the screening include:
    
    Blood Pressure Analysis: {bp_normal:.1f}% of employees demonstrated normal blood pressure readings, while {bp_elevated:.1f}% showed elevated levels and {bp_high:.1f}% required immediate attention for hypertension management. Early detection of these cases allows for timely intervention and prevention of serious cardiovascular complications.
    """
    
    # Add cholesterol findings if available
    if results.get('has_cholesterol') and results.get('cholesterol'):
        chol_normal = results['cholesterol']['distribution_pct'].get('NORMAL', 0)
        chol_high = (results['cholesterol']['distribution_pct'].get('HIGH', 0) + 
                     results['cholesterol']['distribution_pct'].get('VERY HIGH', 0) +
                     results['cholesterol']['distribution_pct'].get('BORDERLINE HIGH', 0))
        conclusion_text += f"""
    
    Cholesterol Screening: {chol_normal:.1f}% of employees showed optimal cholesterol levels, while {chol_high:.1f}% demonstrated elevated levels requiring dietary and lifestyle interventions.
    """
    
    # Add urine analysis findings if available
    if results.get('has_urine') and results.get('urine'):
        glucose_positive = results['urine']['glucose']['distribution_pct'].get('POSITIVE', 0) if 'glucose' in results['urine'] else 0
        protein_positive = results['urine']['protein']['distribution_pct'].get('POSITIVE', 0) if 'protein' in results['urine'] else 0
        conclusion_text += f"""
    
    Urine Analysis: {glucose_positive:.1f}% of employees tested positive for glucose in urine and {protein_positive:.1f}% tested positive for protein, indicating the need for further evaluation and monitoring.
    """
    
    conclusion_text += """
    
    All employees with abnormal findings received immediate counseling and were provided with appropriate referrals to their primary healthcare providers for follow-up care. Educational materials and lifestyle modification recommendations were distributed to promote better health outcomes.
    
    The screening program successfully identified employees at risk for chronic diseases, enabling early intervention and prevention strategies. Regular monitoring and follow-up screenings are recommended to track progress and maintain optimal health status across the workforce.
    
    This health screening initiative serves as a foundation for ongoing workplace wellness programs and demonstrates the positive impact of preventive healthcare in the corporate environment.
    """
    
    elements.append(Paragraph(conclusion_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_recommendations_section(results):
    """Creates the recommended health actions section"""
    styles = getSampleStyleSheet()
    elements = []
    
    # Add section title
    elements.append(Paragraph("RECOMMENDED HEALTH ACTIONS", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Add introduction paragraph
    elements.append(Paragraph(f"Based on the comprehensive health screening results for {results['company_name']}, the following evidence-based recommendations are proposed to improve the overall health and wellbeing of the workforce:", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Immediate Actions
    elements.append(Paragraph("IMMEDIATE ACTIONS:", styles['Heading2']))
    elements.append(Paragraph("• Establish a workplace wellness committee to oversee health initiatives and monitor progress.", styles['Normal']))
    elements.append(Paragraph("• Implement regular health screening programs (quarterly blood pressure checks, annual comprehensive screenings).", styles['Normal']))
    elements.append(Paragraph("• Create a referral system for employees requiring immediate medical attention.", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Workplace Environment Modifications
    elements.append(Paragraph("WORKPLACE ENVIRONMENT MODIFICATIONS:", styles['Heading2']))
    elements.append(Paragraph("• Introduce healthy food options in cafeterias and vending machines, reducing processed and high-sodium foods.", styles['Normal']))
    elements.append(Paragraph("• Create designated spaces for physical activity and relaxation.", styles['Normal']))
    elements.append(Paragraph("• Implement ergonomic workstation assessments to reduce physical strain.", styles['Normal']))
    elements.append(Paragraph("• Establish smoke-free policies throughout all company premises.", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Employee Education and Engagement
    elements.append(Paragraph("EMPLOYEE EDUCATION AND ENGAGEMENT:", styles['Heading2']))
    elements.append(Paragraph("• Conduct monthly health education seminars covering topics such as hypertension management, diabetes prevention, and stress reduction.", styles['Normal']))
    elements.append(Paragraph("• Organize group fitness activities and walking clubs to promote physical activity.", styles['Normal']))
    elements.append(Paragraph("• Provide access to mental health resources and stress management programs.", styles['Normal']))
    elements.append(Paragraph("• Create health awareness campaigns using newsletters, posters, and digital platforms.", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Policy Recommendations
    elements.append(Paragraph("POLICY RECOMMENDATIONS:", styles['Heading2']))
    elements.append(Paragraph("• Implement flexible work arrangements to reduce stress and improve work-life balance.", styles['Normal']))
    elements.append(Paragraph("• Establish mandatory health breaks during long work periods.", styles['Normal']))
    elements.append(Paragraph("• Provide health insurance coverage that includes preventive care and wellness programs.", styles['Normal']))
    elements.append(Paragraph("• Create incentive programs for employees who participate in wellness activities.", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_intervention_section(results):
    """Creates the intervention strategies section"""
    styles = getSampleStyleSheet()
    elements = []
    
    # Add section title
    elements.append(Paragraph("INTERVENTION STRATEGIES", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Blood Pressure Management
    elements.append(Paragraph("HYPERTENSION MANAGEMENT PROGRAM", styles['Heading2']))
    elements.append(Paragraph(
        "Hypertension is a leading cause of cardiovascular disease and stroke. Effective management requires a multi-faceted approach combining lifestyle modifications, regular monitoring, and medical intervention when necessary.",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Implementation Strategy: Establish on-site blood pressure monitoring stations, provide educational materials on the DASH diet, organize stress management workshops, and create a referral system for employees requiring medication management. Our Chronic Disease Registry (CDR) program can provide ongoing support with dedicated healthcare professionals and medication supplies.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Diabetes Prevention and Management
    elements.append(Paragraph("DIABETES PREVENTION AND MANAGEMENT", styles['Heading2']))
    elements.append(Paragraph(
        "Early detection and management of diabetes and pre-diabetes can prevent serious complications including heart disease, stroke, kidney disease, and vision problems.",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Implementation Strategy: Implement regular blood glucose screening, provide nutrition counseling focusing on carbohydrate management, establish partnerships with certified diabetes educators, and create support groups for affected employees. The CDR program offers comprehensive diabetes management including regular monitoring and medication support.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Cholesterol Management (only if data is available)
    if results.get('has_cholesterol', False):
        elements.append(Paragraph("CHOLESTEROL MANAGEMENT PROGRAM", styles['Heading2']))
        elements.append(Paragraph(
            "Elevated cholesterol levels significantly increase the risk of heart disease and stroke. Every 1% reduction in cholesterol levels corresponds to a 2% reduction in heart disease risk.",
            styles['Normal']
        ))
        elements.append(Paragraph(
            "Implementation Strategy: Provide heart-healthy nutrition education, establish partnerships with registered dietitians, organize group fitness activities, and ensure access to lipid-lowering medications when indicated. Regular monitoring through our CDR program ensures optimal cholesterol management with dedicated medical support.",
            styles['Normal']
        ))
        elements.append(Spacer(1, 12))
    
    # Weight Management
    elements.append(Paragraph("COMPREHENSIVE WEIGHT MANAGEMENT", styles['Heading2']))
    elements.append(Paragraph(
        "Maintaining a healthy weight reduces the risk of developing multiple chronic conditions including diabetes, heart disease, stroke, and certain cancers. Weight management also improves energy levels, self-confidence, and overall quality of life.",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Implementation Strategy: Offer group weight loss programs, provide access to nutrition counseling, create workplace fitness challenges, establish walking groups, and provide healthy meal options. Consider partnerships with fitness centers and wellness apps to support employee engagement.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Nutritional Wellness
    elements.append(Paragraph("NUTRITIONAL WELLNESS PROGRAM", styles['Heading2']))
    elements.append(Paragraph(
        "Proper nutrition is fundamental to preventing chronic diseases and maintaining optimal health. A well-balanced diet supports immune function, energy levels, and mental wellbeing.",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Implementation Strategy: Transform workplace food environments by offering healthy options in cafeterias and vending machines, conduct nutrition education workshops, provide access to registered dietitians, and create educational materials on meal planning and healthy cooking techniques.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Physical Fitness
    elements.append(Paragraph("PHYSICAL FITNESS AND ACTIVITY PROMOTION", styles['Heading2']))
    elements.append(Paragraph(
        "Regular physical activity is one of the most effective interventions for preventing and managing chronic diseases. Exercise improves cardiovascular health, mental wellbeing, bone density, and helps maintain healthy weight.",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Implementation Strategy: Create on-site fitness facilities or partner with local gyms, organize group fitness classes, establish walking meetings and active commuting programs, provide fitness trackers or wellness apps, and create company-wide fitness challenges with incentives.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Stress Management
    elements.append(Paragraph("STRESS MANAGEMENT AND MENTAL WELLNESS", styles['Heading2']))
    elements.append(Paragraph(
        "Chronic stress contributes to numerous health problems including hypertension, heart disease, diabetes, depression, and weakened immune function. Effective stress management is crucial for overall health and workplace productivity.",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Implementation Strategy: Offer stress management workshops, provide access to employee assistance programs, create quiet spaces for relaxation and meditation, implement flexible work arrangements, and train managers to recognize and address workplace stressors.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Kidney Health (if urine analysis shows issues)
    if results.get('has_urine', False):
        elements.append(Paragraph("KIDNEY HEALTH MONITORING", styles['Heading2']))
        elements.append(Paragraph(
            "Early detection of kidney dysfunction through urine analysis allows for timely intervention to prevent progression to chronic kidney disease. Proteinuria and glucosuria require careful monitoring and management.",
            styles['Normal']
        ))
        elements.append(Paragraph(
            "Implementation Strategy: Establish regular urine screening protocols, provide education on kidney health and hydration, ensure appropriate follow-up for abnormal results, and coordinate with nephrologists for specialized care when needed.",
            styles['Normal']
        ))
        elements.append(Spacer(1, 12))
    
    # Overall Health Practices
    elements.append(Paragraph("PROMOTING OVERALL HEALTHY LIFESTYLE PRACTICES", styles['Heading2']))
    elements.append(Paragraph("The following evidence-based practices should be actively promoted throughout the organization:", styles['Normal']))
    elements.append(Paragraph("• Complete tobacco cessation with access to smoking cessation programs and resources", styles['Normal']))
    elements.append(Paragraph("• Daily consumption of a nutritious breakfast to maintain stable blood sugar and energy levels", styles['Normal']))
    elements.append(Paragraph("• Regular physical activity with a minimum of 150 minutes of moderate exercise per week", styles['Normal']))
    elements.append(Paragraph("• Maintenance of healthy body weight through balanced nutrition and regular activity", styles['Normal']))
    elements.append(Paragraph("• Moderate alcohol consumption or complete abstinence as appropriate", styles['Normal']))
    elements.append(Paragraph("• Adequate sleep duration of 7-9 hours per night for optimal health and cognitive function", styles['Normal']))
    elements.append(Paragraph("• Healthy snacking choices emphasizing fruits, vegetables, and whole grains", styles['Normal']))
    elements.append(Paragraph("• Regular preventive healthcare visits and health screenings", styles['Normal']))
    elements.append(Paragraph("• Effective stress management through various techniques and social support", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def generate_report(results, output_path):
    """
    Generates a comprehensive PDF report using the analysis results
    
    Parameters:
    results (dict): Analysis results from analyze_staff_data
    output_path (str): Path where the PDF report should be saved
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create the story (content) for the PDF
    story = []
    
    # Add title and introduction
    story.extend(create_title(results['company_name']))
    story.extend(create_introduction(results['company_name'], results))
    
    # Add page break before main content
    story.append(PageBreak())
    
    # Add summary section
    story.extend(create_summary_section(results))
    
    # Add page break before detailed analysis
    story.append(PageBreak())
    
    # Add detailed health metrics section
    story.extend(create_health_metrics_section(results))
    
    # Add page break before conclusion
    story.append(PageBreak())
    
    # Add conclusion section
    story.extend(create_conclusion_section(results))
    
    # Add recommendations section
    story.extend(create_recommendations_section(results))
    
    # Add page break before interventions
    story.append(PageBreak())
    
    # Add intervention strategies section
    story.extend(create_intervention_section(results))
    
    # Build the PDF
    try:
        doc.build(story)
        print(f"Report successfully generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating report: {e}")
        raise e

if __name__ == "__main__":
    # Test the report generator
    from HEALTH_SCREEN import analyze_staff_data
    
    file_path = 'VACCIPHARM.xlsx'
    company_name = 'VACCIPHARM LIMITED'
    output_path = f"{company_name.replace(' ', '_')}_Health_Screening_Report.pdf"
    
    try:
        results = analyze_staff_data(file_path, company_name)
        report_path = generate_report(results, output_path)
        print(f"Report generated successfully at: {report_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()