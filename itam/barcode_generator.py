from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing
import io
import time

def generate_asset_labels(assets):
    """
    Generate PDF with Asset barcode and QR code labels.
    """
    buffer = io.BytesIO()
    
    # We will just print one label per page for simplicity, similar to an asset tag printer
    # Pagesize 3x1 inches roughly for an asset tag
    tag_width = 3 * inch
    tag_height = 1.5 * inch
    
    p = canvas.Canvas(buffer, pagesize=(tag_width, tag_height))
    
    for asset in assets:
        # Title/Company Header
        p.setFont("Helvetica-Bold", 10)
        p.drawString(0.1 * inch, 1.25 * inch, "PROPERTY OF ORGANIZATION")
        
        # Asset Info
        p.setFont("Helvetica", 8)
        p.drawString(0.1 * inch, 1.1 * inch, f"Asset: {asset.name[:30]}")
        p.drawString(0.1 * inch, 0.95 * inch, f"S/N: {asset.serial_number}")
        
        # Barcode
        barcode = code128.Code128(asset.barcode, barHeight=0.4*inch, barWidth=1.2)
        barcode.drawOn(p, 0.1 * inch, 0.3 * inch)
        
        # Human Readable Barcode text
        p.setFont("Helvetica-Bold", 8)
        p.drawString(0.1 * inch, 0.15 * inch, asset.barcode)
        
        # QR Code (right side)
        qr_code = qr.QrCodeWidget(asset.barcode)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        d = Drawing(width, height)
        d.add(qr_code)
        # Scale to fit
        scale = 0.8 * inch / width
        d.scale(scale, scale)
        d.drawOn(p, 2.0 * inch, 0.3 * inch)
        
        p.showPage()
        
    p.save()
    buffer.seek(0)
    
    filename = f"asset_labels_{int(time.time())}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)
