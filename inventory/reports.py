from core.reports.pdf import BasePDFReport
from reportlab.platypus import Paragraph

def generate_po_pdf(po):
    report = BasePDFReport(title=f"Purchase Order #PO-{po.id:04d}")
    
    report.add_paragraph(f"<b>Date Created:</b> {po.created_at.strftime('%Y-%m-%d')}")
    report.add_paragraph(f"<b>Current Status:</b> {po.workflow_state.name if po.workflow_state else 'Draft'}")
    
    # Ensure text wrapping by using a Paragraph for strings that might be long
    item_desc = f"{po.item.name}<br/>SKU: {po.item.sku}"
    
    data = [
        ["Item Details", "Quantity", "Total Cost (USD)"],
        [Paragraph(item_desc, report.styles['Normal']), f"{po.quantity} units", f"${po.total_cost:,.2f}"]
    ]
    
    report.add_table(data, col_widths=[250, 120, 120])
    
    report.add_paragraph("<i>System generated receipt.</i>")
    
    return report.build()
