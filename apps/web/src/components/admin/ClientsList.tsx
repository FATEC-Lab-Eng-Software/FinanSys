import { UserRound } from "lucide-react";
import type { AdminClient } from "@/types/admin";

type ClientsListProps = {
    clients: AdminClient[];
    busyClientId: string | null;
    onToggleStatus: (client: AdminClient) => void;
};

function clientName(client: AdminClient) {
    return [client.first_name, client.last_name].filter(Boolean).join(" ") || "Nome não informado";
}

function formatDate(value: string | null) {
    if (!value) return "Nunca";
    return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(new Date(value));
}

export default function ClientsList({ clients, busyClientId, onToggleStatus }: ClientsListProps) {
    if (clients.length === 0) return <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center text-sm text-slate-500">Nenhum cliente encontrado com esses filtros.</div>;

    return (
        <div className="grid gap-3">
            {clients.map((client) => (
                <article key={client.id} className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:p-5">
                    <div className="flex min-w-0 items-start gap-3">
                        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-700"><UserRound size={19} aria-hidden="true" /></span>
                        <div className="min-w-0 flex-1">
                            <h2 className="truncate font-semibold text-slate-800">{clientName(client)}</h2>
                            <p className="mt-1 break-all text-sm text-slate-500">{client.email}</p>
                            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                                <span className={`rounded-full px-2.5 py-1 font-medium ${client.is_active ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{client.is_active ? "Ativa" : "Suspensa"}</span>
                                <span>Cadastro: {formatDate(client.created_at)}</span>
                                <span>Último acesso: {formatDate(client.last_access_at)}</span>
                            </div>
                        </div>
                    </div>
                    <button type="button" disabled={busyClientId === client.id} onClick={() => onToggleStatus(client)} className={`h-10 rounded-xl px-4 text-sm font-semibold transition-colors disabled:cursor-wait disabled:opacity-60 ${client.is_active ? "border border-amber-200 text-amber-800 hover:bg-amber-50" : "bg-blue-700 text-white hover:bg-blue-800"}`}>
                        {busyClientId === client.id ? "Salvando…" : client.is_active ? "Suspender conta" : "Reativar conta"}
                    </button>
                </article>
            ))}
        </div>
    );
}
