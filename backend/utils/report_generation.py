from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors


def generate_excel_report(title: str, data: dict, file_path: Path):
    """
    Generates an Excel (`.xlsx`) report with the given title and data.

    Saves your data in two rows (headers and values) as a table.

    The report will be saved at the specified file path (use `.xlsx` format).

    Args:
        title (str): the title that will be used for the report
        data (dict): dict data that will be placed in the table
        file_path (Path): where you need to save the path
    """

    workbook = Workbook()
    sheet = workbook.active

    # title
    sheet.title = title

    # headers
    headers = list(data.items())

    for row, (header, value) in enumerate(headers, start=1):
        sheet.cell(row=1, column=row, value=header)
        sheet.cell(row=2, column=row, value=value)

    # style headers, adjust column widths
    header_fill = PatternFill(
        start_color="FFCF40",
        end_color="FFCF40",
        fill_type="solid"
    )

    for col in sheet.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        sheet.column_dimensions[col_letter].width = max(max_len + 3, 11)
        if col[0].row == 1:
            col[0].fill = header_fill

    # save on the path
    if file_path.exists():
        # remove existing file to avoid overwrite issues
        # maybe need to create copy of the file instead of deleting it?
        file_path.unlink()
    workbook.save(file_path)


def generate_pdf_report(title: str, data: dict, file_path: Path, imgs: list[Path] | None = None):
    """
    Generates a PDF report with the given title and data.

    The report will be saved at the specified file path (use `.pdf` format).

    **ONLY ENGLISH (for now)**

    Args:
        title (str): the title that will be used for the report
        data (dict): dict data that will be placed in the table
        file_path (Path): where you need to save the path
        imgs (list[Path] | None, optional): the images you want to add to the report. Defaults to None.
    """
    document = SimpleDocTemplate(
        filename=str(file_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40
    )

    # styles object
    styles = getSampleStyleSheet()

    # document's elements
    story = []

    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 10))

    headers = ["Parameter", "Value"]
    table_data = [headers] + list(data.items())

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTSIZE',   (0, 0), (-1, 0), 11),

        ('FONTSIZE',   (0, 1), (-1, -1), 10),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.grey),

        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    # add optional images
    if imgs is not None:
        story.append(PageBreak())
        story.append(Paragraph(f"{title}: images", styles['Title']))
        for img in imgs:
            img = Image(img)
            # scale
            width = document.width * 0.7
            scale = width / img.imageWidth
            img.drawWidth = width
            img.drawHeight = img.imageHeight * scale

            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 10))

    # save on the path
    document.build(story)
