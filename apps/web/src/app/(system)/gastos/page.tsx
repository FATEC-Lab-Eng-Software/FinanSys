"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ArrowDownLeft, ArrowUpRight, ChevronDown, Plus, Search, Trash2, X } from "lucide-react";

import Card from "../../../components/ui/Card";
import Form from "../../../components/ui/Form";
import Modal from "../../../components/ui/Modal";
import ErrorMessage from "../../../components/message/error";
import { ApiError, createTransaction, deleteTransaction, listTransactions } from "../../../services/transactions";
import { TRANSACTION_CATEGORY_LABELS, TRANSACTION_TYPE_LABELS } from "../../../types/transactions";
import type { Transaction, TransactionCategory, TransactionFilters, TransactionType } from "../../../types/transactions";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const date = new Intl.DateTimeFormat("pt-BR");
const CATEGORIES = Object.entries(TRANSACTION_CATEGORY_LABELS) as [TransactionCategory, string][];
const TYPES = Object.entries(TRANSACTION_TYPE_LABELS) as [TransactionType, string][];
const TRANSACTIONS_LIMIT = 200;
const TOAST_DURATION = 5000;

function today() {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function toAmount(value: string) {
    const normalized = value.includes(",") ? value.replace(/\./g, "").replace(",", ".") : value;
    return Number(normalized).toFixed(2);
}

function emptyForm() {
    return {
        type: "outflow" as TransactionType,
        category: "other" as TransactionCategory,
        transactionDate: today(),
        value: "",
        sourceMoney: "",
    };
}

export default function Gastos() {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [type, setType] = useState<TransactionType | "all">("all");
    const [category, setCategory] = useState<TransactionCategory | "all">("all");
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState(emptyForm);
    const [saving, setSaving] = useState(false);
    const [reloadKey, setReloadKey] = useState(0);

    const handleUnauthorized = useCallback(
        (error: unknown) => {
            if (error instanceof ApiError && error.status === 401) {
                router.replace("/login");
                return true;
            }
            return false;
        },
        [router],
    );

    useEffect(() => {
        let active = true;
        const filters: TransactionFilters = { limit: TRANSACTIONS_LIMIT };
        if (type !== "all") filters.type = type;
        if (category !== "all") filters.category = category;
        listTransactions(filters)
            .then((items) => {
                if (!active) return;
                setTransactions(items);
                setLoadError(false);
            })
            .catch((error) => {
                if (active && !handleUnauthorized(error)) setLoadError(true);
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [category, handleUnauthorized, reloadKey, type]);

    useEffect(() => {
        if (!actionError) return;
        const timer = setTimeout(() => setActionError(null), TOAST_DURATION);
        return () => clearTimeout(timer);
    }, [actionError]);

    const filtered = useMemo(() => {
        const search = query.trim().toLowerCase();
        if (!search) return transactions;
        return transactions.filter((item) =>
            `${TRANSACTION_CATEGORY_LABELS[item.category]} ${item.source_money}`.toLowerCase().includes(search),
        );
    }, [query, transactions]);

    const totals = useMemo(() => filtered.reduce((acc, item) => {
        const value = Number(item.value);
        if (item.type === "inflow") acc.inflow += value;
        else acc.outflow += value;
        return acc;
    }, { inflow: 0, outflow: 0 }), [filtered]);

    const closeForm = useCallback(() => {
        setShowForm(false);
        setForm(emptyForm());
    }, []);

    function openCreate() {
        setForm(emptyForm());
        setShowForm(true);
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setActionError(null);
        try {
            await createTransaction({
                type: form.type,
                category: form.category,
                transaction_date: form.transactionDate,
                value: toAmount(form.value),
                source_money: form.sourceMoney.trim(),
            });
            closeForm();
            setReloadKey((key) => key + 1);
        } catch (error) {
            if (!handleUnauthorized(error)) setActionError("Não foi possível criar a transação.");
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(item: Transaction) {
        if (!window.confirm(`Excluir a transação de ${TRANSACTION_CATEGORY_LABELS[item.category]}?`)) return;
        setActionError(null);
        try {
            await deleteTransaction(item.id);
            setReloadKey((key) => key + 1);
        } catch (error) {
            if (!handleUnauthorized(error)) setActionError("Não foi possível excluir a transação.");
        }
    }

    return (
        <section className="mx-auto max-w-6xl p-6">
            <div className="mb-7 flex flex-col justify-between gap-5 md:flex-row md:items-start">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-800">Entradas e saídas</h1>
                    <p className="mt-1 text-sm text-slate-400">{filtered.length} lançamentos encontrados</p>
                </div>
            </div>

            <div className="mb-7 grid gap-4 md:grid-cols-3">
                <SummaryCard label="Entradas filtradas" value={totals.inflow} tone="positive" />
                <SummaryCard label="Saídas filtradas" value={totals.outflow} tone="negative" />
                <SummaryCard label="Resultado" value={totals.inflow - totals.outflow} tone="neutral" />
            </div>

            <div className="mb-6 grid gap-3 md:grid-cols-[minmax(220px,1fr)_180px_200px_180px]">
                <label className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4"><Search size={17} className="text-slate-400" /><input className="h-11 w-full bg-transparent text-sm outline-none" placeholder="Buscar transação..." aria-label="Buscar transação" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
                <Select value={type} onChange={(value) => setType(value as TransactionType | "all")} ariaLabel="Filtrar por tipo" options={[["all", "Todos os tipos"], ["inflow", "Entradas"], ["outflow", "Saídas"]]} />
                <Select value={category} onChange={(value) => setCategory(value as TransactionCategory | "all")} ariaLabel="Filtrar por categoria" options={[["all", "Todas as categorias"], ...CATEGORIES]} />
                <button type="button" onClick={openCreate} className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-blue-700 px-4 text-sm font-semibold text-white hover:bg-blue-800"><Plus size={17} /> Nova transação</button>
            </div>

            <Modal open={showForm} onClose={closeForm} labelledBy="transaction-form-title">
                <Card>
                    <Card.Header>
                        <h3 id="transaction-form-title" className="font-semibold">Nova transação</h3>
                        <button type="button" onClick={closeForm} aria-label="Fechar" className="text-gray-500">
                            <X size={20} />
                        </button>
                    </Card.Header>
                    <Card.Body>
                        <Form id="transaction-form" onSubmit={handleSubmit}>
                            <Form.Field>
                                <Form.Label htmlFor="transaction-type">Tipo</Form.Label>
                                <Form.Select
                                    id="transaction-type"
                                    value={form.type}
                                    onChange={(event) => setForm({ ...form, type: event.target.value as TransactionType })}
                                >
                                    {TYPES.map(([value, label]) => (
                                        <option key={value} value={value}>
                                            {label}
                                        </option>
                                    ))}
                                </Form.Select>
                            </Form.Field>
                            <Form.Field>
                                <Form.Label htmlFor="transaction-category">Categoria</Form.Label>
                                <Form.Select
                                    id="transaction-category"
                                    value={form.category}
                                    onChange={(event) =>
                                        setForm({ ...form, category: event.target.value as TransactionCategory })
                                    }
                                >
                                    {CATEGORIES.map(([value, label]) => (
                                        <option key={value} value={value}>
                                            {label}
                                        </option>
                                    ))}
                                </Form.Select>
                            </Form.Field>
                            <Form.Field>
                                <Form.Label htmlFor="transaction-value">Valor</Form.Label>
                                <Form.Input
                                    id="transaction-value"
                                    value={form.value}
                                    onChange={(event) => setForm({ ...form, value: event.target.value })}
                                    placeholder="150,00"
                                    inputMode="decimal"
                                    required
                                />
                            </Form.Field>
                            <Form.Field>
                                <Form.Label htmlFor="transaction-date">Data</Form.Label>
                                <Form.Input
                                    id="transaction-date"
                                    type="date"
                                    value={form.transactionDate}
                                    onChange={(event) => setForm({ ...form, transactionDate: event.target.value })}
                                    required
                                />
                            </Form.Field>
                            <Form.Field>
                                <Form.Label htmlFor="transaction-source">Origem do dinheiro</Form.Label>
                                <Form.Input
                                    id="transaction-source"
                                    value={form.sourceMoney}
                                    onChange={(event) => setForm({ ...form, sourceMoney: event.target.value })}
                                    placeholder="Conta corrente"
                                    maxLength={100}
                                    required
                                />
                            </Form.Field>
                        </Form>
                    </Card.Body>
                    <Card.Footer className="justify-end">
                        <button
                            type="button"
                            onClick={closeForm}
                            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            form="transaction-form"
                            disabled={saving}
                            className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                        >
                            {saving ? "Salvando..." : "Salvar transação"}
                        </button>
                    </Card.Footer>
                </Card>
            </Modal>

            {loading && <p className="text-sm text-gray-500">Carregando transações...</p>}
            {loadError && <ErrorMessage title="Não foi possível carregar as transações." />}

            {!loading && !loadError && (
                <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white" role="table" aria-label="Transações financeiras">
                    {filtered.map((item) => (
                        <div className="grid min-h-20 grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3 border-b border-slate-200 px-4 last:border-0 md:grid-cols-[40px_minmax(220px,1fr)_130px_150px_32px] md:px-5" role="row" key={item.id}>
                            <span className={`grid h-10 w-10 place-items-center rounded-full ${item.type === "inflow" ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`} aria-hidden="true">{item.type === "inflow" ? <ArrowUpRight size={18} /> : <ArrowDownLeft size={18} />}</span>
                            <div><strong className="block text-sm text-slate-800">{item.source_money}</strong><small className="mt-1 block text-xs text-slate-400">{date.format(new Date(`${item.transaction_date}T12:00:00`))} · {TRANSACTION_TYPE_LABELS[item.type]}</small></div>
                            <span className="hidden justify-self-center rounded-md bg-slate-100 px-3 py-2 text-xs font-bold text-slate-500 md:inline-block">{TRANSACTION_CATEGORY_LABELS[item.category]}</span>
                            <strong className={`col-start-2 text-sm md:col-auto md:text-right ${item.type === "inflow" ? "text-emerald-600" : "text-red-500"}`}>{item.type === "inflow" ? "+" : "-"}{money.format(Number(item.value))}</strong>
                            <button type="button" className="col-start-3 row-span-2 grid h-8 w-8 place-items-center rounded-md text-slate-400 hover:bg-red-50 hover:text-red-500 md:col-auto md:row-auto" aria-label={`Excluir ${TRANSACTION_CATEGORY_LABELS[item.category]}`} onClick={() => handleDelete(item)}><Trash2 size={16} /></button>
                        </div>
                    ))}
                    {filtered.length === 0 && <p className="p-5 text-sm text-gray-500">Nenhum lançamento encontrado.</p>}
                </div>
            )}

            {actionError && (
                <div role="alert" className="fixed bottom-6 right-6 z-[60] max-w-sm">
                    <ErrorMessage title={actionError} />
                </div>
            )}
        </section>
    );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: "positive" | "negative" | "neutral" }) {
    return <article className="min-h-28 rounded-2xl border border-slate-200 bg-white p-5"><span className="block text-sm text-slate-400">{label}</span><strong className={`mt-3 block text-2xl tracking-tight ${tone === "positive" ? "text-emerald-600" : tone === "negative" ? "text-red-500" : "text-slate-800"}`}>{money.format(value)}</strong></article>;
}

function Select({ value, onChange, options, ariaLabel }: { value: string; onChange: (value: string) => void; options: string[][]; ariaLabel: string }) {
    return <label className="relative flex items-center"><select className="h-11 w-full appearance-none rounded-full border border-slate-200 bg-white px-4 pr-10 text-sm outline-none" aria-label={ariaLabel} value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([option, label]) => <option key={option} value={option}>{label}</option>)}</select><ChevronDown size={16} className="pointer-events-none absolute right-4 text-slate-400" /></label>;
}
