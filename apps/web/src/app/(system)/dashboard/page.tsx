"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import ErrorMessage from "../../../components/message/error";
import { getDashboard } from "../../../services/dashboard";
import { ApiError } from "../../../services/goals";
import { TRANSACTION_CATEGORY_LABELS } from "../../../types/transactions";
import type { Dashboard } from "../../../types/dashboard";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function amount(value: string) {
    return Number(value);
}

function categoryLabel(category: string) {
    return TRANSACTION_CATEGORY_LABELS[category as keyof typeof TRANSACTION_CATEGORY_LABELS] ?? category;
}

function formatDate(value: string) {
    return new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR");
}

function formatMonth(value: string) {
    return new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}

export default function DashboardPage() {
    const router = useRouter();
    const [data, setData] = useState<Dashboard | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;
        getDashboard()
            .then((result) => {
                if (active) setData(result);
            })
            .catch((requestError: unknown) => {
                if (!active) return;
                if (requestError instanceof ApiError && requestError.status === 401) {
                    router.replace("/login");
                    return;
                }
                setError("Não foi possível carregar o dashboard.");
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [router]);

    const categoryMax = Math.max(1, ...(data?.expenses_by_category.map((item) => amount(item.total)) ?? []));

    return (
        <main className="mx-auto max-w-6xl space-y-6 p-5 md:p-7">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-slate-800">Dashboard</h1>
                <p className="mt-1 text-sm capitalize text-slate-500">
                    {data ? `Resumo de ${formatMonth(data.month_start)}` : "Resumo do mês"}
                </p>
            </header>

            {error && <ErrorMessage title={error} />}
            {loading && <p className="text-sm text-slate-500">Carregando dashboard...</p>}

            {!loading && !error && data && (
                <>
                    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Resumo financeiro">
                        <SummaryCard label="Saldo total" value={data.summary.balance} tone="neutral" />
                        <SummaryCard label="Entradas do mês" value={data.summary.month_inflow} tone="positive" />
                        <SummaryCard label="Saídas do mês" value={data.summary.month_outflow} tone="negative" />
                        <SummaryCard label="Total guardado em metas" value={data.goals.total_accumulated} tone="neutral" />
                    </section>

                    <section className="grid gap-5 lg:grid-cols-2">
                        <article className="rounded-2xl border border-slate-200 bg-white p-5">
                            <h2 className="font-semibold text-slate-800">Metas</h2>
                            <p className="mt-1 text-sm text-slate-500">
                                {data.goals.done} de {data.goals.total} concluídas · {currency.format(amount(data.goals.total_accumulated))} de {currency.format(amount(data.goals.total_target))}
                            </p>
                            {data.goals.in_progress.length === 0 ? (
                                <p className="py-10 text-center text-sm text-slate-500">Nenhuma meta em andamento.</p>
                            ) : (
                                <div className="mt-6 space-y-4">
                                    {data.goals.in_progress.map((goal) => (
                                        <div key={goal.id}>
                                            <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                                                <span className="truncate text-slate-600">{goal.name}</span>
                                                <strong className="shrink-0 text-slate-800">{goal.percentage}%</strong>
                                            </div>
                                            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                                                <div className="h-full rounded-full bg-blue-700" style={{ width: `${amount(goal.percentage)}%` }} />
                                            </div>
                                            <p className="mt-1 text-xs text-slate-500">
                                                {currency.format(amount(goal.accumulated_value))} de {currency.format(amount(goal.target_value))}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </article>

                        <article className="rounded-2xl border border-slate-200 bg-white p-5">
                            <h2 className="font-semibold text-slate-800">Saídas por categoria</h2>
                            <p className="mt-1 text-sm text-slate-500">Maiores gastos do mês</p>
                            {data.expenses_by_category.length === 0 ? (
                                <p className="py-10 text-center text-sm text-slate-500">Sem saídas neste mês.</p>
                            ) : (
                                <div className="mt-6 space-y-4">
                                    {data.expenses_by_category.map((item) => (
                                        <div key={item.category}>
                                            <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                                                <span className="truncate text-slate-600">{categoryLabel(item.category)}</span>
                                                <strong className="shrink-0 text-slate-800">{currency.format(amount(item.total))}</strong>
                                            </div>
                                            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                                                <div className="h-full rounded-full bg-blue-600" style={{ width: `${(amount(item.total) / categoryMax) * 100}%` }} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </article>
                    </section>

                    <article className="rounded-2xl border border-slate-200 bg-white p-5">
                        <h2 className="font-semibold text-slate-800">Últimas transações</h2>
                        {data.recent_transactions.length === 0 ? (
                            <p className="py-10 text-center text-sm text-slate-500">Nenhuma transação registrada.</p>
                        ) : (
                            <ul className="mt-4 divide-y divide-slate-100">
                                {data.recent_transactions.map((item) => {
                                    const inflow = item.type === "inflow";
                                    return (
                                        <li key={item.id} className="flex items-center justify-between gap-3 py-3">
                                            <div className="min-w-0">
                                                <p className="truncate text-sm font-medium text-slate-800">{categoryLabel(item.category)}</p>
                                                <p className="truncate text-xs text-slate-500">
                                                    {formatDate(item.transaction_date)} · {item.source_money}
                                                </p>
                                            </div>
                                            <strong className={`shrink-0 text-sm ${inflow ? "text-emerald-600" : "text-rose-600"}`}>
                                                {inflow ? "+" : "-"}
                                                {currency.format(amount(item.value))}
                                            </strong>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </article>
                </>
            )}
        </main>
    );
}

function SummaryCard({ label, value, tone }: { label: string; value: string; tone: "positive" | "negative" | "neutral" }) {
    const color = tone === "positive" ? "text-emerald-600" : tone === "negative" ? "text-rose-600" : "text-slate-800";
    return (
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
            <span className="text-sm text-slate-500">{label}</span>
            <strong className={`mt-3 block text-2xl tracking-tight ${color}`}>{currency.format(amount(value))}</strong>
        </article>
    );
}