import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

def generate_payslip_pdf(payslip):
    """
    Generate a professional PDF payslip.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'SheetTitle', parent=styles['Title'],
        fontSize=20, leading=24, alignment=TA_CENTER,
        spaceAfter=10 * mm, fontName='Helvetica-Bold'
    )
    story.append(Paragraph("PAYSLIP", title_style))

    # Employee Details
    company_style = ParagraphStyle(
        'Company', parent=styles['Normal'],
        fontSize=12, alignment=TA_CENTER,
        spaceAfter=15 * mm
    )
    story.append(Paragraph("<b>Generic ERP Framework</b>", company_style))
    
    emp = payslip.employee
    
    emp_details = [
        ["Employee Name:", emp.user.get_full_name(), "Employee ID:", emp.employee_id],
        ["Designation:", emp.designation, "Department:", emp.department],
        ["Month:", payslip.month.strftime('%B %Y'), "Date of Joining:", str(emp.date_of_joining) if emp.date_of_joining else "-"],
    ]

    detail_table = Table(emp_details, colWidths=[35*mm, 50*mm, 35*mm, 50*mm])
    detail_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 15 * mm))

    # Salary Details
    salary_data = [
        ["Earnings", "Amount (Rs.)", "Deductions", "Amount (Rs.)"],
        ["Base Salary", f"{payslip.base_salary:,.2f}", "Tax Deductions", f"{payslip.tax_deductions:,.2f}"],
        ["HRA", f"{payslip.hra:,.2f}", "", ""],
        ["Other Allowances", f"{payslip.other_allowances:,.2f}", "", ""],
        ["", "", "", ""],
        ["Total Earnings", f"{(payslip.base_salary + payslip.hra + payslip.other_allowances):,.2f}", 
         "Total Deductions", f"{payslip.tax_deductions:,.2f}"],
    ]

    salary_table = Table(salary_data, colWidths=[60*mm, 25*mm, 60*mm, 25*mm])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(salary_table)
    story.append(Spacer(1, 10 * mm))

    # Net Salary
    net_salary_style = ParagraphStyle(
        'NetSalary', parent=styles['Normal'],
        fontSize=14, alignment=TA_RIGHT, fontName='Helvetica-Bold'
    )
    story.append(Paragraph(f"Net Salary Payable: Rs. {payslip.net_salary:,.2f}", net_salary_style))

    story.append(Spacer(1, 30 * mm))
    
    # Signature
    sig_data = [
        ["_________________________", "_________________________"],
        ["Employer Signature", "Employee Signature"]
    ]
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica'),
        ('TEXTCOLOR', (0,1), (-1,1), colors.grey),
    ]))
    
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
