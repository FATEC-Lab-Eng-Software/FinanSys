"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listAdminClients, updateAdminClientStatus } from "@/services/admin";
import type { AdminClient } from "@/types/admin";
import ClientsList from "./ClientsList";
import ClientsToolbar from "./ClientsToolbar";

export default function AdminClientsPanel() {
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("all");
    const [page, setPage] = useState(1);
    const queryClient = useQueryClient();
    const queryKey = ["admin-clients", search, status, page];
    const clientsQuery = useQuery({ queryKey, queryFn: () => listAdminClients(search, status, page) });
    const statusMutation = useMutation({
        mutationFn: (client: AdminClient) => updateAdminClientStatus(client.id, !client.is_active),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-clients"] });
            queryClient.invalidateQueries({ queryKey: ["admin-overview"] });
        },
    });

    return (
        <section className="mx-auto w-full max-w-7xl space-y-5">
            <header>
                <p className="text-sm font-semibold text-blue-700">Administração</p>
                <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-800 sm:text-3xl">Gerenciamento de clientes</h1>
                <p className="mt-2 text-sm text-slate-500">Consulte contas e controle o acesso dos clientes.</p>
            </header>
            <ClientsToolbar search={search} status={status} onSearchChange={(value) => { setSearch(value); setPage(1); }} onStatusChange={(value) => { setStatus(value); setPage(1); }} />
            {clientsQuery.isPending && <div className="rounded-2xl bg-white px-5 py-10 text-center text-sm text-slate-500" role="status">Carregando clientes…</div>}
            {clientsQuery.isError && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">Não foi possível carregar os clientes. Tente novamente.</div>}
            {statusMutation.isError && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">Não foi possível atualizar a conta. Tente novamente.</div>}
            {clientsQuery.data && <ClientsList clients={clientsQuery.data.items} busyClientId={statusMutation.isPending ? statusMutation.variables.id : null} onToggleStatus={(client) => statusMutation.mutate(client)} />}
            <div className="flex items-center justify-between gap-3">
                <button type="button" disabled={page <= 1 || clientsQuery.isFetching} onClick={() => setPage((current) => current - 1)} className="h-10 rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 disabled:opacity-40">Anterior</button>
                <span className="text-sm text-slate-500">Página {page}</span>
                <button type="button" disabled={!clientsQuery.data?.has_more || clientsQuery.isFetching} onClick={() => setPage((current) => current + 1)} className="h-10 rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 disabled:opacity-40">Próxima</button>
            </div>
        </section>
    );
}
