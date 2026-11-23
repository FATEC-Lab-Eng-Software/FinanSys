"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Bot, LoaderCircle, Send } from "lucide-react";

import Card from "../../../components/ui/Card";
import { AssistantApiError, sendAssistantMessage } from "../../../services/assistant";
import type { AssistantMessage } from "../../../types/assistant";

const MAX_MESSAGES = 20;
const INTRO_MESSAGE: AssistantMessage = {
    role: "assistant",
    content: "Oi! Como posso te ajudar hoje?",
};

function Assistente() {
    const router = useRouter();
    const [messages, setMessages] = useState<AssistantMessage[]>([INTRO_MESSAGE]);
    const [draft, setDraft] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }, [messages, sending]);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const content = draft.trim();
        if (!content || sending) return;

        const nextMessages = [...messages, { role: "user" as const, content }].slice(-MAX_MESSAGES);
        setMessages(nextMessages);
        setDraft("");
        setError(null);
        setSending(true);

        try {
            const response = await sendAssistantMessage(nextMessages);
            const assistantMessage: AssistantMessage = { role: "assistant", content: response.message };
            setMessages((current) => [...current, assistantMessage].slice(-MAX_MESSAGES));
        } catch (requestError) {
            if (requestError instanceof AssistantApiError && requestError.status === 401) {
                router.replace("/login");
                return;
            }
            setError(requestError instanceof Error ? requestError.message : "Não foi possível enviar a mensagem.");
        } finally {
            setSending(false);
        }
    }

    return (
        <main className="mx-auto flex h-[calc(100vh-2rem)] w-full max-w-5xl flex-col gap-5 p-4 md:h-[calc(100vh-3rem)] md:p-8">
            <header>
                <div className="flex items-center gap-3">
                    <span className="grid h-11 w-11 place-items-center rounded-xl bg-secondary/10 text-secondary">
                        <Bot size={23} />
                    </span>
                    <div>
                        <h1 className="text-2xl font-bold text-text">Assistente FinanSys</h1>
                        <p className="text-sm text-text/60">Conectado ao agente Hermes</p>
                    </div>
                </div>
            </header>

            <Card className="min-h-0 flex-1 gap-0 overflow-hidden border border-slate-200 p-0">
                <div className="flex-1 space-y-4 overflow-y-auto p-4 md:p-6" aria-live="polite" aria-label="Conversa com o assistente">
                    {messages.map((message, index) => (
                        <div key={`${index}-${message.role}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 md:max-w-[75%] ${message.role === "user" ? "rounded-br-md bg-secondary text-white" : "rounded-bl-md bg-slate-100 text-slate-800"}`}>
                                <p className="whitespace-pre-wrap">{message.content}</p>
                            </div>
                        </div>
                    ))}
                    {sending && (
                        <div className="flex items-center gap-2 text-sm text-text/60" role="status">
                            <LoaderCircle size={16} className="animate-spin" />
                            O assistente está respondendo…
                        </div>
                    )}
                    {error && <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">{error}</p>}
                    <div ref={bottomRef} />
                </div>

                <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white p-3 md:p-4">
                    <label htmlFor="assistant-message" className="sr-only">Escreva uma mensagem</label>
                    <div className="flex items-end gap-3">
                        <textarea
                            id="assistant-message"
                            value={draft}
                            onChange={(event) => setDraft(event.target.value)}
                            onKeyDown={(event) => {
                                if (event.key === "Enter" && !event.shiftKey) {
                                    event.preventDefault();
                                    event.currentTarget.form?.requestSubmit();
                                }
                            }}
                            maxLength={4000}
                            rows={2}
                            placeholder="Escreva sua mensagem…"
                            disabled={sending}
                            className="max-h-40 min-h-12 flex-1 resize-y rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:bg-slate-50"
                        />
                        <button
                            type="submit"
                            disabled={sending || !draft.trim()}
                            aria-label="Enviar mensagem"
                            className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-secondary text-white transition hover:bg-secondary/90 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <Send size={18} />
                        </button>
                    </div>
                    <p className="mt-2 text-xs text-text/50">Enter envia · Shift + Enter quebra a linha</p>
                </form>
            </Card>
        </main>
    );
}

export default Assistente;
