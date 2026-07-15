"""
Barcode & QR Code PDF Label Sheet Generator for Inventory Products.

Generates a printable A4 PDF sheet laid out in a grid of sticker labels,
each containing the product's barcode (Code128), QR code, SKU, and name.
Designed for cutting and pasting onto product boxes.
"""
import io
import barcode
from barcode.writer import ImageWriter
import qrcode

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


# ---------------------------------------------------------------------------
# Label configuration (standard 3-column x 7-row sticker sheet, A4)
# ---------------------------------------------------------------------------
LABELS_PER_ROW = 3
LABELS_PER_COL = 7
LABELS_PER_PAGE = LABELS_PER_ROW * LABELS_PER_COL  # 21 labels/page

LABEL_WIDTH = 63.5 * mm    # ~63.5mm standard label width
LABEL_HEIGHT = 38.1 * mm   # ~38.1mm standard label height

BARCODE_WIDTH = 50 * mm
BARCODE_HEIGHT = 12 * mm
QR_SIZE = 22 * mm


def _generate_barcode_image(sku):
    """Generate a Code128 barcode PNG in memory and return a BytesIO buffer."""
    code128 = barcode.get_barcode_class('code128')
    writer = ImageWriter()
    # Configure writer for compact labels
    writer.set_options({
        'module_width': 0.25,
        'module_height': 6.0,
        'font_size': 6,
        'text_distance': 2.0,
        'quiet_zone': 2.0,
    })
    bc = code128(sku, writer=writer)
    buffer = io.BytesIO()
    bc.write(buffer)
    buffer.seek(0)
    return buffer


def _generate_qr_image(data):
    """Generate a QR code PNG in memory and return a BytesIO buffer."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def _build_label_flowable(item, styles, label_type='both'):
    """
    Build one label cell as a Table flowable containing:
    - Product Name (truncated)
    - SKU text
    - Barcode image and/or QR code image
    """
    elements = []

    # Product Name
    name_style = ParagraphStyle(
        'LabelName', parent=styles['Normal'],
        fontSize=7, leading=8, alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    sku_style = ParagraphStyle(
        'LabelSKU', parent=styles['Normal'],
        fontSize=6, leading=7, alignment=TA_CENTER,
        fontName='Helvetica', textColor=colors.grey,
    )

    truncated_name = item.name[:30] + ('...' if len(item.name) > 30 else '')
    elements.append(Paragraph(truncated_name, name_style))
    elements.append(Spacer(1, 1 * mm))
    elements.append(Paragraph(item.sku, sku_style))
    elements.append(Spacer(1, 1.5 * mm))

    if label_type in ('barcode', 'both'):
        bc_buffer = _generate_barcode_image(item.sku)
        bc_img = RLImage(bc_buffer, width=BARCODE_WIDTH, height=BARCODE_HEIGHT)
        elements.append(bc_img)

    if label_type in ('qr', 'both'):
        qr_buffer = _generate_qr_image(item.sku)
        qr_img = RLImage(qr_buffer, width=QR_SIZE, height=QR_SIZE)
        elements.append(qr_img)

    # Wrap in a fixed-size cell table for uniform sizing
    cell_table = Table(
        [[e] for e in elements],
        colWidths=[LABEL_WIDTH - 4 * mm],
    )
    cell_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    return cell_table


def generate_label_sheet_pdf(items, label_type='both', copies=1):
    """
    Generate a multi-page A4 PDF of printable product labels.

    Args:
        items: QuerySet or list of InventoryItem instances.
        label_type: 'barcode', 'qr', or 'both'.
        copies: Number of label copies per product (e.g., 3 labels for 3 boxes).

    Returns:
        BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        leftMargin=7 * mm,
        rightMargin=7 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title page header
    title_style = ParagraphStyle(
        'SheetTitle', parent=styles['Title'],
        fontSize=14, leading=16, alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )
    story.append(Paragraph("Product Label Sheet", title_style))

    # Expand items by copies
    label_items = []
    for item in items:
        label_items.extend([item] * copies)

    # Chunk into pages
    for page_start in range(0, len(label_items), LABELS_PER_PAGE):
        page_items = label_items[page_start:page_start + LABELS_PER_PAGE]

        # Build rows
        rows = []
        for row_start in range(0, len(page_items), LABELS_PER_ROW):
            row_items = page_items[row_start:row_start + LABELS_PER_ROW]
            row_cells = []
            for item in row_items:
                cell = _build_label_flowable(item, styles, label_type)
                row_cells.append(cell)

            # Pad incomplete rows with empty cells
            while len(row_cells) < LABELS_PER_ROW:
                row_cells.append('')

            rows.append(row_cells)

        # Build page grid
        grid = Table(
            rows,
            colWidths=[LABEL_WIDTH] * LABELS_PER_ROW,
            rowHeights=[LABEL_HEIGHT] * len(rows),
        )
        grid.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        story.append(grid)

        # Add page break if more pages follow
        if page_start + LABELS_PER_PAGE < len(label_items):
            story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer
