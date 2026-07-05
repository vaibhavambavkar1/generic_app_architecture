import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class BasePDFReport:
    """Base class for standardizing PDF reports across the ERP."""
    def __init__(self, title="Report", margin=36):
        self.buffer = io.BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=margin,
            bottomMargin=margin
        )
        self.styles = getSampleStyleSheet()
        self.story = []
        
        # Add Title
        self.add_heading(title)

    def add_heading(self, text):
        style = self.styles['Heading1']
        self.story.append(Paragraph(text, style))
        self.story.append(Spacer(1, 12))
        
    def add_paragraph(self, text):
        self.story.append(Paragraph(text, self.styles['Normal']))
        self.story.append(Spacer(1, 8))
        
    def add_table(self, data, col_widths=None):
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#111827')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        self.story.append(table)
        self.story.append(Spacer(1, 12))
        
    def build(self):
        self.doc.build(self.story)
        self.buffer.seek(0)
        return self.buffer
