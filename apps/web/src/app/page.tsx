"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ArrowDownLeft, ArrowUpRight, ChevronDown, Pencil, Plus, Search, Trash2, WalletCards } from "lucide-react";

type Transaction = {
    id: number;
    type: "inflow" | "outflow";
    category: string;
    transaction_date: string;
    value: string;
    source_money: string;
};

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const date = new Intl.DateTimeFormat("pt-BR");
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [type, setType] = useState("all");
    const [category, setCategory] = useState("all");
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({ type: "outflow", category: "other", transaction_date: new Date().toISOString().slice(0, 10), value: "", source_money: "" });

    useEffect(() => {
        fetch(`${API_BASE_URL}/transactions`, { credentials: "include" })
            .then(async (response) => {
                if (response.status === 401) {
                    router.replace("/login");
                    return null;
                }
                if (!response.ok) throw new Error("transactions_failed");
                return response.json() as Promise<Transaction[]>;
            })
            .then((items) => { if (items) setTransactions(items); })
            .catch(() => setTransactions([]));
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

    const remove = async (id: number) => {
        const response = await fetch(`${API_BASE_URL}/transactions/${id}`, { method: "DELETE", credentials: "include" });
        if (response.ok) setTransactions((items) => items.filter((item) => item.id !== id));
    };

    const saveTransaction = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSaving(true);
        try {
            const method = editingId === null ? "POST" : "PATCH";
            const endpoint = editingId === null ? `${API_BASE_URL}/transactions` : `${API_BASE_URL}/transactions/${editingId}`;
            const response = await fetch(endpoint, { method, credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, value: form.value.replace(",", ".") }) });
            if (!response.ok) return;
            const saved = await response.json() as Transaction;
            setTransactions((items) => editingId === null ? [saved, ...items] : items.map((item) => item.id === saved.id ? saved : item));
            setForm({ type: "outflow", category: "other", transaction_date: new Date().toISOString().slice(0, 10), value: "", source_money: "" });
            setEditingId(null);
            setShowForm(false);
        } finally {
            setSaving(false);
        }
    };

    const edit = (item: Transaction) => {
        setEditingId(item.id);
        setForm({ type: item.type, category: item.category, transaction_date: item.transaction_date, value: item.value, source_money: item.source_money });
        setShowForm(true);
    };

    const openNew = () => {
        setEditingId(null);
        setForm({ type: "outflow", category: "other", transaction_date: new Date().toISOString().slice(0, 10), value: "", source_money: "" });
        setShowForm(true);
    };

    return (
        <section className="mx-auto max-w-6xl pb-8">
            <div className="mb-7 flex flex-col justify-between gap-5 md:flex-row md:items-start">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-800">Entradas e saídas</h1>
                    <p className="mt-1 text-sm text-slate-400">{filtered.length} lançamentos encontrados</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <label className="flex min-w-56 flex-1 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4"><Search size={17} className="text-slate-400" /><input className="h-10 w-full bg-transparent text-sm outline-none" placeholder="Buscar..." aria-label="Buscar" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
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
                <button type="button" onClick={openNew} className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-blue-700 px-4 text-sm font-semibold text-white hover:bg-blue-800"><Plus size={17} /> Nova transação</button>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white" role="table" aria-label="Transações financeiras">
                {filtered.map((item) => (
                    <div className="grid min-h-20 grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3 border-b border-slate-200 px-4 last:border-0 md:grid-cols-[40px_minmax(220px,1fr)_130px_150px_32px] md:px-5" role="row" key={item.id}>
                        <span className={`grid h-10 w-10 place-items-center rounded-full ${item.type === "inflow" ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`} aria-hidden="true">{item.type === "inflow" ? <ArrowUpRight size={18} /> : <ArrowDownLeft size={18} />}</span>
                        <div><strong className="block text-sm text-slate-800">{item.category === "Freelance" ? "Projeto freelance — landing page" : item.category === "Moradia" ? "Aluguel do apartamento" : item.category === "Alimentação" ? "Supermercado Pão de Açúcar" : item.category === "Transporte" ? "Combustível" : item.category === "Lazer" ? "Cinema e jantar" : "Salário mensal"}</strong><small className="mt-1 block text-xs text-slate-400">{date.format(new Date(`${item.transaction_date}T12:00:00`))} · {item.source_money}</small></div>
                        <span className="hidden justify-self-center rounded-md bg-slate-100 px-3 py-2 text-xs font-bold text-slate-500 md:inline-block">{item.category}</span>
                        <strong className={`col-start-2 text-sm md:col-auto md:text-right ${item.type === "inflow" ? "text-emerald-600" : "text-red-500"}`}>{item.type === "inflow" ? "+" : "-"}{money.format(Number(item.value))}</strong>
                        <div className="col-start-3 row-span-2 flex gap-1 md:col-auto md:row-auto"><button className="grid h-8 w-8 place-items-center rounded-md text-slate-400 hover:bg-blue-50 hover:text-blue-600" aria-label={`Editar ${item.category}`} onClick={() => edit(item)}><Pencil size={15} /></button><button className="grid h-8 w-8 place-items-center rounded-md text-slate-400 hover:bg-red-50 hover:text-red-500" aria-label={`Excluir ${item.category}`} onClick={() => void remove(item.id)}><Trash2 size={16} /></button></div>
                    </div>
                ))}
                {filtered.length === 0 && (
                    <div className="flex min-h-64 flex-col items-center justify-center px-6 py-12 text-center">
                        <span className="mb-4 grid h-16 w-16 place-items-center rounded-full bg-blue-50 text-blue-700"><WalletCards size={30} strokeWidth={1.8} /></span>
                        <h2 className="text-lg font-semibold text-slate-800">Nenhum lançamento encontrado</h2>
                        <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">Suas entradas e saídas aparecerão aqui. Comece adicionando sua primeira transação.</p>
                        <button onClick={openNew} className="mt-5 inline-flex h-10 items-center gap-2 rounded-full bg-blue-700 px-5 text-sm font-semibold text-white hover:bg-blue-800"><Plus size={16} /> Adicionar lançamento</button>
                    </div>
                )}
            </div>
            {showForm && <TransactionForm form={form} editing={editingId !== null} saving={saving} onChange={(field, value) => setForm((current) => ({ ...current, [field]: value }))} onSubmit={saveTransaction} onClose={() => { setShowForm(false); setEditingId(null); }} />}
        </section>
    );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: "positive" | "negative" | "neutral" }) {
    return <article className="min-h-28 rounded-2xl border border-slate-200 bg-white p-5"><span className="block text-sm text-slate-400">{label}</span><strong className={`mt-3 block text-2xl tracking-tight ${tone === "positive" ? "text-emerald-600" : tone === "negative" ? "text-red-500" : "text-slate-800"}`}>{money.format(value)}</strong></article>;
}

function Select({ value, onChange, options, ariaLabel }: { value: string; onChange: (value: string) => void; options: string[][]; ariaLabel: string }) {
    return <label className="relative flex items-center"><select className="h-11 w-full appearance-none rounded-full border border-slate-200 bg-white px-4 pr-10 text-sm outline-none" aria-label={ariaLabel} value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([option, label]) => <option key={option} value={option}>{label}</option>)}</select><ChevronDown size={16} className="pointer-events-none absolute right-4 text-slate-400" /></label>;
}

function TransactionForm({ form, editing, saving, onChange, onSubmit, onClose }: { form: Record<string, string>; editing: boolean; saving: boolean; onChange: (field: string, value: string) => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onClose: () => void }) {
    return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4"><form onSubmit={onSubmit} className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl"><div className="mb-5 flex items-center justify-between"><h2 className="text-xl font-semibold text-slate-800">{editing ? "Editar transação" : "Nova transação"}</h2><button type="button" onClick={onClose} className="text-slate-400">×</button></div><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm text-slate-600">Tipo<select required value={form.type} onChange={(event) => onChange("type", event.target.value)} className="mt-1 h-11 w-full rounded-lg border border-slate-200 px-3"><option value="outflow">Saída</option><option value="inflow">Entrada</option></select></label><label className="text-sm text-slate-600">Categoria<select required value={form.category} onChange={(event) => onChange("category", event.target.value)} className="mt-1 h-11 w-full rounded-lg border border-slate-200 px-3"><option value="other">Outros</option><option value="work">Trabalho</option><option value="housing">Moradia</option><option value="food">Alimentação</option><option value="transportation">Transporte</option></select></label><label className="text-sm text-slate-600">Data<input required type="date" value={form.transaction_date} onChange={(event) => onChange("transaction_date", event.target.value)} className="mt-1 h-11 w-full rounded-lg border border-slate-200 px-3" /></label><label className="text-sm text-slate-600">Valor<input required min="0.01" step="0.01" type="number" value={form.value} onChange={(event) => onChange("value", event.target.value)} className="mt-1 h-11 w-full rounded-lg border border-slate-200 px-3" /></label><label className="text-sm text-slate-600 sm:col-span-2">Origem do dinheiro<input required value={form.source_money} onChange={(event) => onChange("source_money", event.target.value)} placeholder="Conta corrente, cartão..." className="mt-1 h-11 w-full rounded-lg border border-slate-200 px-3" /></label></div><div className="mt-6 flex justify-end gap-3"><button type="button" onClick={onClose} className="rounded-full px-4 py-2 text-sm text-slate-600">Cancelar</button><button disabled={saving} className="rounded-full bg-blue-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-60">{saving ? "Salvando..." : editing ? "Salvar alterações" : "Salvar lançamento"}</button></div></form></div>;
}
