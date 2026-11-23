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
from typing import Any

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
    "monthly_expenses": "Gastos por mês",
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
        elif key == "monthly_expenses":
            display = _format_monthly_expenses(value)
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


def _format_monthly_expenses(value: Any) -> str:
    if not isinstance(value, (list, tuple)):
        return _display(value)
    month_names = (
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    )
    formatted: list[str] = []
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("month"), str) or "total" not in item:
            formatted.append(_display(item))
            continue
        try:
            month = date.fromisoformat(f"{item['month']}-01")
        except ValueError:
            formatted.append(_display(item))
            continue
        month_label = f"{month_names[month.month - 1].capitalize()} de {month.year}"
        formatted.append(f"{month_label}: {_format_brl(item['total'])}")
    return "\n".join(formatted) if formatted else "Sem gastos no período"


def _render_email() -> tuple[str, str]:
    html_template = (_EMAIL_TEMPLATE_DIRECTORY / "financial-report.html").read_text(encoding="utf-8")
    text_template = (_EMAIL_TEMPLATE_DIRECTORY / "financial-report.txt").read_text(encoding="utf-8")
    return text_template, html_template


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
    return [ReportArtifact("relatorio-financeiro.pdf", _PDF_TYPE, _make_pdf(rows))]


def send_financial_report_email(
    recipient: str,
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
    text_body, html_body = _render_email()
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
