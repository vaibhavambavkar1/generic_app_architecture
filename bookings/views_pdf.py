import io
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .models import Booking
from .views import get_business

@login_required
def booking_receipt_pdf(request, pk):
    business = get_business(request)
    booking = get_object_or_404(Booking, pk=pk, business=business)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=1, # Center
        spaceAfter=14
    )
    normal_style = styles['Normal']
    bold_style = ParagraphStyle('BoldStyle', parent=normal_style, fontName='Helvetica-Bold')

    # Header
    story.append(Paragraph(f"{business.name} - Booking Confirmation", title_style))
    story.append(Spacer(1, 12))
    
    # Booking Info
    info_data = [
        [Paragraph("<b>Booking #:</b>", normal_style), Paragraph(booking.booking_number, normal_style)],
        [Paragraph("<b>Customer Name:</b>", normal_style), Paragraph(booking.customer.name, normal_style)],
        [Paragraph("<b>Date:</b>", normal_style), Paragraph(booking.start_datetime.strftime("%Y-%m-%d %H:%M"), normal_style)],
        [Paragraph("<b>Status:</b>", normal_style), Paragraph(booking.status, normal_style)],
    ]
    info_table = Table(info_data, colWidths=[120, 400])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 24))

    # Items Table Header
    items_data = [
        [Paragraph("<b>Description</b>", normal_style), 
         Paragraph("<b>Qty</b>", normal_style), 
         Paragraph("<b>Unit Price</b>", normal_style), 
         Paragraph("<b>Total</b>", normal_style)]
    ]
    
    # Items
    for item in booking.items.all():
        items_data.append([
            Paragraph(f"{item.resource.name} ({item.resource.resource_type.name})", normal_style),
            Paragraph(str(item.quantity), normal_style),
            Paragraph(f"{business.currency} {item.unit_price}", normal_style),
            Paragraph(f"{business.currency} {item.line_total}", normal_style)
        ])
    
    for addon in booking.addons.all():
        items_data.append([
            Paragraph(f"{addon.addon.name} (Add-on)", normal_style),
            Paragraph(str(addon.quantity), normal_style),
            Paragraph(f"{business.currency} {addon.unit_price}", normal_style),
            Paragraph(f"{business.currency} {addon.line_total}", normal_style)
        ])

    items_table = Table(items_data, colWidths=[260, 60, 100, 100])
    items_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')), # Primary color
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    # Totals
    totals_data = [
        ["", "", Paragraph("<b>Subtotal:</b>", normal_style), Paragraph(f"{business.currency} {booking.subtotal}", normal_style)],
        ["", "", Paragraph("<b>Tax:</b>", normal_style), Paragraph(f"{business.currency} {booking.tax_amount}", normal_style)],
        ["", "", Paragraph("<b>Discount:</b>", normal_style), Paragraph(f"-{business.currency} {booking.discount_amount}", normal_style)],
        ["", "", Paragraph("<b>Total:</b>", bold_style), Paragraph(f"<b>{business.currency} {booking.total_amount}</b>", bold_style)],
    ]
    totals_table = Table(totals_data, colWidths=[160, 160, 100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(totals_table)
    
    story.append(Spacer(1, 48))
    story.append(Paragraph("Thank you for your business!", ParagraphStyle('ThankYou', parent=normal_style, alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Booking_Confirmation_{booking.booking_number}.pdf")
