import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.barcode import code128

def generate_waybill_pdf(waybill):
    """
    Generates a PDF Waybill with a Code128 barcode.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Header
    elements.append(Paragraph(f"<b>Waybill / Consignment Note</b>", styles['Title']))
    elements.append(Spacer(1, 20))

    # Barcode
    barcode = code128.Code128(waybill.waybill_number, barHeight=40, barWidth=1.5)
    elements.append(barcode)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Tracking No:</b> {waybill.waybill_number}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Sender & Receiver Info
    data = [
        ['SENDER', 'RECEIVER'],
        [waybill.sender.name if waybill.sender else 'N/A', waybill.receiver_name],
        [waybill.sender_address, waybill.receiver_address],
        ['', f"Phone: {waybill.receiver_phone}"],
    ]
    
    t = Table(data, colWidths=[250, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Package Details
    details_data = [
        ['Origin Zone', waybill.origin_zone.name if waybill.origin_zone else 'N/A'],
        ['Destination Zone', waybill.destination_zone.name if waybill.destination_zone else 'N/A'],
        ['Service Type', waybill.service_type.name if waybill.service_type else 'N/A'],
        ['Actual Weight (kg)', str(waybill.weight_kg)],
        ['Volumetric (m3)', str(waybill.volume_m3)],
        ['Chargeable Weight', str(waybill.chargeable_weight)],
        ['Total Price', f"${waybill.price}"],
    ]
    
    t_details = Table(details_data, colWidths=[200, 300])
    t_details.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))
    elements.append(t_details)
    
    # Generate PDF
    doc.build(elements)
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f"Waybill_{waybill.waybill_number}.pdf")
