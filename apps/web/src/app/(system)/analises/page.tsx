"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import ErrorMessage from "../../../components/message/error";
import { ApiError, getFinancialAnalytics } from "../../../services/transactions";
import { TRANSACTION_CATEGORY_LABELS } from "../../../types/transactions";
import type { AnalyticsPeriod, FinancialAnalytics } from "../../../types/analytics";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const axisCurrency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const monthFormatter = new Intl.DateTimeFormat("pt-BR", { month: "short" });
const PERIOD_PRESETS = [
    { id: "1m", label: "1 mês", months: 1 },
    { id: "3m", label: "3 meses", months: 3 },
    { id: "6m", label: "6 meses", months: 6 },
] as const;

type PeriodPreset = (typeof PERIOD_PRESETS)[number]["id"] | "year" | "custom";

function dateInputValue(value: Date) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function subscribeToDate() {
    return () => {};
}

function clientToday() {
    return dateInputValue(new Date());
}

function serverToday() {
    return "";
}

function recentPeriod(todayValue: string): AnalyticsPeriod | null {
    return periodForPreset("6m", todayValue);
}

function periodForPreset(preset: Exclude<PeriodPreset, "custom">, todayValue: string): AnalyticsPeriod | null {
    if (!todayValue) return null;
    const [year, month] = todayValue.split("-").map(Number);
    const selectedPreset = PERIOD_PRESETS.find((item) => item.id === preset);
    const start = preset === "year" ? new Date(year, 0, 1) : new Date(year, month - (selectedPreset?.months ?? 6), 1);
    return { start_date: dateInputValue(start), end_date: todayValue };
}

function formatMonth(value: string) {
    return monthFormatter.format(new Date(`${value}T12:00:00`)).replace(".", "");
}

function amount(value: string) {
    return Number(value);
}

function periodMonthCount(period: AnalyticsPeriod) {
    const [startYear, startMonth] = period.start_date.split("-").map(Number);
    const [endYear, endMonth] = period.end_date.split("-").map(Number);
    return (endYear - startYear) * 12 + endMonth - startMonth + 1;
}

export default function Analises() {
    const router = useRouter();
    const todayValue = useSyncExternalStore(subscribeToDate, clientToday, serverToday);
    const initialPeriod = useMemo(() => recentPeriod(todayValue), [todayValue]);
    const [period, setPeriod] = useState<AnalyticsPeriod | null>(null);
    const [draftPeriod, setDraftPeriod] = useState<AnalyticsPeriod | null>(null);
    const [activePreset, setActivePreset] = useState<PeriodPreset>("6m");
    const [analytics, setAnalytics] = useState<FinancialAnalytics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const activePeriod = period ?? initialPeriod;
    const visiblePeriod = draftPeriod ?? initialPeriod ?? { start_date: "", end_date: "" };

    useEffect(() => {
        if (!activePeriod) return;
        let active = true;
        getFinancialAnalytics(activePeriod)
            .then((result) => {
                if (active) setAnalytics(result);
            })
            .catch((requestError: unknown) => {
                if (!active) return;
                if (requestError instanceof ApiError && requestError.status === 401) {
                    router.replace("/login");
                    return;
                }
                if (requestError instanceof ApiError && requestError.status === 422) {
                    setError(requestError.message);
                    return;
                }
                setError("Não foi possível carregar as análises financeiras.");
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [activePeriod, router]);

    function applyPeriod(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!visiblePeriod.start_date || !visiblePeriod.end_date || visiblePeriod.start_date > visiblePeriod.end_date) {
            setError("Informe um período válido, com a data inicial anterior à data final.");
            return;
        }
        if (periodMonthCount(visiblePeriod) > 120) {
            setError("O período máximo para análise é de 120 meses.");
            return;
        }
        setLoading(true);
        setError(null);
        setActivePreset("custom");
        setPeriod({ ...visiblePeriod });
    }

    function selectPreset(preset: Exclude<PeriodPreset, "custom">) {
        const nextPeriod = periodForPreset(preset, todayValue);
        if (!nextPeriod) return;
        setActivePreset(preset);
        setDraftPeriod(nextPeriod);
        setLoading(true);
        setError(null);
        setPeriod(nextPeriod);
    }

    const monthlyMax = Math.max(
        1,
        ...(analytics?.monthly.flatMap((item) => [amount(item.inflow), amount(item.outflow)]) ?? []),
    );
    const axisTicks = [monthlyMax, monthlyMax * 0.75, monthlyMax * 0.5, monthlyMax * 0.25, 0];
    const categoryMax = Math.max(
        1,
        ...(analytics?.expenses_by_category.map((item) => amount(item.total)) ?? []),
    );

    return (
        <main className="mx-auto max-w-6xl space-y-6 p-5 md:p-7">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-slate-800">Gráficos e análises</h1>
                <p className="mt-1 text-sm text-slate-500">Acompanhe entradas, saídas e a distribuição dos seus gastos.</p>
            </header>

            <form onSubmit={applyPeriod} className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:flex-wrap sm:items-end">
                <div className="flex w-full flex-wrap items-center gap-2" role="group" aria-label="Períodos rápidos">
                    <span className="mr-1 text-sm font-medium text-slate-600">Período:</span>
                    {PERIOD_PRESETS.map((preset) => (
                        <button
                            key={preset.id}
                            type="button"
                            aria-pressed={activePreset === preset.id}
                            onClick={() => selectPreset(preset.id)}
                            className={`rounded-full px-4 py-2 text-sm font-medium ${activePreset === preset.id ? "bg-blue-700 text-white" : "border border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                        >
                            {preset.label}
                        </button>
                    ))}
                    <button
                        type="button"
                        aria-pressed={activePreset === "year"}
                        onClick={() => selectPreset("year")}
                        className={`rounded-full px-4 py-2 text-sm font-medium ${activePreset === "year" ? "bg-blue-700 text-white" : "border border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                    >
                        Esse ano
                    </button>
                </div>
                <label className="flex flex-1 flex-col gap-1 text-sm font-medium text-slate-600">
                    De
                    <input
                        type="date"
                        value={visiblePeriod.start_date}
                        onChange={(event) => {
                            setActivePreset("custom");
                            setDraftPeriod({ ...visiblePeriod, start_date: event.target.value });
                        }}
                        className="h-11 rounded-lg border border-slate-200 px-3 text-slate-800"
                        required
                    />
                </label>
                <label className="flex flex-1 flex-col gap-1 text-sm font-medium text-slate-600">
                    Até
                    <input
                        type="date"
                        value={visiblePeriod.end_date}
                        onChange={(event) => {
                            setActivePreset("custom");
                            setDraftPeriod({ ...visiblePeriod, end_date: event.target.value });
                        }}
                        className="h-11 rounded-lg border border-slate-200 px-3 text-slate-800"
                        required
                    />
                </label>
                <button type="submit" className="h-11 rounded-lg bg-blue-700 px-5 text-sm font-semibold text-white hover:bg-blue-800">
                    Aplicar período
                </button>
            </form>

            {error && <ErrorMessage title={error} />}
            {loading && <p className="text-sm text-slate-500">Carregando análises...</p>}

            {!loading && !error && analytics && (
                <>
                    <section className="grid gap-4 sm:grid-cols-3" aria-label="Resumo financeiro do período">
                        <SummaryCard label="Entradas" value={analytics.total_inflow} tone="positive" />
                        <SummaryCard label="Saídas" value={analytics.total_outflow} tone="negative" />
                        <SummaryCard label="Saldo do período" value={analytics.net_balance} tone="neutral" />
                    </section>

                    <section className="grid gap-5 lg:grid-cols-2">
                        <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5">
                            <h2 className="font-semibold text-slate-800">Entradas e saídas por mês</h2>
                            <p className="mt-1 text-sm text-slate-500">Valores registrados no período selecionado</p>
                            <div className="mt-5 flex gap-4 text-xs text-slate-600" aria-label="Legenda do gráfico">
                                <span className="inline-flex items-center gap-2"><i className="h-3 w-3 rounded-sm bg-emerald-500" />Entradas</span>
                                <span className="inline-flex items-center gap-2"><i className="h-3 w-3 rounded-sm bg-rose-500" />Saídas</span>
                            </div>
                            {analytics.monthly.every((item) => amount(item.inflow) === 0 && amount(item.outflow) === 0) ? (
                                <p className="py-12 text-center text-sm text-slate-500">Sem transações neste período.</p>
                            ) : (
                                <div className="mt-3 overflow-x-auto">
                                    <div className="flex min-w-max items-end gap-3 border-b border-slate-200 px-2 pt-3">
                                        <div className="flex h-40 items-center gap-1" aria-label="Eixo vertical em reais">
                                            <span className="text-[10px] font-medium text-slate-500 [writing-mode:vertical-rl] -rotate-180">Valor (R$)</span>
                                            <div className="flex h-full w-16 shrink-0 flex-col justify-between text-right text-[10px] tabular-nums text-slate-500">
                                                {axisTicks.map((tick, index) => <span key={index}>{axisCurrency.format(tick)}</span>)}
                                            </div>
                                        </div>
                                        <div className="relative flex items-end gap-3">
                                            <div className="pointer-events-none absolute inset-x-0 top-0 flex h-40 flex-col justify-between" aria-hidden="true">
                                                {axisTicks.map((_, index) => <span key={index} className="w-full border-t border-slate-100" />)}
                                            </div>
                                            {analytics.monthly.map((item) => (
                                                <div key={item.month} role="group" className="relative z-10 flex w-12 flex-col items-center gap-2" aria-label={`${formatMonth(item.month)}: entradas ${currency.format(amount(item.inflow))}, saídas ${currency.format(amount(item.outflow))}`}>
                                                    <div className="flex h-40 w-full items-end justify-center gap-1">
                                                        <div className="w-4 rounded-t bg-emerald-500" style={{ height: `${amount(item.inflow) / monthlyMax * 100}%` }} title={`Entradas: ${currency.format(amount(item.inflow))}`} />
                                                        <div className="w-4 rounded-t bg-rose-500" style={{ height: `${amount(item.outflow) / monthlyMax * 100}%` }} title={`Saídas: ${currency.format(amount(item.outflow))}`} />
                                                    </div>
                                                    <span className="pb-2 text-xs capitalize text-slate-500">{formatMonth(item.month)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </article>

                        <article className="rounded-2xl border border-slate-200 bg-white p-5">
                            <h2 className="font-semibold text-slate-800">Saídas por categoria</h2>
                            <p className="mt-1 text-sm text-slate-500">Total gasto em cada categoria no período</p>
                            {analytics.expenses_by_category.length === 0 ? (
                                <p className="py-12 text-center text-sm text-slate-500">Sem saídas neste período.</p>
                            ) : (
                                <div className="mt-6 space-y-4">
                                    {analytics.expenses_by_category.map((item) => (
                                        <div key={item.category}>
                                            <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                                                <span className="truncate text-slate-600">{TRANSACTION_CATEGORY_LABELS[item.category]}</span>
                                                <strong className="shrink-0 text-slate-800">{currency.format(amount(item.total))}</strong>
                                            </div>
                                            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                                                <div className="h-full rounded-full bg-blue-600" style={{ width: `${amount(item.total) / categoryMax * 100}%` }} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </article>
                    </section>
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
