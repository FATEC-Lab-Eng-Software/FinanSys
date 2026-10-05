"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowDownLeft, ArrowUpRight, Bell, ChevronDown, Plus, Search, Trash2 } from "lucide-react";

type Transaction = {
    id: number;
    type: "inflow" | "outflow";
    category: string;
    transaction_date: string;
    value: string;
    source_money: string;
};

const sampleTransactions: Transaction[] = [
    { id: 1, type: "inflow", category: "Salário", transaction_date: "2026-08-06", value: "12500.00", source_money: "Conta Corrente" },
    { id: 2, type: "outflow", category: "Moradia", transaction_date: "2026-08-06", value: "3200.00", source_money: "Conta Corrente" },
    { id: 3, type: "outflow", category: "Alimentação", transaction_date: "2026-08-09", value: "842.35", source_money: "Cartão Nubank" },
    { id: 4, type: "inflow", category: "Freelance", transaction_date: "2026-08-11", value: "3800.00", source_money: "Conta Corrente" },
    { id: 5, type: "outflow", category: "Transporte", transaction_date: "2026-08-13", value: "320.90", source_money: "Cartão Nubank" },
    { id: 6, type: "outflow", category: "Lazer", transaction_date: "2026-08-15", value: "218.40", source_money: "Carteira" },
];

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const date = new Intl.DateTimeFormat("pt-BR");

export default function Home() {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [type, setType] = useState("all");
    const [category, setCategory] = useState("all");
    const [transactions, setTransactions] = useState(sampleTransactions);

    useEffect(() => {
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        fetch(`${apiBase}/transactions`, { credentials: "include" })
            .then(async (response) => {
                if (response.status === 401) {
                    router.replace("/login");
                    return null;
                }
                if (!response.ok) throw new Error("transactions_failed");
                return response.json() as Promise<Transaction[]>;
            })
            .then((items) => { if (items) setTransactions(items); })
            .catch(() => undefined);
    }, [router]);

    const filtered = useMemo(() => transactions.filter((item) => {
        const matchesQuery = `${item.category} ${item.source_money}`.toLowerCase().includes(query.toLowerCase());
        return matchesQuery && (type === "all" || item.type === type) && (category === "all" || item.category === category);
    }), [category, query, transactions, type]);

    const totals = useMemo(() => filtered.reduce((acc, item) => {
        const value = Number(item.value);
        if (item.type === "inflow") acc.inflow += value;
        else acc.outflow += value;
        return acc;
    }, { inflow: 0, outflow: 0 }), [filtered]);

    const remove = (id: number) => setTransactions((items) => items.filter((item) => item.id !== id));

    return (
        <section className="mx-auto max-w-6xl pb-8">
            <div className="mb-7 flex flex-col justify-between gap-5 md:flex-row md:items-start">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-800">Entradas e saídas</h1>
                    <p className="mt-1 text-sm text-slate-400">{filtered.length} lançamentos encontrados</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <label className="flex min-w-56 flex-1 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4"><Search size={17} className="text-slate-400" /><input className="h-10 w-full bg-transparent text-sm outline-none" placeholder="Buscar..." aria-label="Buscar" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
                    <button className="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white" aria-label="Notificações"><Bell size={18} /></button>
                    <div className="flex items-center gap-2"><span className="grid h-10 w-10 place-items-center rounded-full bg-blue-800 text-xs font-bold text-white">VM</span><div><strong className="block text-sm">Vinicius M</strong><small className="block text-xs text-slate-400">Plano Premium</small></div></div>
                </div>
            </div>

            <div className="mb-7 grid gap-4 md:grid-cols-3">
                <SummaryCard label="Entradas filtradas" value={totals.inflow} tone="positive" />
                <SummaryCard label="Saídas filtradas" value={totals.outflow} tone="negative" />
                <SummaryCard label="Resultado" value={totals.inflow - totals.outflow} tone="neutral" />
            </div>

            <div className="mb-6 grid gap-3 md:grid-cols-[minmax(220px,1fr)_180px_200px_180px]">
                <label className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4"><Search size={17} className="text-slate-400" /><input className="h-11 w-full bg-transparent text-sm outline-none" placeholder="Buscar transação..." aria-label="Buscar transação" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
                <Select value={type} onChange={setType} ariaLabel="Filtrar por tipo" options={[["all", "Todos os tipos"], ["inflow", "Entradas"], ["outflow", "Saídas"]]} />
                <Select value={category} onChange={setCategory} ariaLabel="Filtrar por categoria" options={[["all", "Todas as categorias"], ...[...new Set(transactions.map((item) => item.category))].map((item) => [item, item])]} />
                <button className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-blue-700 px-4 text-sm font-semibold text-white hover:bg-blue-800"><Plus size={17} /> Nova transação</button>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white" role="table" aria-label="Transações financeiras">
                {filtered.map((item) => (
                    <div className="grid min-h-20 grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3 border-b border-slate-200 px-4 last:border-0 md:grid-cols-[40px_minmax(220px,1fr)_130px_150px_32px] md:px-5" role="row" key={item.id}>
                        <span className={`grid h-10 w-10 place-items-center rounded-full ${item.type === "inflow" ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`} aria-hidden="true">{item.type === "inflow" ? <ArrowUpRight size={18} /> : <ArrowDownLeft size={18} />}</span>
                        <div><strong className="block text-sm text-slate-800">{item.category === "Freelance" ? "Projeto freelance — landing page" : item.category === "Moradia" ? "Aluguel do apartamento" : item.category === "Alimentação" ? "Supermercado Pão de Açúcar" : item.category === "Transporte" ? "Combustível" : item.category === "Lazer" ? "Cinema e jantar" : "Salário mensal"}</strong><small className="mt-1 block text-xs text-slate-400">{date.format(new Date(`${item.transaction_date}T12:00:00`))} · {item.source_money}</small></div>
                        <span className="hidden justify-self-center rounded-md bg-slate-100 px-3 py-2 text-xs font-bold text-slate-500 md:inline-block">{item.category}</span>
                        <strong className={`col-start-2 text-sm md:col-auto md:text-right ${item.type === "inflow" ? "text-emerald-600" : "text-red-500"}`}>{item.type === "inflow" ? "+" : "-"}{money.format(Number(item.value))}</strong>
                        <button className="col-start-3 row-span-2 grid h-8 w-8 place-items-center rounded-md text-slate-400 hover:bg-red-50 hover:text-red-500 md:col-auto md:row-auto" aria-label={`Excluir ${item.category}`} onClick={() => remove(item.id)}><Trash2 size={16} /></button>
                    </div>
                ))}
                {filtered.length === 0 && <p className="empty-state">Nenhum lançamento encontrado.</p>}
            </div>
        </section>
    );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: "positive" | "negative" | "neutral" }) {
    return <article className="min-h-28 rounded-2xl border border-slate-200 bg-white p-5"><span className="block text-sm text-slate-400">{label}</span><strong className={`mt-3 block text-2xl tracking-tight ${tone === "positive" ? "text-emerald-600" : tone === "negative" ? "text-red-500" : "text-slate-800"}`}>{money.format(value)}</strong></article>;
}

function Select({ value, onChange, options, ariaLabel }: { value: string; onChange: (value: string) => void; options: string[][]; ariaLabel: string }) {
    return <label className="relative flex items-center"><select className="h-11 w-full appearance-none rounded-full border border-slate-200 bg-white px-4 pr-10 text-sm outline-none" aria-label={ariaLabel} value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([option, label]) => <option key={option} value={option}>{label}</option>)}</select><ChevronDown size={16} className="pointer-events-none absolute right-4 text-slate-400" /></label>;
}
