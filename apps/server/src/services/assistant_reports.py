from __future__ import annotations

import re
import smtplib
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from html import escape
from io import BytesIO
from pathlib import Path
from string import Template
from typing import Any

from docx import Document
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class ReportArtifact:
    filename: str
    content_type: str
    content: bytes


_MAILPIT_HOST = "mailpit"
_MAILPIT_PORT = 1025
_EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
_DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PDF_TYPE = "application/pdf"
_EMAIL_TEMPLATE_DIRECTORY = Path(__file__).resolve().parents[2] / "templates" / "emails"
_FIELD_LABELS = {
    "start_date": "Data inicial",
    "end_date": "Data final",
    "currency": "Moeda",
    "income_total": "Total de receitas",
    "expense_total": "Total de despesas",
    "balance": "Saldo",
    "transaction_count": "Quantidade de transações",
    "expenses_by_category": "Despesas por categoria",
}
_MONEY_FIELDS = {"income_total", "expense_total", "balance"}
_CATEGORY_LABELS = {
    "food": "Alimentação",
    "work": "Trabalho",
    "groceries": "Supermercado",
    "transport": "Transporte",
    "transportation": "Transporte",
    "housing": "Moradia",
    "health": "Saúde",
    "medical": "Saúde",
    "education": "Educação",
    "entertainment": "Entretenimento",
    "pets": "Animais de estimação",
    "travel": "Viagem",
    "utilities": "Contas e serviços",
    "salary": "Salário",
    "other": "Outros",
}


def _display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, dict):
        return "; ".join(f"{key}: {_display(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return ", ".join(_display(item) for item in value)
    return str(value)


def _summary_rows(summary: dict[str, object]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key, value in summary.items():
        label = _FIELD_LABELS.get(str(key), str(key).replace("_", " ").capitalize())
        if key in _MONEY_FIELDS:
            display = _format_brl(value)
        elif key in ("start_date", "end_date"):
            display = _format_date(value)
        elif key == "currency" and str(value).upper() == "BRL":
            display = "Real brasileiro (BRL)"
        elif key == "expenses_by_category":
            display = _format_categories(value)
        else:
            display = _display(value)
        rows.append((label, display))
    return rows or [("Resumo", "Sem dados disponíveis")]


def _format_brl(value: Any) -> str:
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return _display(value)
        formatted = f"{abs(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"-R$ {formatted}" if amount < 0 else f"R$ {formatted}"
    except (InvalidOperation, ValueError, TypeError):
        return _display(value)


def _format_date(value: Any) -> str:
    if isinstance(value, str):
        try:
            return date.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError:
            pass
    return _display(value)


def _format_categories(value: Any) -> str:
    if not isinstance(value, (list, tuple)):
        return _display(value)
    formatted: list[str] = []
    for item in value:
        if isinstance(item, dict) and "category" in item and "total" in item:
            category = str(item["category"])
            category = _CATEGORY_LABELS.get(category.strip().lower(), category.replace("_", " ").capitalize())
            formatted.append(f"{category}: {_format_brl(item['total'])}")
        else:
            formatted.append(_display(item))
    return "\n".join(formatted) if formatted else "Sem despesas por categoria"


def _email_template_values(summary: dict[str, object]) -> dict[str, str]:
    period = f"{_format_date(summary.get('start_date'))} a {_format_date(summary.get('end_date'))}"
    categories = summary.get("expenses_by_category")
    category_items = categories if isinstance(categories, (list, tuple)) else []
    category_rows = "".join(
        '<tr><td style="padding:12px 0;border-bottom:1px solid #e8edf5;color:#334155;font-size:14px">'
        f"{escape(_category_label(item.get('category')))}</td>"
        '<td align="right" style="padding:12px 0;border-bottom:1px solid #e8edf5;color:#0f172a;font-size:14px;font-weight:700">'
        f"{escape(_format_brl(item.get('total')))}</td></tr>"
        for item in category_items
        if isinstance(item, dict) and "category" in item and "total" in item
    )
    return {
        "period": escape(period),
        "income_total": escape(_format_brl(summary.get("income_total"))),
        "expense_total": escape(_format_brl(summary.get("expense_total"))),
        "balance": escape(_format_brl(summary.get("balance"))),
        "transaction_count": escape(_display(summary.get("transaction_count", 0))),
        "category_rows": category_rows or (
            '<tr><td colspan="2" style="padding:14px 0;color:#64748b;font-size:14px">'
            "Sem despesas registradas neste período.</td></tr>"
        ),
        "category_text": _format_categories(categories),
    }


def _category_label(value: Any) -> str:
    label = str(value)
    return _CATEGORY_LABELS.get(label.strip().lower(), label.replace("_", " ").capitalize())


def _render_email(summary: dict[str, object]) -> tuple[str, str]:
    values = _email_template_values(summary)
    html_template = (_EMAIL_TEMPLATE_DIRECTORY / "financial-report.html").read_text(encoding="utf-8")
    text_template = (_EMAIL_TEMPLATE_DIRECTORY / "financial-report.txt").read_text(encoding="utf-8")
    return Template(text_template).substitute(values), Template(html_template).substitute(values)


def _make_docx(rows: list[tuple[str, str]]) -> bytes:
    document = Document()
    document.add_heading("Relatório financeiro", level=0)
    document.add_paragraph("Resumo financeiro fornecido pelo assistente.")
    for label, value in rows:
        document.add_heading(label, level=2)
        document.add_paragraph(value)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _make_pdf(rows: list[tuple[str, str]]) -> bytes:
    output = BytesIO()
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("ReportBody", parent=styles["BodyText"], alignment=TA_LEFT, leading=14)
    if "FinanSysVera" not in pdfmetrics.getRegisteredFontNames():
        import reportlab

        pdfmetrics.registerFont(TTFont("FinanSysVera", f"{reportlab.__path__[0]}/fonts/Vera.ttf"))
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], fontName="FinanSysVera")
    normal.fontName = "FinanSysVera"
    story = [Paragraph("Relatório financeiro", title), Spacer(1, 5 * mm)]
    table_data = [[Paragraph("Campo", normal), Paragraph("Valor", normal)]]
    table_data.extend(
        [Paragraph(escape(label), normal), Paragraph(escape(value).replace("\n", "<br/>"), normal)]
        for label, value in rows
    )
    table = Table(table_data, colWidths=[48 * mm, 122 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4D1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    SimpleDocTemplate(output, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm).build(story)
    return output.getvalue()


def generate_financial_report(summary: dict[str, object]) -> list[ReportArtifact]:
    rows = _summary_rows(summary)
    return [
        ReportArtifact("relatorio-financeiro.docx", _DOCX_TYPE, _make_docx(rows)),
        ReportArtifact("relatorio-financeiro.pdf", _PDF_TYPE, _make_pdf(rows)),
    ]


def send_financial_report_email(
    recipient: str,
    summary: dict[str, object],
    artifacts: list[ReportArtifact],
) -> None:
    if not isinstance(recipient, str) or len(recipient) > 254 or not _EMAIL_RE.fullmatch(recipient):
        raise ValueError("Destinatário de email inválido.")
    pdf_artifacts = [artifact for artifact in artifacts if artifact.content_type == _PDF_TYPE]
    if (
        len(pdf_artifacts) != 1
        or not pdf_artifacts[0].filename.lower().endswith(".pdf")
        or not pdf_artifacts[0].content.startswith(b"%PDF-")
    ):
        raise ValueError("O email deve conter exatamente um relatório PDF.")

    message = EmailMessage()
    message["Subject"] = "Seu relatório financeiro está pronto"
    message["From"] = "assistente@finansys.local"
    message["To"] = recipient
    text_body, html_body = _render_email(summary)
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    for artifact in pdf_artifacts:
        message.add_attachment(
            artifact.content,
            maintype="application",
            subtype="pdf",
            filename=artifact.filename,
        )

    with smtplib.SMTP(_MAILPIT_HOST, _MAILPIT_PORT, timeout=10) as smtp:
        smtp.send_message(message)
