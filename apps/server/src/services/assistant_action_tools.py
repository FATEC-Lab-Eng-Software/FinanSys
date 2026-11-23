from __future__ import annotations

from typing import Any

from src.services.assistant_reports import (
    ReportArtifact,
    generate_financial_report,
    send_financial_report_email,
)
from src.services.assistant_tools import (
    AssistantTool,
    AssistantToolContext,
    AuditToolDecorator,
    AuthenticatedUserScopeDecorator,
    ToolDecorator,
)


class _ReportTool:
    name = "gerar_relatorio_financeiro"
    arguments_schema = {
        "type": "object",
        "properties": {"summary": {"type": "object"}},
        "required": ["summary"],
        "additionalProperties": False,
    }

    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        summary = _summary_argument(arguments, {"summary"})
        artifacts: list[ReportArtifact] = generate_financial_report(summary)
        return {"summary": summary, "_artifacts": artifacts}


class _SendReportEmailTool:
    name = "enviar_relatorio_email"
    arguments_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "object"},
            "recipient": {"type": "string", "format": "email"},
        },
        "required": ["summary", "recipient"],
        "additionalProperties": False,
    }

    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        summary = _summary_argument(arguments, {"summary", "recipient"})
        recipient = arguments["recipient"]
        if not isinstance(recipient, str):
            raise ValueError("Destinatário de email inválido.")
        artifacts: list[ReportArtifact] = generate_financial_report(summary)
        send_financial_report_email(recipient, artifacts)
        return {
            "summary": summary,
            "_artifacts": artifacts,
            "email_sent": True,
            "recipient": recipient,
            "delivery": "Mailpit local",
        }


def _summary_argument(arguments: dict[str, Any], expected_keys: set[str]) -> dict[str, object]:
    if not isinstance(arguments, dict) or set(arguments) != expected_keys:
        raise ValueError("Argumentos inválidos para a ferramenta de relatório.")
    summary = arguments["summary"]
    if not isinstance(summary, dict):
        raise ValueError("summary deve ser um objeto.")
    return summary


def _decorate(tool: AssistantTool) -> AssistantTool:
    return AuditToolDecorator(AuthenticatedUserScopeDecorator(ToolDecorator(tool)))


def build_assistant_action_tools() -> dict[str, AssistantTool]:
    tools: list[AssistantTool] = [_decorate(_ReportTool()), _decorate(_SendReportEmailTool())]
    return {tool.name: tool for tool in tools}
