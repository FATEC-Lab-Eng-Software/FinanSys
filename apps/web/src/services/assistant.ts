import type { AssistantChatResponse, AssistantMessage } from "../types/assistant";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class AssistantApiError extends Error {
    readonly status: number;
    readonly code: string;

    constructor(status: number, code: string, message: string) {
        super(message);
        this.name = "AssistantApiError";
        this.status = status;
        this.code = code;
    }
}

async function readError(response: Response): Promise<AssistantApiError> {
    try {
        const body = await response.json();
        const detail = body?.detail;
        if (typeof detail?.message === "string") {
            return new AssistantApiError(response.status, String(detail.code ?? "request_failed"), detail.message);
        }
    } catch {
        return new AssistantApiError(response.status, "request_failed", "Não foi possível enviar a mensagem.");
    }
    return new AssistantApiError(response.status, "request_failed", "Não foi possível enviar a mensagem.");
}

export async function sendAssistantMessage(messages: AssistantMessage[]): Promise<AssistantChatResponse> {
    const response = await fetch(`${API_BASE_URL}/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ messages: messages.map(({ role, content }) => ({ role, content })) }),
    });
    if (!response.ok) throw await readError(response);
    return response.json() as Promise<AssistantChatResponse>;
}
