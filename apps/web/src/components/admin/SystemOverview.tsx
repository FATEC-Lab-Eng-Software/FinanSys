"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, UserRound, UserPlus, UsersRound } from "lucide-react";
import { getAdminOverview } from "@/services/admin";
import ActivityOverview from "./ActivityOverview";
import OverviewMetricCard from "./OverviewMetricCard";
import PlatformHealth from "./PlatformHealth";

const numberFormat = new Intl.NumberFormat("pt-BR");

export default function SystemOverview() {
    const overview = useQuery({ queryKey: ["admin-overview"], queryFn: getAdminOverview });
    const data = overview.data;
    const metrics = [
        { label: "Clientes cadastrados", value: data ? numberFormat.format(data.clients_total) : "—", detail: "Contas de cliente", icon: UsersRound, tone: "blue" as const },
        { label: "Clientes ativos", value: data ? numberFormat.format(data.clients_active) : "—", detail: "Com acesso liberado", icon: UserRound, tone: "green" as const },
        { label: "Contas suspensas", value: data ? numberFormat.format(data.clients_suspended) : "—", detail: "Sem acesso ao sistema", icon: Activity, tone: "amber" as const },
        { label: "Novos clientes no mês", value: data ? numberFormat.format(data.clients_created_this_month) : "—", detail: "Desde o início do mês", icon: UserPlus, tone: "violet" as const },
    ];

    return (
        <section className="mx-auto w-full max-w-7xl space-y-6">
            <header>
                <p className="text-sm font-semibold text-blue-700">Painel administrativo</p>
                <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-800 sm:text-3xl">Visão geral do sistema</h1>
                <p className="mt-2 text-sm text-slate-500">Acompanhe os principais indicadores de clientes do FinanSys.</p>
            </header>
            {overview.isError && <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">Não foi possível carregar os indicadores.</p>}
            {overview.isPending && <p className="text-sm text-slate-500" role="status">Carregando indicadores…</p>}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {metrics.map((metric) => <OverviewMetricCard key={metric.label} {...metric} />)}
            </div>
            {data && <div className="grid gap-4 xl:grid-cols-2"><ActivityOverview createdThisMonth={data.clients_created_this_month} active={data.clients_active} suspended={data.clients_suspended} /><PlatformHealth total={data.clients_total} active={data.clients_active} suspended={data.clients_suspended} /></div>}
        </section>
    );
}
