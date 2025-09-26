import os
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor

def create_individual_title(individual_data):
    """Creates the personalized title for the individual report"""
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
    
    # Individual name and ID header
    name = individual_data.get('NAME', 'Unknown')
    enrollee_id = individual_data.get('ENROLLEE ID', 'Unknown')
    
    elements.extend([
        Paragraph(f"<b>{name}</b>", 
                 ParagraphStyle('IndividualName', 
                              parent=getSampleStyleSheet()['Title'],
                              fontSize=28,
                              alignment=1,  # Center alignment
                              spaceAfter=10)),
        Paragraph(f"<b>Enrollee ID: {enrollee_id}</b>", 
                 ParagraphStyle('EnrolleeID',
                              parent=getSampleStyleSheet()['Title'],
                              fontSize=18,
                              alignment=1,  # Center alignment
                              spaceAfter=30)),
        Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
                 ParagraphStyle('Subtitle',
                              parent=getSampleStyleSheet()['Normal'],
                              fontSize=12,
                              alignment=1,  # Center alignment
                              spaceAfter=30))
    ])
    
    return elements

def create_individual_introduction(individual_data):
    """Creates the personalized introduction section"""
    styles = getSampleStyleSheet()
    elements = []
    
    name = individual_data.get('NAME', 'Valued Employee')
    
    intro_text = f"""
    <b>Hello {name}! I'm your friendly health bot Klaire, here to walk you through your checkup results. Let's dive in!</b><br/><br/>
    
    This is your personalized health report based on the medical screening we conducted at your company. 
    I've analyzed all your test results and I'm excited to share what I found! Don't worry if anything seems confusing - 
    I'm here to explain everything in simple terms and help you understand what your numbers mean for your health.<br/><br/>
    
    If you have any questions after reading through your results, don't hesitate to reach out to our doctors on 
    WhatsApp <b>08076490056</b> for telemedicine consultation - they're always happy to help!
    """
    
    elements.append(Paragraph(intro_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def add_health_overview_visual(analysis):
    """Adds a health overview visual to the report"""
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("YOUR HEALTH OVERVIEW", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    return elements

def create_heart_icon(x, y, size, color):
    """Creates a heart icon"""
    d = Drawing(size, size)
    
    # Heart shape using circles and triangle
    # Left lobe
    left_circle = Circle(x - size/6, y + size/8, size/4)
    left_circle.fillColor = color
    left_circle.strokeColor = colors.black
    left_circle.strokeWidth = 1
    d.add(left_circle)
    
    # Right lobe
    right_circle = Circle(x + size/6, y + size/8, size/4)
    right_circle.fillColor = color
    right_circle.strokeColor = colors.black
    right_circle.strokeWidth = 1
    d.add(right_circle)
    
    # Heart point (triangle) - using three separate lines to form triangle
    from reportlab.graphics.shapes import Line
    # Bottom left to point
    line1 = Line(x - size/3, y + size/6, x, y - size/3)
    line1.strokeColor = color
    line1.strokeWidth = 3
    d.add(line1)
    
    # Point to bottom right
    line2 = Line(x, y - size/3, x + size/3, y + size/6)
    line2.strokeColor = color
    line2.strokeWidth = 3
    d.add(line2)
    
    # Bottom line
    line3 = Line(x - size/3, y + size/6, x + size/3, y + size/6)
    line3.strokeColor = color
    line3.strokeWidth = 3
    d.add(line3)
    
    return d

def create_blood_vessel_icon(x, y, width, height, color):
    """Creates a blood vessel icon"""
    d = Drawing(width, height)
    
    # Main vessel
    vessel = Rect(x, y, width, height)
    vessel.fillColor = color
    vessel.strokeColor = colors.black
    vessel.strokeWidth = 2
    d.add(vessel)
    
    # Add blood cells (circles)
    for i in range(3):
        cell_y = y + height/4 + (i * height/4)
        cell = Circle(x + width/2, cell_y, width/8)
        cell.fillColor = colors.red
        cell.strokeColor = colors.black
        cell.strokeWidth = 1
        d.add(cell)
    
    return d

def create_health_status_visual(analysis):
    """Creates a visual health status overview with heart icon"""
    d = Drawing(500, 250)
    
    # Create a health status circle with heart
    center_x, center_y = 250, 125
    radius = 80
    
    # Count normal vs abnormal results
    normal_count = 0
    total_tests = 0
    
    for test_name, test_data in analysis.items():
        if test_name in ['bmi', 'blood_pressure', 'blood_sugar', 'cholesterol']:
            total_tests += 1
            if 'category' in test_data:
                if test_data['category'] in ['NORMAL', 'NORMAL WEIGHT']:
                    normal_count += 1
        elif test_name == 'urine':
            total_tests += 2  # glucose and protein
            if test_data.get('glucose') == 'NEGATIVE':
                normal_count += 1
            if test_data.get('protein') == 'NEGATIVE':
                normal_count += 1
        elif test_name == 'psa':
            psa_value = test_data.get('value')
            psa_result = test_data.get('result')
            has_psa_value = psa_value is not None and not (isinstance(psa_value, str) and psa_value.strip() == "") and not (pd.isna(psa_value) if hasattr(pd, 'isna') else False)
            valid_result = isinstance(psa_result, str) and psa_result.strip().upper() in {'NEGATIVE', 'POSITIVE'}
            if has_psa_value and valid_result:
                total_tests += 1
                if psa_result.strip().upper() == 'NEGATIVE':
                    normal_count += 1
    
    # Calculate health percentage
    if total_tests > 0:
        health_percentage = (normal_count / total_tests) * 100
    else:
        health_percentage = 0
    
    # Color based on health percentage
    if health_percentage >= 80:
        color = HexColor('#4CAF50')  # Green
        status = "Excellent"
    elif health_percentage >= 60:
        color = HexColor('#FFC107')  # Yellow
        status = "Good"
    else:
        color = HexColor('#F44336')  # Red
        status = "Needs Attention"
    
    # Draw the circle
    circle = Circle(center_x, center_y, radius)
    circle.fillColor = color
    circle.strokeColor = colors.black
    circle.strokeWidth = 3
    d.add(circle)
    
    # Add heart icon in the center
    heart = create_heart_icon(center_x, center_y, 60, colors.white)
    d.add(heart)
    
    # Add text
    d.add(String(center_x, center_y + 25, f"{health_percentage:.0f}%", 
                 textAnchor="middle", fontSize=18, fillColor=colors.white, fontName="Helvetica-Bold"))
    d.add(String(center_x, center_y - 25, status, 
                 textAnchor="middle", fontSize=14, fillColor=colors.white, fontName="Helvetica-Bold"))
    
    # Add health icons around the circle
    icon_positions = [
        (center_x - 120, center_y - 40, "BMI"),
        (center_x + 120, center_y - 40, "BP"),
        (center_x - 120, center_y + 40, "GLU"),
        (center_x + 120, center_y + 40, "CHOL")
    ]
    
    for x, y, label in icon_positions:
        # Small circle for each health parameter
        param_circle = Circle(x, y, 15)
        param_circle.fillColor = HexColor('#E3F2FD')
        param_circle.strokeColor = colors.black
        param_circle.strokeWidth = 1
        d.add(param_circle)
        
        # Label
        d.add(String(x, y - 25, label, 
                     textAnchor="middle", fontSize=10, fillColor=colors.black))
    
    return d

def create_person_icon(x, y, size, bmi_category):
    """Creates a person icon based on BMI category"""
    d = Drawing(size, size)
    
    # Body color based on BMI category
    if bmi_category == 'UNDERWEIGHT':
        body_color = HexColor('#2196F3')  # Blue
    elif bmi_category == 'NORMAL':
        body_color = HexColor('#4CAF50')  # Green
    elif bmi_category == 'OVERWEIGHT':
        body_color = HexColor('#FF9800')  # Orange
    else:  # OBESE
        body_color = HexColor('#F44336')  # Red
    
    # Head
    head = Circle(x, y + size/3, size/6)
    head.fillColor = body_color
    head.strokeColor = colors.black
    head.strokeWidth = 1
    d.add(head)
    
    # Body (varies by BMI category)
    if bmi_category == 'UNDERWEIGHT':
        # Thin body
        body = Rect(x - size/8, y - size/6, size/4, size/3)
    elif bmi_category == 'NORMAL':
        # Normal body
        body = Rect(x - size/6, y - size/6, size/3, size/3)
    elif bmi_category == 'OVERWEIGHT':
        # Wider body
        body = Rect(x - size/5, y - size/6, size/2.5, size/3)
    else:  # OBESE
        # Very wide body
        body = Rect(x - size/4, y - size/6, size/2, size/3)
    
    body.fillColor = body_color
    body.strokeColor = colors.black
    body.strokeWidth = 1
    d.add(body)
    
    # Arms
    left_arm = Rect(x - size/4, y - size/12, size/8, size/4)
    left_arm.fillColor = body_color
    left_arm.strokeColor = colors.black
    left_arm.strokeWidth = 1
    d.add(left_arm)
    
    right_arm = Rect(x + size/6, y - size/12, size/8, size/4)
    right_arm.fillColor = body_color
    right_arm.strokeColor = colors.black
    right_arm.strokeWidth = 1
    d.add(right_arm)
    
    # Legs
    left_leg = Rect(x - size/12, y - size/2, size/6, size/3)
    left_leg.fillColor = body_color
    left_leg.strokeColor = colors.black
    left_leg.strokeWidth = 1
    d.add(left_leg)
    
    right_leg = Rect(x + size/12, y - size/2, size/6, size/3)
    right_leg.fillColor = body_color
    right_leg.strokeColor = colors.black
    right_leg.strokeWidth = 1
    d.add(right_leg)
    
    return d

def create_bmi_visual(bmi_value, bmi_category):
    """Creates a visual BMI indicator with person icon"""
    d = Drawing(400, 200)
    
    # BMI scale ranges
    ranges = [
        (0, 18.5, "Underweight", HexColor('#2196F3')),
        (18.5, 25, "Normal", HexColor('#4CAF50')),
        (25, 30, "Overweight", HexColor('#FF9800')),
        (30, 50, "Obese", HexColor('#F44336'))
    ]
    
    # Draw BMI scale
    x_start, y = 50, 120
    scale_width = 250
    scale_height = 25
    
    for i, (min_val, max_val, label, color) in enumerate(ranges):
        x_pos = x_start + (i * scale_width / len(ranges))
        width = scale_width / len(ranges)
        
        rect = Rect(x_pos, y, width, scale_height)
        rect.fillColor = color
        rect.strokeColor = colors.black
        rect.strokeWidth = 2
        d.add(rect)
        
        # Add labels
        d.add(String(x_pos + width/2, y - 15, f"{min_val}-{max_val}", 
                     textAnchor="middle", fontSize=9, fontName="Helvetica-Bold"))
        d.add(String(x_pos + width/2, y - 30, label, 
                     textAnchor="middle", fontSize=8))
    
    # Mark current BMI
    if bmi_value <= 50:  # Cap at 50 for display
        bmi_x = x_start + (bmi_value / 50) * scale_width
        marker = Circle(bmi_x, y + scale_height/2, 8)
        marker.fillColor = colors.black
        marker.strokeColor = colors.white
        marker.strokeWidth = 3
        d.add(marker)
        
        # Add BMI value
        d.add(String(bmi_x, y + 50, f"Your BMI: {bmi_value:.1f}", 
                     textAnchor="middle", fontSize=12, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add person icon
    person_icon = create_person_icon(350, 100, 60, bmi_category)
    d.add(person_icon)
    
    # Add title
    d.add(String(200, 180, "Body Mass Index (BMI) Scale", 
                 textAnchor="middle", fontSize=14, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    return d

def create_blood_pressure_visual(systolic, diastolic, category):
    """Creates a visual blood pressure indicator with heart and blood vessel graphics"""
    d = Drawing(450, 200)
    
    # Blood pressure zones
    zones = [
        (0, 120, 0, 80, "Normal", HexColor('#4CAF50')),
        (120, 140, 80, 90, "Elevated", HexColor('#FFC107')),
        (140, 180, 90, 120, "High", HexColor('#F44336'))
    ]
    
    # Draw zones
    x_start, y_start = 50, 100
    zone_width = 200
    zone_height = 30
    
    for i, (min_sys, max_sys, min_dia, max_dia, label, color) in enumerate(zones):
        y_pos = y_start + (i * zone_height)
        
        rect = Rect(x_start, y_pos, zone_width, zone_height)
        rect.fillColor = color
        rect.strokeColor = colors.black
        rect.strokeWidth = 2
        d.add(rect)
        
        # Add labels
        d.add(String(x_start + zone_width/2, y_pos + zone_height/2 + 5, f"{min_sys}/{min_dia} - {max_sys}/{max_dia}", 
                     textAnchor="middle", fontSize=9, fontName="Helvetica-Bold"))
        d.add(String(x_start + zone_width/2, y_pos + zone_height/2 - 8, label, 
                     textAnchor="middle", fontSize=8))
    
    # Mark current reading
    if systolic <= 180 and diastolic <= 120:
        # Scale to fit in the visual
        sys_x = x_start + (systolic / 180) * zone_width
        dia_y = y_start + (diastolic / 120) * (zone_height * 3)
        
        marker = Circle(sys_x, dia_y, 6)
        marker.fillColor = colors.black
        marker.strokeColor = colors.white
        marker.strokeWidth = 3
        d.add(marker)
        
        # Add current reading
        d.add(String(x_start + zone_width/2, y_start - 20, f"Your Reading: {systolic}/{diastolic} mmHg", 
                     textAnchor="middle", fontSize=12, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add heart icon
    heart_icon = create_heart_icon(300, 130, 40, colors.red)
    d.add(heart_icon)
    
    # Add blood vessel icon
    vessel_icon = create_blood_vessel_icon(350, 120, 60, 30, HexColor('#E8F5E8'))
    d.add(vessel_icon)
    
    # Add title
    d.add(String(225, 180, "Blood Pressure Zones", 
                 textAnchor="middle", fontSize=14, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add heart rate indicator
    d.add(String(320, 100, "Heart", 
                 textAnchor="middle", fontSize=10, fillColor=colors.black))
    d.add(String(380, 100, "Blood Flow", 
                 textAnchor="middle", fontSize=10, fillColor=colors.black))
    
    return d

def create_glucose_molecule_icon(x, y, size, color):
    """Creates a glucose molecule icon"""
    d = Drawing(size, size)
    
    # Central carbon ring
    center_circle = Circle(x, y, size/6)
    center_circle.fillColor = color
    center_circle.strokeColor = colors.black
    center_circle.strokeWidth = 2
    d.add(center_circle)
    
    # Surrounding atoms (circles)
    atom_positions = [
        (x - size/3, y, size/8),
        (x + size/3, y, size/8),
        (x, y - size/3, size/8),
        (x, y + size/3, size/8),
        (x - size/4, y - size/4, size/8),
        (x + size/4, y + size/4, size/8)
    ]
    
    for atom_x, atom_y, atom_size in atom_positions:
        atom = Circle(atom_x, atom_y, atom_size)
        atom.fillColor = HexColor('#FFD700')  # Gold color for atoms
        atom.strokeColor = colors.black
        atom.strokeWidth = 1
        d.add(atom)
    
    return d

def create_blood_sugar_visual(glucose_value, glucose_category):
    """Creates a visual blood sugar indicator with glucose molecules"""
    d = Drawing(400, 200)
    
    # Blood sugar ranges
    ranges = [
        (0, 100, "Normal", HexColor('#4CAF50')),
        (100, 125, "Pre-diabetic", HexColor('#FFC107')),
        (125, 200, "Diabetic", HexColor('#F44336'))
    ]
    
    # Draw ranges
    x_start, y = 50, 120
    scale_width = 250
    scale_height = 25
    
    for i, (min_val, max_val, label, color) in enumerate(ranges):
        x_pos = x_start + (i * scale_width / len(ranges))
        width = scale_width / len(ranges)
        
        rect = Rect(x_pos, y, width, scale_height)
        rect.fillColor = color
        rect.strokeColor = colors.black
        rect.strokeWidth = 2
        d.add(rect)
        
        # Add labels
        d.add(String(x_pos + width/2, y - 15, f"{min_val}-{max_val} mg/dL", 
                     textAnchor="middle", fontSize=9, fontName="Helvetica-Bold"))
        d.add(String(x_pos + width/2, y - 30, label, 
                     textAnchor="middle", fontSize=8))
    
    # Mark current glucose level
    if glucose_value <= 200:
        glucose_x = x_start + (glucose_value / 200) * scale_width
        marker = Circle(glucose_x, y + scale_height/2, 8)
        marker.fillColor = colors.black
        marker.strokeColor = colors.white
        marker.strokeWidth = 3
        d.add(marker)
        
        # Add glucose value
        d.add(String(glucose_x, y + 50, f"Your Level: {glucose_value} mg/dL", 
                     textAnchor="middle", fontSize=12, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add glucose molecule icons
    molecule1 = create_glucose_molecule_icon(320, 100, 40, HexColor('#E8F5E8'))
    d.add(molecule1)
    
    molecule2 = create_glucose_molecule_icon(360, 120, 30, HexColor('#E8F5E8'))
    d.add(molecule2)
    
    molecule3 = create_glucose_molecule_icon(340, 140, 35, HexColor('#E8F5E8'))
    d.add(molecule3)
    
    # Add title
    d.add(String(200, 180, "Blood Sugar (Glucose) Levels", 
                 textAnchor="middle", fontSize=14, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add glucose molecules label
    d.add(String(340, 80, "Glucose", 
                 textAnchor="middle", fontSize=10, fillColor=colors.black))
    d.add(String(340, 70, "Molecules", 
                 textAnchor="middle", fontSize=10, fillColor=colors.black))
    
    return d

def create_artery_icon(x, y, width, height, cholesterol_level):
    """Creates an artery icon showing cholesterol buildup"""
    d = Drawing(width, height)
    
    # Artery wall
    artery = Rect(x, y, width, height)
    artery.fillColor = HexColor('#F5F5F5')
    artery.strokeColor = colors.black
    artery.strokeWidth = 2
    d.add(artery)
    
    # Cholesterol buildup based on level
    if cholesterol_level > 200:
        # High cholesterol - more buildup
        buildup_height = height * 0.3
        buildup = Rect(x + 5, y + height/2 - buildup_height/2, width - 10, buildup_height)
        buildup.fillColor = HexColor('#FF6B6B')  # Red for high cholesterol
        buildup.strokeColor = colors.black
        buildup.strokeWidth = 1
        d.add(buildup)
    elif cholesterol_level > 150:
        # Moderate cholesterol - some buildup
        buildup_height = height * 0.2
        buildup = Rect(x + 5, y + height/2 - buildup_height/2, width - 10, buildup_height)
        buildup.fillColor = HexColor('#FFA500')  # Orange for moderate
        buildup.strokeColor = colors.black
        buildup.strokeWidth = 1
        d.add(buildup)
    else:
        # Normal cholesterol - minimal buildup
        buildup_height = height * 0.1
        buildup = Rect(x + 5, y + height/2 - buildup_height/2, width - 10, buildup_height)
        buildup.fillColor = HexColor('#90EE90')  # Light green for normal
        buildup.strokeColor = colors.black
        buildup.strokeWidth = 1
        d.add(buildup)
    
    # Blood flow (red circles)
    for i in range(3):
        flow_y = y + height/4 + (i * height/4)
        flow_cell = Circle(x + width/2, flow_y, width/8)
        flow_cell.fillColor = colors.red
        flow_cell.strokeColor = colors.black
        flow_cell.strokeWidth = 1
        d.add(flow_cell)
    
    return d

def create_cholesterol_visual(cholesterol_value, chol_category):
    """Creates a visual cholesterol indicator with artery graphics"""
    d = Drawing(400, 200)
    
    # Cholesterol ranges
    ranges = [
        (0, 200, "Normal", HexColor('#4CAF50')),
        (200, 240, "Borderline High", HexColor('#FFC107')),
        (240, 300, "High", HexColor('#F44336'))
    ]
    
    # Draw ranges
    x_start, y = 50, 120
    scale_width = 250
    scale_height = 25
    
    for i, (min_val, max_val, label, color) in enumerate(ranges):
        x_pos = x_start + (i * scale_width / len(ranges))
        width = scale_width / len(ranges)
        
        rect = Rect(x_pos, y, width, scale_height)
        rect.fillColor = color
        rect.strokeColor = colors.black
        rect.strokeWidth = 2
        d.add(rect)
        
        # Add labels
        d.add(String(x_pos + width/2, y - 15, f"{min_val}-{max_val} mg/dL", 
                     textAnchor="middle", fontSize=9, fontName="Helvetica-Bold"))
        d.add(String(x_pos + width/2, y - 30, label, 
                     textAnchor="middle", fontSize=8))
    
    # Mark current cholesterol level
    if cholesterol_value <= 300:
        chol_x = x_start + (cholesterol_value / 300) * scale_width
        marker = Circle(chol_x, y + scale_height/2, 8)
        marker.fillColor = colors.black
        marker.strokeColor = colors.white
        marker.strokeWidth = 3
        d.add(marker)
        
        # Add cholesterol value
        d.add(String(chol_x, y + 50, f"Your Level: {cholesterol_value} mg/dL", 
                     textAnchor="middle", fontSize=12, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add artery icons
    artery1 = create_artery_icon(320, 100, 60, 40, cholesterol_value)
    d.add(artery1)
    
    artery2 = create_artery_icon(360, 110, 50, 30, cholesterol_value)
    d.add(artery2)
    
    # Add title
    d.add(String(200, 180, "Total Cholesterol Levels", 
                 textAnchor="middle", fontSize=14, fillColor=colors.black, fontName="Helvetica-Bold"))
    
    # Add artery labels
    d.add(String(350, 90, "Artery", 
                 textAnchor="middle", fontSize=10, fillColor=colors.black))
    d.add(String(350, 80, "Health", 
                 textAnchor="middle", fontSize=10, fillColor=colors.black))
    
    return d

def create_bmi_section(analysis, individual_data):
    """Creates the BMI analysis section with educational content"""
    styles = getSampleStyleSheet()
    elements = []
    
    if 'bmi' not in analysis:
        return elements
    
    bmi_data = analysis['bmi']
    bmi_value = bmi_data['value']
    bmi_category = bmi_data['category']
    
    elements.append(Paragraph("Body Mass Index (BMI)", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # BMI Definition and Ranges
    bmi_text = f"""
    <b>Your BMI is {bmi_value:.1f}, which puts you in the {bmi_category} range.</b><br/><br/>
    
    <b>What does this mean?</b> BMI is a measure of body fat based on your height and weight. 
    It helps us understand if you're carrying a healthy amount of weight for your body size.<br/><br/>
    
    <b>BMI Categories:</b><br/>
    • Underweight: BMI < 18.5<br/>
    • Normal weight: BMI 18.5-24.9<br/>
    • Overweight: BMI 25-29.9<br/>
    • Obese: BMI ≥ 30<br/><br/>
    """
    
    elements.append(Paragraph(bmi_text, styles['Normal']))
    
    # Add BMI image
    try:
        bmi_section_image = Image("/Users/kenechukwuchukwuka/Downloads/download_win/HEALTH SCREEN/body-mass-index.png", 
                                 width=200, height=150)
        bmi_section_image.hAlign = 'CENTER'
        elements.append(bmi_section_image)
        elements.append(Spacer(1, 12))
    except:
        pass  # Skip if image not found
    
    # Health implications based on BMI category
    if bmi_category == 'UNDERWEIGHT':
        implications = f"""
        <b>What does this mean?</b> You're carrying less weight than is ideal, which can affect your energy levels and overall health.<br/><br/>
        
        <b>The bright side?</b> You're at lower risk for weight-related conditions like diabetes and heart disease.<br/><br/>
        
        <b>Tips just for you:</b><br/>
        • Focus on nutrient-dense foods to gain healthy weight<br/>
        • Add strength training to build muscle mass<br/>
        • Eat regular, balanced meals throughout the day<br/>
        • Consider talking to a nutritionist for personalized guidance<br/><br/>
        """
    elif bmi_category == 'NORMAL':
        implications = f"""
        <b>The bright side?</b> Your weight is in the healthy range! This means you're at lower risk for many chronic diseases and your body is functioning optimally.<br/><br/>
        
        <b>Keep it up by:</b><br/>
        • Staying active with regular exercise<br/>
        • Maintaining a balanced diet<br/>
        • Keeping an eye on your weight to stay in this healthy range<br/>
        • Continuing regular health checkups<br/><br/>
        """
    elif bmi_category == 'OVERWEIGHT':
        # Check actual blood pressure, blood sugar, and cholesterol values
        bp_status = "normal"
        glucose_status = "normal" 
        chol_status = "normal"
        
        if pd.notna(bmi_data.get('systolic')) and pd.notna(bmi_data.get('diastolic')):
            if bmi_data['systolic'] > 140 or bmi_data['diastolic'] > 90:
                bp_status = "high"
            elif bmi_data['systolic'] > 120 or bmi_data['diastolic'] > 80:
                bp_status = "elevated"
        
        if pd.notna(bmi_data.get('blood_glucose')):
            if bmi_data['blood_glucose'] > 125:
                glucose_status = "high"
            elif bmi_data['blood_glucose'] > 100:
                glucose_status = "elevated"
        
        if pd.notna(bmi_data.get('cholesterol')):
            if bmi_data['cholesterol'] > 240:
                chol_status = "high"
            elif bmi_data['cholesterol'] > 200:
                chol_status = "elevated"
        
        # Create dynamic bright side message
        normal_params = []
        if bp_status == "normal":
            normal_params.append("blood pressure")
        if glucose_status == "normal":
            normal_params.append("blood sugar")
        if chol_status == "normal":
            normal_params.append("cholesterol")
        
        if normal_params:
            if len(normal_params) == 3:
                bright_side = "Your blood pressure, blood sugar, and cholesterol are all normal — so your body is handling things really well right now."
            elif len(normal_params) == 2:
                bright_side = f"Your {normal_params[0]} and {normal_params[1]} are normal — which is great news!"
            else:
                bright_side = f"Your {normal_params[0]} is normal — which is a positive sign!"
        else:
            bright_side = "The good news is that with the right approach, you can improve all these numbers together!"
        
        implications = f"""
        <b>What does this mean?</b> You're carrying a bit more weight than is ideal, which can slightly raise your risk for diabetes, joint problems, or high blood pressure in the future.<br/><br/>
        
        <b>The bright side?</b> {bright_side}<br/><br/>
        
        <b>Tips just for you:</b><br/>
        • Eat more whole foods and fewer processed ones<br/>
        • Stay active — aim for 150 minutes of fun movement per week<br/>
        • Add strength training to boost metabolism<br/>
        • Drink plenty of water, and sleep well<br/><br/>
        """
    else:  # OBESE
        implications = f"""
        <b>What does this mean?</b> You're carrying significantly more weight than is ideal, which increases your risk for several health conditions including diabetes, heart disease, and joint problems.<br/><br/>
        
        <b>The bright side?</b> With the right approach, you can make meaningful changes to improve your health and reduce these risks.<br/><br/>
        
        <b>Tips just for you:</b><br/>
        • Focus on whole, unprocessed foods<br/>
        • Start with gentle activities and gradually increase intensity<br/>
        • Include both cardio and strength training<br/>
        • Work with healthcare professionals for personalized guidance<br/>
        • Stay hydrated and prioritize good sleep<br/><br/>
        """
    
    elements.append(Paragraph(implications, styles['Normal']))
    
    # Cross-reference with other parameters
    cross_ref_text = "<b>How your BMI connects with your other health numbers:</b><br/>"
    
    if pd.notna(bmi_data.get('systolic')) and pd.notna(bmi_data.get('diastolic')):
        bp_status = "high" if bmi_data['systolic'] > 140 or bmi_data['diastolic'] > 90 else "normal"
        cross_ref_text += f"• Your blood pressure is {bp_status} ({bmi_data['systolic']}/{bmi_data['diastolic']} mmHg)<br/>"
    
    if pd.notna(bmi_data.get('blood_glucose')):
        glucose_status = "elevated" if bmi_data['blood_glucose'] > 100 else "normal"
        cross_ref_text += f"• Your blood sugar is {glucose_status} ({bmi_data['blood_glucose']} mg/dL)<br/>"
    
    if pd.notna(bmi_data.get('cholesterol')):
        chol_status = "high" if bmi_data['cholesterol'] > 200 else "normal"
        cross_ref_text += f"• Your cholesterol is {chol_status} ({bmi_data['cholesterol']} mg/dL)<br/>"
    
    cross_ref_text += "<br/>"
    elements.append(Paragraph(cross_ref_text, styles['Normal']))
    
    # Recommendations
    if bmi_category in ['OVERWEIGHT', 'OBESE']:
        recommendations = """
        <b>Recommendations to Reduce BMI:</b><br/>
        • <b>Dietary Changes:</b> Focus on whole foods, reduce processed foods, control portion sizes<br/>
        • <b>Regular Exercise:</b> Aim for 150 minutes of moderate exercise per week<br/>
        • <b>Strength Training:</b> Build muscle mass to increase metabolism<br/>
        • <b>Hydration:</b> Drink plenty of water throughout the day<br/>
        • <b>Sleep:</b> Ensure 7-9 hours of quality sleep nightly<br/>
        • <b>Stress Management:</b> Practice relaxation techniques<br/>
        • <b>Professional Support:</b> Consider consulting a nutritionist or dietitian<br/><br/>
        """
    elif bmi_category == 'UNDERWEIGHT':
        recommendations = """
        <b>Recommendations to Increase BMI Healthily:</b><br/>
        • <b>Nutrient-Dense Foods:</b> Focus on healthy fats, lean proteins, and complex carbs<br/>
        • <b>Strength Training:</b> Build muscle mass through resistance exercises<br/>
        • <b>Regular Meals:</b> Eat 5-6 small meals throughout the day<br/>
        • <b>Healthy Snacking:</b> Include nuts, avocados, and dairy products<br/>
        • <b>Medical Check:</b> Rule out underlying health conditions<br/><br/>
        """
    else:
        recommendations = """
        <b>Maintaining Your Healthy BMI:</b><br/>
        • <b>Consistent Exercise:</b> Continue regular physical activity<br/>
        • <b>Balanced Diet:</b> Maintain a variety of nutritious foods<br/>
        • <b>Regular Monitoring:</b> Check your weight and BMI monthly<br/>
        • <b>Lifestyle Balance:</b> Maintain healthy habits long-term<br/><br/>
        """
    
    elements.append(Paragraph(recommendations, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_blood_pressure_section(analysis, individual_data):
    """Creates the blood pressure analysis section"""
    styles = getSampleStyleSheet()
    elements = []
    
    if 'blood_pressure' not in analysis:
        return elements
    
    bp_data = analysis['blood_pressure']
    systolic = bp_data['systolic']
    diastolic = bp_data['diastolic']
    bp_category = bp_data['category']
    
    elements.append(Paragraph("Blood Pressure", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Blood Pressure Definition and Ranges
    bp_text = f"""
    <b>Your reading is {systolic}/{diastolic} mmHg, which is {bp_category.lower()}.</b><br/><br/>
    
    <b>What does this mean?</b> Blood pressure is the force of blood pushing against your artery walls. 
    It's like the pressure in a garden hose - too high and it can cause problems, too low and it might not work properly.<br/><br/>
    
    <b>Blood Pressure Categories:</b><br/>
    • Normal: Less than 120/80 mmHg<br/>
    • Elevated: 120-129/less than 80 mmHg<br/>
    • High Stage 1: 130-139/80-89 mmHg<br/>
    • High Stage 2: 140/90 mmHg or higher<br/>
    • Hypertensive Crisis: Higher than 180/120 mmHg<br/><br/>
    """
    
    elements.append(Paragraph(bp_text, styles['Normal']))
    
    # Add blood pressure image
    try:
        bp_section_image = Image("/Users/kenechukwuchukwuka/Downloads/download_win/HEALTH SCREEN/hypertension-101-causes-warning-signs-and-impact-on-healthl-ArtemisHospitals.png", 
                                width=200, height=150)
        bp_section_image.hAlign = 'CENTER'
        elements.append(bp_section_image)
        elements.append(Spacer(1, 12))
    except:
        pass  # Skip if image not found
    
    # Health implications
    if bp_category == 'LOW':
        implications = f"""
        <b>👉 What does this mean?</b> Your blood pressure is lower than normal, which can sometimes cause dizziness or fatigue.<br/><br/>
        
        <b>✨ The bright side?</b> You're at very low risk for heart disease and stroke!<br/><br/>
        
        <b>💡 Keep it up by:</b><br/>
        💧 Staying well hydrated<br/>
        🧂 Adding a bit more salt to your diet (with doctor's approval)<br/>
        🏃 Standing up slowly to avoid dizziness<br/>
        🩺 Regular checkups to monitor your levels<br/><br/>
        """
    elif bp_category == 'NORMAL':
        implications = f"""
        <b>✨ Great work! Your blood pressure is in the healthy range.</b><br/><br/>
        
        <b>👉 This means your heart and blood vessels are in good shape. You're at lower risk of heart disease, stroke, and kidney problems.</b><br/><br/>
        
        <b>💡 Keep it up by:</b><br/>
        🌱 Maintaining your healthy lifestyle<br/>
        ⏱️ Checking your BP regularly<br/>
        🩺 Seeing your doctor for routine checkups<br/><br/>
        """
    else:  # HIGH or MODERATE HIGH
        implications = f"""
        <b>👉 What does this mean?</b> Your blood pressure is elevated, which means your heart is working harder than it should.<br/><br/>
        
        <b>✨ The bright side?</b> With proper management, you can significantly reduce your risks and protect your health.<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🩺 Work closely with your doctor for proper management<br/>
        💊 Take any prescribed medications as directed<br/>
        🧂 Dramatically reduce sodium intake<br/>
        🏃 Get regular, doctor-approved exercise<br/>
        😌 Focus on stress reduction<br/><br/>
        """
    
    elements.append(Paragraph(implications, styles['Normal']))
    
    # Cross-reference with other parameters
    cross_ref_text = "<b>How your blood pressure relates to other health parameters:</b><br/>"
    
    if pd.notna(bp_data.get('bmi')):
        bmi_status = "high" if bp_data['bmi'] > 25 else "normal"
        cross_ref_text += f"• Your BMI is {bmi_status} ({bp_data['bmi']:.1f})<br/>"
    
    if pd.notna(bp_data.get('blood_glucose')):
        glucose_status = "elevated" if bp_data['blood_glucose'] > 100 else "normal"
        cross_ref_text += f"• Your blood sugar is {glucose_status} ({bp_data['blood_glucose']} mg/dL)<br/>"
    
    if pd.notna(bp_data.get('cholesterol')):
        chol_status = "high" if bp_data['cholesterol'] > 200 else "normal"
        cross_ref_text += f"• Your cholesterol is {chol_status} ({bp_data['cholesterol']} mg/dL)<br/>"
    
    cross_ref_text += "<br/>"
    elements.append(Paragraph(cross_ref_text, styles['Normal']))
    
    # Recommendations
    if bp_category in ['HIGH', 'MODERATE HIGH']:
        recommendations = """
        <b>Recommendations to Lower Blood Pressure:</b><br/>
        • <b>DASH Diet:</b> Focus on fruits, vegetables, whole grains, and lean proteins<br/>
        • <b>Reduce Sodium:</b> Limit salt intake to less than 2,300mg daily<br/>
        • <b>Regular Exercise:</b> 30 minutes of moderate activity most days<br/>
        • <b>Weight Management:</b> Maintain a healthy BMI<br/>
        • <b>Limit Alcohol:</b> No more than 1 drink per day for women, 2 for men<br/>
        • <b>Stress Management:</b> Practice relaxation techniques<br/>
        • <b>Medication:</b> Follow your doctor's prescription if prescribed<br/><br/>
        """
    elif bp_category == 'LOW':
        recommendations = """
        <b>Recommendations for Low Blood Pressure:</b><br/>
        • <b>Increase Salt Intake:</b> Add moderate amounts of salt to your diet<br/>
        • <b>Stay Hydrated:</b> Drink plenty of fluids<br/>
        • <b>Gradual Position Changes:</b> Move slowly when standing up<br/>
        • <b>Compression Stockings:</b> May help improve circulation<br/>
        • <b>Medical Evaluation:</b> Consult your doctor if symptoms persist<br/><br/>
        """
    else:
        recommendations = """
        <b>Maintaining Healthy Blood Pressure:</b><br/>
        • <b>Continue Healthy Habits:</b> Maintain your current lifestyle<br/>
        • <b>Regular Monitoring:</b> Check your blood pressure regularly<br/>
        • <b>Annual Checkups:</b> See your doctor for routine health checks<br/><br/>
        """
    
    elements.append(Paragraph(recommendations, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_blood_sugar_section(analysis, individual_data):
    """Creates the blood sugar analysis section"""
    styles = getSampleStyleSheet()
    elements = []
    
    if 'blood_sugar' not in analysis:
        return elements
    
    glucose_data = analysis['blood_sugar']
    glucose_value = glucose_data['value']
    glucose_category = glucose_data['category']
    
    elements.append(Paragraph("🍬 Blood Sugar", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Blood Sugar Definition and Ranges
    glucose_text = f"""
    <b>📊 Your blood sugar is {glucose_value} mg/dL, which is {glucose_category.lower()}.</b><br/><br/>
    
    <b>👉 What does this mean?</b> Blood sugar (glucose) is your body's main source of energy, 
    like fuel for a car. Your body regulates it with insulin to keep it in the right range.<br/><br/>
    
    <b>📏 Blood Sugar Categories (Random/Fasting):</b><br/>
    • Normal: Less than 100 mg/dL (fasting) / Less than 140 mg/dL (random)<br/>
    • Pre-diabetic: 100-125 mg/dL (fasting) / 140-199 mg/dL (random)<br/>
    • Diabetic: 126 mg/dL or higher (fasting) / 200 mg/dL or higher (random)<br/><br/>
    """
    
    elements.append(Paragraph(glucose_text, styles['Normal']))
    
    # Add blood sugar image
    try:
        glucose_section_image = Image("/Users/kenechukwuchukwuka/Downloads/download_win/HEALTH SCREEN/Blood-sugar-e1545320562250.png", 
                                     width=200, height=150)
        glucose_section_image.hAlign = 'CENTER'
        elements.append(glucose_section_image)
        elements.append(Spacer(1, 12))
    except:
        pass  # Skip if image not found
    
    # Health implications
    if glucose_category == 'NORMAL':
        implications = f"""
        <b>✨ Excellent! Your blood sugar is in the healthy range.</b><br/><br/>
        
        <b>👉 This means your body is regulating energy beautifully — less chance of diabetes and more steady energy levels through the day.</b><br/><br/>
        
        <b>💡 Keep your sugar in the sweet spot by:</b><br/>
        🥗 Eating balanced meals<br/>
        🏃 Keeping active<br/>
        ⚖️ Watching your weight to keep BMI in check<br/><br/>
        """
    elif glucose_category == 'PRE_DIABETIC':
        implications = f"""
        <b>👉 What does this mean?</b> Your blood sugar is higher than normal but not quite in the diabetic range yet. This is like a warning sign that your body is having trouble processing sugar efficiently.<br/><br/>
        
        <b>✨ The bright side?</b> This is often reversible with lifestyle changes! You're catching it early.<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🥗 Focus on whole foods and reduce processed carbs<br/>
        🏃 Get regular exercise to help your body use sugar better<br/>
        ⚖️ Work on achieving a healthy weight<br/>
        🩺 Work with your doctor to monitor and manage it<br/><br/>
        """
    else:  # DIABETIC
        implications = f"""
        <b>👉 What does this mean?</b> Your blood sugar is consistently high, which means your body isn't producing enough insulin or isn't using it effectively.<br/><br/>
        
        <b>✨ The bright side?</b> With proper management, you can live a full, healthy life and prevent complications.<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🩺 Work closely with your doctor for proper management<br/>
        💊 Take any prescribed medications as directed<br/>
        🥗 Follow a diabetes-friendly meal plan<br/>
        🏃 Get regular, doctor-approved exercise<br/>
        📊 Monitor your blood sugar regularly<br/><br/>
        """
    
    elements.append(Paragraph(implications, styles['Normal']))
    
    # Cross-reference with other parameters
    cross_ref_text = "<b>How your blood sugar relates to other health parameters:</b><br/>"
    
    if pd.notna(glucose_data.get('bmi')):
        bmi_status = "high" if glucose_data['bmi'] > 25 else "normal"
        cross_ref_text += f"• Your BMI is {bmi_status} ({glucose_data['bmi']:.1f})<br/>"
    
    if pd.notna(glucose_data.get('systolic')) and pd.notna(glucose_data.get('diastolic')):
        bp_status = "high" if glucose_data['systolic'] > 140 or glucose_data['diastolic'] > 90 else "normal"
        cross_ref_text += f"• Your blood pressure is {bp_status} ({glucose_data['systolic']}/{glucose_data['diastolic']} mmHg)<br/>"
    
    if pd.notna(glucose_data.get('cholesterol')):
        chol_status = "high" if glucose_data['cholesterol'] > 200 else "normal"
        cross_ref_text += f"• Your cholesterol is {chol_status} ({glucose_data['cholesterol']} mg/dL)<br/>"
    
    cross_ref_text += "<br/>"
    elements.append(Paragraph(cross_ref_text, styles['Normal']))
    
    # Recommendations
    if glucose_category == 'DIABETIC':
        recommendations = """
        <b>Recommendations for Diabetes Management:</b><br/>
        • <b>Medical Care:</b> Work closely with your healthcare team<br/>
        • <b>Blood Sugar Monitoring:</b> Check levels regularly as advised<br/>
        • <b>Medication Adherence:</b> Take prescribed medications as directed<br/>
        • <b>Carbohydrate Counting:</b> Learn to manage carb intake<br/>
        • <b>Regular Exercise:</b> 150 minutes of moderate activity weekly<br/>
        • <b>Foot Care:</b> Check feet daily for cuts or sores<br/>
        • <b>Regular Checkups:</b> See your doctor every 3-6 months<br/><br/>
        """
    elif glucose_category == 'PRE_DIABETIC':
        recommendations = """
        <b>Recommendations to Prevent Diabetes:</b><br/>
        • <b>Weight Loss:</b> Lose 5-7% of body weight if overweight<br/>
        • <b>Physical Activity:</b> 150 minutes of moderate exercise weekly<br/>
        • <b>Healthy Diet:</b> Focus on whole grains, vegetables, and lean proteins<br/>
        • <b>Limit Sugars:</b> Reduce added sugars and refined carbohydrates<br/>
        • <b>Regular Monitoring:</b> Check blood sugar levels regularly<br/>
        • <b>Lifestyle Changes:</b> Make sustainable long-term changes<br/><br/>
        """
    else:
        recommendations = """
        <b>Maintaining Healthy Blood Sugar:</b><br/>
        • <b>Balanced Diet:</b> Continue eating a variety of nutritious foods<br/>
        • <b>Regular Exercise:</b> Maintain your current activity level<br/>
        • <b>Weight Management:</b> Keep your BMI in the healthy range<br/>
        • <b>Regular Checkups:</b> Continue annual health screenings<br/><br/>
        """
    
    elements.append(Paragraph(recommendations, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_cholesterol_section(analysis, individual_data):
    """Creates the cholesterol analysis section"""
    styles = getSampleStyleSheet()
    elements = []
    
    if 'cholesterol' not in analysis:
        return elements
    
    chol_data = analysis['cholesterol']
    cholesterol_value = chol_data['value']
    chol_category = chol_data['category']
    
    elements.append(Paragraph("🧈 Cholesterol", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Cholesterol Definition and Ranges
    chol_text = f"""
    <b>📊 Your cholesterol is {cholesterol_value} mg/dL, which is {chol_category.lower()}.</b><br/><br/>
    
    <b>👉 What does this mean?</b> Cholesterol is a waxy substance your body uses to build healthy cells. 
    Think of it like building materials - you need some, but too much can clog your arteries like pipes.<br/><br/>
    
    <b>📏 Total Cholesterol Categories:</b><br/>
    • Desirable: Less than 200 mg/dL<br/>
    • Borderline High: 200-239 mg/dL<br/>
    • High: 240 mg/dL and above<br/><br/>
    """
    
    elements.append(Paragraph(chol_text, styles['Normal']))
    
    # Add cholesterol image
    try:
        cholesterol_section_image = Image("/Users/kenechukwuchukwuka/Downloads/download_win/HEALTH SCREEN/high-cholesterol-overview.webp", 
                                         width=200, height=150)
        cholesterol_section_image.hAlign = 'CENTER'
        elements.append(cholesterol_section_image)
        elements.append(Spacer(1, 12))
    except:
        pass  # Skip if image not found
    
    # Health implications
    if chol_category == 'NORMAL':
        implications = f"""
        <b>✨ Excellent! Your cholesterol is in the healthy range.</b><br/><br/>
        
        <b>👉 This is excellent news! It means lower risk of heart disease and stroke, and your heart health is looking solid.</b><br/><br/>
        
        <b>💡 To keep it that way:</b><br/>
        🥑 Stick with a variety of nutritious foods<br/>
        🚶 Stay active<br/>
        🩺 Recheck cholesterol every year<br/><br/>
        """
    elif chol_category == 'BORDERLINE HIGH':
        implications = f"""
        <b>👉 What does this mean?</b> Your cholesterol is slightly elevated, which means there's a bit more cholesterol in your blood than ideal.<br/><br/>
        
        <b>✨ The bright side?</b> This is often manageable with lifestyle changes, and you're catching it early!<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🥑 Focus on heart-healthy foods like fish, nuts, and vegetables<br/>
        🚶 Get regular exercise to help your body process cholesterol better<br/>
        🧂 Reduce saturated and trans fats in your diet<br/>
        🩺 Work with your doctor to monitor and manage it<br/><br/>
        """
    else:  # HIGH
        implications = f"""
        <b>👉 What does this mean?</b> Your cholesterol is significantly elevated, which increases your risk of heart disease and stroke.<br/><br/>
        
        <b>✨ The bright side?</b> With proper management, you can significantly reduce your risks and protect your heart health.<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🩺 Work closely with your doctor for proper management<br/>
        💊 Take any prescribed medications as directed<br/>
        🥑 Dramatically reduce saturated and trans fats<br/>
        🚶 Get regular, doctor-approved exercise<br/>
        🥗 Focus on a heart-healthy diet<br/><br/>
        """
    
    elements.append(Paragraph(implications, styles['Normal']))
    
    # Cross-reference with other parameters
    cross_ref_text = "<b>How your cholesterol relates to other health parameters:</b><br/>"
    
    if pd.notna(chol_data.get('bmi')):
        bmi_status = "high" if chol_data['bmi'] > 25 else "normal"
        cross_ref_text += f"• Your BMI is {bmi_status} ({chol_data['bmi']:.1f})<br/>"
    
    if pd.notna(chol_data.get('systolic')) and pd.notna(chol_data.get('diastolic')):
        bp_status = "high" if chol_data['systolic'] > 140 or chol_data['diastolic'] > 90 else "normal"
        cross_ref_text += f"• Your blood pressure is {bp_status} ({chol_data['systolic']}/{chol_data['diastolic']} mmHg)<br/>"
    
    if pd.notna(chol_data.get('blood_glucose')):
        glucose_status = "elevated" if chol_data['blood_glucose'] > 100 else "normal"
        cross_ref_text += f"• Your blood sugar is {glucose_status} ({chol_data['blood_glucose']} mg/dL)<br/>"
    
    cross_ref_text += "<br/>"
    elements.append(Paragraph(cross_ref_text, styles['Normal']))
    
    # Recommendations
    if chol_category in ['HIGH', 'BORDERLINE HIGH']:
        recommendations = """
        <b>Recommendations to Lower Cholesterol:</b><br/>
        • <b>Heart-Healthy Diet:</b> Focus on fruits, vegetables, whole grains, and lean proteins<br/>
        • <b>Reduce Saturated Fats:</b> Limit red meat, full-fat dairy, and fried foods<br/>
        • <b>Increase Fiber:</b> Eat more oats, beans, and fruits<br/>
        • <b>Regular Exercise:</b> 150 minutes of moderate activity weekly<br/>
        • <b>Weight Management:</b> Maintain a healthy BMI<br/>
        • <b>Limit Alcohol:</b> Moderate alcohol consumption<br/>
        • <b>Medication:</b> Take prescribed cholesterol-lowering drugs as directed<br/><br/>
        """
    else:
        recommendations = """
        <b>Maintaining Healthy Cholesterol:</b><br/>
        • <b>Continue Healthy Habits:</b> Maintain your current lifestyle<br/>
        • <b>Regular Monitoring:</b> Check cholesterol levels annually<br/>
        • <b>Balanced Diet:</b> Keep eating a variety of nutritious foods<br/>
        • <b>Regular Exercise:</b> Continue your current activity level<br/><br/>
        """
    
    elements.append(Paragraph(recommendations, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_urine_section(analysis, individual_data):
    """Creates the urine analysis section"""
    styles = getSampleStyleSheet()
    elements = []
    
    if 'urine' not in analysis:
        return elements
    
    urine_data = analysis['urine']
    glucose_result = urine_data['glucose']
    protein_result = urine_data['protein']
    
    elements.append(Paragraph("💧 Urine Analysis", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Add kidney/renal health image under the header
    try:
        kidney_image = Image("/Users/kenechukwuchukwuka/Downloads/download_win/HEALTH SCREEN/world-kidney-day-renal-health-organ-awareness-global-care-nephrology-focus-medical-celebration-bodily-function-filtration-351627608.webp",
                             width=200, height=120)
        kidney_image.hAlign = 'CENTER'
        elements.append(kidney_image)
        elements.append(Spacer(1, 12))
    except Exception:
        pass  # If image not available, continue without it
    
    # Urine Analysis Introduction
    urine_text = f"""
    <b>📊 Results: Glucose – {glucose_result}, Protein – {protein_result}.</b><br/><br/>
    
    <b>👉 What does this mean?</b> Urine analysis is like a health detective! It looks for clues in your urine 
    that can tell us about your kidney health and how well your body is managing sugar. Think of it as a 
    simple way to check if everything is working properly inside.<br/><br/>
    """
    
    elements.append(Paragraph(urine_text, styles['Normal']))
    
    # Glucose in Urine Analysis
    elements.append(Paragraph("🍬 Glucose in Urine:", styles['Heading2']))
    if glucose_result == 'POSITIVE':
        glucose_analysis = f"""
        <b>👉 What does this mean?</b> Glucose was found in your urine, which is like finding sugar in a place 
        where it shouldn't be. This suggests your blood sugar levels are high enough to "spill over" into your urine.<br/><br/>
        
        <b>✨ The bright side?</b> We caught this early! This is often a warning sign that can be managed with 
        the right approach.<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🩺 Work with your doctor to check your blood sugar levels<br/>
        🥗 Focus on a diabetes-friendly diet<br/>
        🏃 Get regular exercise to help your body use sugar better<br/>
        📊 Monitor your blood sugar regularly<br/><br/>
        """
    else:
        glucose_analysis = f"""
        <b>✨ Great news! No glucose detected in your urine.</b><br/><br/>
        
        <b>👉 This means your kidneys are working perfectly, and your body is managing sugar properly.</b><br/><br/>
        
        <b>💡 Keep protecting your kidneys by:</b><br/>
        💧 Drinking plenty of water<br/>
        🩺 Keeping up with annual health checks<br/>
        🌱 Staying healthy overall<br/><br/>
        """
    
    elements.append(Paragraph(glucose_analysis, styles['Normal']))
    
    # Protein in Urine Analysis
    elements.append(Paragraph("🥚 Protein in Urine:", styles['Heading2']))
    if protein_result == 'POSITIVE':
        protein_analysis = f"""
        <b>👉 What does this mean?</b> Protein was found in your urine, which is like finding building blocks 
        where they shouldn't be. This suggests your kidneys might be letting protein "leak" through when they shouldn't.<br/><br/>
        
        <b>✨ The bright side?</b> Early detection means we can take action to protect your kidney health!<br/><br/>
        
        <b>💡 Tips just for you:</b><br/>
        🩺 Work closely with your doctor for proper evaluation<br/>
        💧 Stay well hydrated to support kidney function<br/>
        🧂 Reduce sodium intake to ease kidney workload<br/>
        🏃 Get regular exercise (with doctor's approval)<br/>
        📊 Monitor your blood pressure and blood sugar<br/><br/>
        """
    else:
        protein_analysis = f"""
        <b>✨ Excellent! No protein detected in your urine.</b><br/><br/>
        
        <b>👉 This means your kidneys are working perfectly, and your body is managing protein properly.</b><br/><br/>
        
        <b>💡 Keep protecting your kidneys by:</b><br/>
        💧 Drinking plenty of water<br/>
        🩺 Keeping up with annual health checks<br/>
        🌱 Staying healthy overall<br/><br/>
        """
    
    elements.append(Paragraph(protein_analysis, styles['Normal']))
    
    # Recommendations
    recommendations = "<b>💡 My recommendations for you:</b><br/>"
    
    if glucose_result == 'POSITIVE' or protein_result == 'POSITIVE':
        recommendations += f"""
        🩺 <b>Medical Follow-up:</b> Schedule an appointment with your doctor to discuss these results<br/>
        📊 <b>Further Testing:</b> You may need additional blood or urine tests to get the full picture<br/>
        🌱 <b>Lifestyle Focus:</b> Pay extra attention to your diet, exercise, and stress management<br/>
        📈 <b>Regular Monitoring:</b> Keep track of your health numbers regularly<br/>
        💊 <b>Medication Support:</b> Take any prescribed medications exactly as your doctor directs<br/><br/>
        """
    else:
        recommendations += f"""
        🎉 <b>Keep up the great work!</b> Your kidneys are doing their job perfectly<br/>
        🩺 <b>Regular Checkups:</b> Continue with annual health screenings to stay on track<br/>
        💧 <b>Stay Hydrated:</b> Keep drinking plenty of water to support your kidney health<br/>
        👀 <b>Stay Alert:</b> Keep an eye on any changes in your health and report them<br/><br/>
        """
    
    elements.append(Paragraph(recommendations, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_psa_section(analysis, individual_data):
    """Creates the PSA analysis section"""
    styles = getSampleStyleSheet()
    elements = []
    
    if 'psa' not in analysis:
        return elements
    
    psa_data = analysis['psa']
    psa_value = psa_data.get('value')
    psa_result = psa_data.get('result')
    # Guard: skip entire section if PSA not actually measured
    has_psa_value = psa_value is not None and not (isinstance(psa_value, str) and psa_value.strip() == "") and not (pd.isna(psa_value) if hasattr(pd, 'isna') else False)
    valid_result = isinstance(psa_result, str) and psa_result.strip().upper() in {'NEGATIVE', 'POSITIVE'}
    if not (has_psa_value and valid_result):
        return []
    age = psa_data.get('age', 'Unknown')
    gender = psa_data.get('gender', 'Unknown')
    
    elements.append(Paragraph("Prostate Specific Antigen (PSA)", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # PSA Definition and Purpose
    psa_text = f"""
    <b>Your PSA test result is {psa_result}.</b><br/><br/>
    
    <b>What does this mean?</b> PSA (Prostate Specific Antigen) is a protein made by the prostate gland. 
    Think of it as a health marker that helps us detect prostate issues early, including prostate cancer. 
    This test is especially important for men over 40 as part of routine health screening.<br/><br/>
    
    <b>PSA Test Interpretation:</b><br/>
    • <b>NEGATIVE (Normal):</b> PSA levels are within normal range (typically below 4.0 ng/mL)<br/>
    • <b>POSITIVE (Elevated):</b> PSA levels are above normal range, requiring further evaluation<br/><br/>
    """
    
    elements.append(Paragraph(psa_text, styles['Normal']))
    
    # Health implications based on PSA result
    if psa_result == 'NEGATIVE':
        implications = f"""
        <b>The bright side?</b> Your PSA levels are in the healthy range! This is great news for your prostate health.<br/><br/>
        
        <b>What does this mean?</b> Your prostate is functioning normally and you're at lower risk for prostate-related issues.<br/><br/>
        
        <b>Keep protecting your prostate by:</b><br/>
        • Continuing regular health checkups as recommended<br/>
        • Maintaining a healthy lifestyle with good nutrition<br/>
        • Staying active and managing stress<br/>
        • Following your doctor's screening schedule<br/><br/>
        """
    else:  # POSITIVE
        implications = f"""
        <b>What does this mean?</b> Your PSA levels are elevated, which means we need to investigate further. 
        Don't worry - this doesn't automatically mean cancer!<br/><br/>
        
        <b>The bright side?</b> We caught this early, and there are many reasons why PSA can be elevated. 
        It could be due to prostate inflammation, infection, or benign enlargement.<br/><br/>
        
        <b>Tips just for you:</b><br/>
        • Work closely with your doctor for proper evaluation<br/>
        • Don't panic - elevated PSA has many possible causes<br/>
        • Further testing will help determine the exact cause<br/>
        • Early detection means better treatment options if needed<br/>
        • Stay positive and follow your doctor's recommendations<br/><br/>
        """
    
    elements.append(Paragraph(implications, styles['Normal']))
    
    # Prevention and Management recommendations
    if psa_result == 'NEGATIVE':
        recommendations = f"""
        <b>My recommendations for you:</b><br/>
        • <b>Regular Exercise:</b> Stay physically active to maintain overall health<br/>
        • <b>Healthy Diet:</b> Eat plenty of fruits, vegetables, and whole grains<br/>
        • <b>Limit Red Meat:</b> Reduce consumption of processed and red meats<br/>
        • <b>Stay Hydrated:</b> Drink plenty of water throughout the day<br/>
        • <b>Regular Checkups:</b> Continue annual PSA testing as recommended<br/>
        • <b>Maintain Healthy Weight:</b> Keep your BMI in the normal range<br/>
        • <b>Limit Alcohol:</b> Moderate alcohol consumption<br/>
        • <b>Stress Management:</b> Practice relaxation techniques<br/><br/>
        """
    else:  # POSITIVE
        recommendations = f"""
        <b>My recommendations for you:</b><br/>
        • <b>Medical Follow-up:</b> Schedule an appointment with a urologist<br/>
        • <b>Additional Testing:</b> May need digital rectal exam, MRI, or biopsy<br/>
        • <b>Lifestyle Changes:</b> Adopt a prostate-healthy diet and exercise routine<br/>
        • <b>Regular Monitoring:</b> More frequent PSA testing may be recommended<br/>
        • <b>Stay Informed:</b> Learn about prostate health and screening options<br/>
        • <b>Support System:</b> Don't hesitate to seek support from family and friends<br/>
        • <b>Stay Positive:</b> Remember that elevated PSA doesn't always mean cancer<br/><br/>
        """
    
    elements.append(Paragraph(recommendations, styles['Normal']))
    
    # General prostate health tips
    general_tips = f"""
    <b>Prostate health tips for all men:</b><br/>
    • <b>Know Your Family History:</b> Share any family history of prostate problems with your doctor<br/>
    • <b>Eat Tomatoes:</b> Lycopene in tomatoes may help protect prostate health<br/>
    • <b>Include Healthy Fats:</b> Omega-3 fatty acids from fish and nuts are beneficial<br/>
    • <b>Stay Active:</b> Regular exercise helps maintain overall health<br/>
    • <b>Don't Smoke:</b> Smoking increases risk of various health problems<br/>
    • <b>Regular Screening:</b> Follow your doctor's recommendations for PSA testing<br/><br/>
    """
    
    elements.append(Paragraph(general_tips, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def create_individual_conclusion(individual_data, analysis):
    """Creates the personalized conclusion section"""
    styles = getSampleStyleSheet()
    elements = []
    
    name = individual_data.get('NAME', 'Valued Employee')
    
    elements.append(Paragraph("🌟 Your Personalized Health Summary", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Count available tests
    available_tests = []
    if 'bmi' in analysis:
        available_tests.append("BMI")
    if 'blood_pressure' in analysis:
        available_tests.append("Blood Pressure")
    if 'blood_sugar' in analysis:
        available_tests.append("Blood Sugar")
    if 'cholesterol' in analysis:
        available_tests.append("Cholesterol")
    if 'urine' in analysis:
        available_tests.append("Urine Analysis")
    if 'psa' in analysis:
        psa_data = analysis.get('psa', {})
        psa_value = psa_data.get('value')
        psa_result = psa_data.get('result')
        has_psa_value = psa_value is not None and not (isinstance(psa_value, str) and psa_value.strip() == "") and not (pd.isna(psa_value) if hasattr(pd, 'isna') else False)
        valid_result = isinstance(psa_result, str) and psa_result.strip().upper() in {'NEGATIVE', 'POSITIVE'}
        if has_psa_value and valid_result:
            available_tests.append("PSA")
    
    tests_text = ", ".join(available_tests) if available_tests else "basic health parameters"
    
    # Check if person has high blood pressure or high blood sugar
    has_high_bp = False
    has_high_glucose = False
    
    if 'blood_pressure' in analysis:
        bp_category = analysis['blood_pressure'].get('category', '')
        if bp_category in ['HIGH', 'MODERATE HIGH']:
            has_high_bp = True
    
    if 'blood_sugar' in analysis:
        glucose_category = analysis['blood_sugar'].get('category', '')
        if glucose_category in ['DIABETIC', 'PRE_DIABETIC']:
            has_high_glucose = True
    
    conclusion_text = f"""
    <b>{name}, overall you're doing really well! ✅</b><br/><br/>
    
    I've analyzed your {tests_text} results, and I'm excited to share what I found! Your health numbers tell a story, 
    and I'm here to help you understand what they mean for your future.<br/><br/>
    
    <b>🔍 What I discovered:</b><br/>
    • Your test results show your current health status across multiple important areas<br/>
    • Each number gives us clues about how well your body is functioning<br/>
    • Small changes can make a big difference in your health journey<br/>
    • You're in control of many factors that influence these numbers<br/><br/>
    
    <b>🚀 Your next steps:</b><br/>
    • Take time to understand what each result means for you personally<br/>
    • Start with one small change - you don't have to do everything at once!<br/>
    • Talk to your doctor about any concerns or questions<br/>
    • Reach out to our medical team at WhatsApp 08076490056 for telemedicine consultation anytime<br/>
    • Remember, every healthy choice you make is a step in the right direction<br/><br/>
    """
    
    # Add CDR program recommendation only for those with high BP or high blood sugar
    if has_high_bp or has_high_glucose:
        conclusion_text += """
    <b>💚 How can Clearline help:</b><br/>
    We have a CDR (Chronic Disease Registry) program where we attach each person to a doctor that checks up on them 
    regularly to ensure their needs are met, explain their readings, and encourage them to take their drugs. 
    This system is run through our mobile app. If you are interested, kindly send a mail to 
    <b>hello@clearlinehmo.com</b> and someone will take it up from there.<br/><br/>
    """
    
    conclusion_text += f"""
    Keep making small, steady lifestyle changes and you'll continue moving in the right direction.<br/><br/>
    
    Remember, I'm always here to help you make sense of your health. Your future self will thank you for the choices you make today! 🚀💚<br/><br/>
    
    <b>With care and support,<br/>
    Klaire, your friendly health bot 🤖</b>
    """
    
    elements.append(Paragraph(conclusion_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    return elements

def generate_individual_report(individual_data, analysis, output_path):
    """
    Generates a personalized PDF report for an individual
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
    story.extend(create_individual_title(individual_data))
    story.extend(create_individual_introduction(individual_data))
    
    # Add health overview visual
    story.extend(add_health_overview_visual(analysis))
    
    # Add page break before main content
    story.append(PageBreak())
    
    # Add BMI section
    story.extend(create_bmi_section(analysis, individual_data))
    
    # Add blood pressure section
    story.extend(create_blood_pressure_section(analysis, individual_data))
    
    # Add blood sugar section
    story.extend(create_blood_sugar_section(analysis, individual_data))
    
    # Add cholesterol section
    story.extend(create_cholesterol_section(analysis, individual_data))
    
    # Add urine analysis section
    story.extend(create_urine_section(analysis, individual_data))
    
    # Add PSA analysis section only if PSA has valid data
    psa_data = analysis.get('psa', {}) if isinstance(analysis, dict) else {}
    psa_value = psa_data.get('value') if isinstance(psa_data, dict) else None
    psa_result = psa_data.get('result') if isinstance(psa_data, dict) else None
    has_psa_value = psa_value is not None and not (isinstance(psa_value, str) and psa_value.strip() == "") and not (pd.isna(psa_value) if hasattr(pd, 'isna') else False)
    valid_result = isinstance(psa_result, str) and psa_result.strip().upper() in {'NEGATIVE', 'POSITIVE'}
    if has_psa_value and valid_result:
        story.extend(create_psa_section(analysis, individual_data))
    
    # Add page break before conclusion
    story.append(PageBreak())
    
    # Add conclusion section
    story.extend(create_individual_conclusion(individual_data, analysis))
    
    # Footer renderer with Clearline logo on each page
    def _add_footer(canvas, doc):
        try:
            logo_path = "/Users/kenechukwuchukwuka/Downloads/download_win/HEALTH SCREEN/Clearline.png"
            # Draw the logo at the bottom-right corner
            logo_width, logo_height = 80, 40
            x = doc.pagesize[0] - doc.rightMargin - logo_width
            y = doc.bottomMargin - (logo_height * 0.6)
            canvas.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        except Exception:
            # If logo not found, skip silently
            pass
        # Optional: page number on footer left
        try:
            canvas.setFont("Helvetica", 9)
            canvas.drawString(doc.leftMargin, doc.bottomMargin - 10, f"Page {doc.page}")
        except Exception:
            pass

    # Build the PDF
    try:
        doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
        print(f"Individual report successfully generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating individual report: {e}")
        raise e

if __name__ == "__main__":
    # Test the individual report generator
    print("Individual Report Generator - Test Mode")
    print("This module is designed to be used with the main HEALTH_SCREEN.py script")
    print("Reports will be saved with ENROLLEE ID as filename (e.g., CL_ARIK_022_2017.pdf)")
