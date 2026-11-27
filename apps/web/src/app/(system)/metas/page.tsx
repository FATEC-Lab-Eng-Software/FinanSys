"use client";

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { History, Medal, Pencil, Plus, X } from "lucide-react";

import Card from "../../../components/ui/Card";
import Form from "../../../components/ui/Form";
import Modal from "../../../components/ui/Modal";
import ErrorMessage from "../../../components/message/error";
import {
    ApiError,
    createGoal,
    deleteGoal,
    getGoalProgress,
    listGoalHistory,
    listGoals,
    updateGoal,
    updateGoalHistory,
} from "../../../services/goals";
import { GOAL_CATEGORY_LABELS } from "../../../types/goals";
import type { Goal, GoalCategory, GoalHistory, GoalProgress, GoalUpdate } from "../../../types/goals";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const CATEGORIES = Object.entries(GOAL_CATEGORY_LABELS) as [GoalCategory, string][];
const EMPTY_FORM = {
    name: "",
    category: "other" as GoalCategory,
    targetValue: "",
    targetDate: "",
    accumulatedValue: "",
};
const TOAST_DURATION = 5000;
const HISTORY_LIMIT = 200;

function formatDate(value: string) {
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR");
}

function formatDateTime(value: string) {
    return new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function toAmount(value: string) {
    const normalized = value.includes(",") ? value.replace(/\./g, "").replace(",", ".") : value;
    return Number(normalized).toFixed(2);
}

function toInputAmount(value: string) {
    return value.replace(".", ",");
}

export default function Metas() {
    const [goals, setGoals] = useState<Goal[]>([]);
    const [progress, setProgress] = useState<Record<number, GoalProgress>>({});
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
    const [form, setForm] = useState(EMPTY_FORM);
    const [saving, setSaving] = useState(false);
    const [historyGoal, setHistoryGoal] = useState<Goal | null>(null);
    const [history, setHistory] = useState<GoalHistory[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [editingEntryId, setEditingEntryId] = useState<number | null>(null);
    const [entryValue, setEntryValue] = useState("");
    const [savingEntry, setSavingEntry] = useState(false);

    const loadGoals = useCallback(async () => {
        try {
            const data = await listGoals();
            const progressList = await Promise.all(data.map((goal) => getGoalProgress(goal.id)));
            setGoals(data);
            setProgress(Object.fromEntries(progressList.map((item) => [item.goal_id, item])));
            setLoadError(false);
        } catch {
            setLoadError(true);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadHistory = useCallback(async (goalId: number) => {
        setHistoryLoading(true);
        setHistoryError(null);
        try {
            const data = await listGoalHistory(goalId, { limit: HISTORY_LIMIT });
            setHistory([...data].reverse());
        } catch {
            setHistoryError("Não foi possível carregar o histórico.");
        } finally {
            setHistoryLoading(false);
        }
    }, []);

    useEffect(() => {
        const run = async () => {
            await loadGoals();
        };
        void run();
    }, [loadGoals]);

    useEffect(() => {
        if (!actionError) return;
        const timer = setTimeout(() => setActionError(null), TOAST_DURATION);
        return () => clearTimeout(timer);
    }, [actionError]);

    const closeForm = useCallback(() => {
        setShowForm(false);
        setEditingGoal(null);
        setForm(EMPTY_FORM);
    }, []);

    const closeHistory = useCallback(() => {
        setHistoryGoal(null);
        setHistory([]);
        setHistoryError(null);
        setEditingEntryId(null);
        setEntryValue("");
    }, []);

    function openCreate() {
        setEditingGoal(null);
        setForm(EMPTY_FORM);
        setShowForm(true);
    }

    function openEdit(goal: Goal) {
        setEditingGoal(goal);
        setForm({
            name: goal.name,
            category: goal.category,
            targetValue: toInputAmount(goal.target_value),
            targetDate: goal.target_date ?? "",
            accumulatedValue: toInputAmount(goal.accumulated_value),
        });
        setShowForm(true);
    }

    function openHistory(goal: Goal) {
        setHistoryGoal(goal);
        setHistory([]);
        setEditingEntryId(null);
        setEntryValue("");
        void loadHistory(goal.id);
    }

    function startEditEntry(entry: GoalHistory) {
        setEditingEntryId(entry.id);
        setEntryValue(toInputAmount(entry.value));
        setHistoryError(null);
    }

    function cancelEditEntry() {
        setEditingEntryId(null);
        setEntryValue("");
    }

    async function saveEntry(entry: GoalHistory) {
        if (!historyGoal) return;
        setSavingEntry(true);
        setHistoryError(null);
        try {
            await updateGoalHistory(historyGoal.id, entry.id, { value: toAmount(entryValue) });
            cancelEditEntry();
            await loadHistory(historyGoal.id);
            await loadGoals();
        } catch (error) {
            setHistoryError(error instanceof ApiError ? error.message : "Não foi possível atualizar o registro.");
        } finally {
            setSavingEntry(false);
        }
    }

    async function saveNewGoal() {
        await createGoal({
            name: form.name,
            category: form.category,
            target_value: toAmount(form.targetValue),
            target_date: form.targetDate || null,
        });
    }

    async function saveGoalChanges(goal: Goal) {
        const values = {
            name: form.name,
            category: form.category,
            target_value: toAmount(form.targetValue),
            target_date: form.targetDate || null,
            accumulated_value: toAmount(form.accumulatedValue),
        };
        const changes = Object.fromEntries(
            Object.entries(values).filter(([key, value]) => value !== goal[key as keyof typeof values]),
        ) as GoalUpdate;
        if (Object.keys(changes).length === 0) return;
        await updateGoal(goal.id, changes);
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setActionError(null);
        try {
            if (editingGoal) {
                await saveGoalChanges(editingGoal);
            } else {
                await saveNewGoal();
            }
            closeForm();
            await loadGoals();
        } catch {
            setActionError(editingGoal ? "Não foi possível atualizar a meta." : "Não foi possível criar a meta.");
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(goal: Goal) {
        if (!window.confirm(`Excluir a meta "${goal.name}"?`)) return;
        setActionError(null);
        try {
            await deleteGoal(goal.id);
            await loadGoals();
        } catch {
            setActionError("Não foi possível excluir a meta.");
        }
    }

    return (
        <section className="flex flex-col gap-6 p-6">
            <div className="flex flex-col gap-5">
                <h2 className="text-xl font-semibold">Ações</h2>
                <button
                    type="button"
                    onClick={openCreate}
                    className="flex flex-row items-center gap-3 rounded-lg bg-sidebar px-4 py-2 text-sm font-medium text-white w-40"
                >
                    Criar nova meta
                    <Plus size={15} />
                </button>
            </div>

            <Modal open={showForm} onClose={closeForm} labelledBy="goal-form-title">
                <Card>
                    <Card.Header>
                        <h3 id="goal-form-title" className="font-semibold">
                            {editingGoal ? "Editar meta" : "Nova meta"}
                        </h3>
                        <button type="button" onClick={closeForm} aria-label="Fechar" className="text-gray-500">
                            <X size={20} />
                        </button>
                    </Card.Header>
                    <Card.Body>
                        <Form id="goal-form" onSubmit={handleSubmit}>
                            <Form.Field>
                                <Form.Label htmlFor="goal-name">Nome</Form.Label>
                                <Form.Input
                                    id="goal-name"
                                    value={form.name}
                                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                                    maxLength={100}
                                    required
                                />
                            </Form.Field>
                            <Form.Field>
                                <Form.Label htmlFor="goal-category">Categoria</Form.Label>
                                <Form.Select
                                    id="goal-category"
                                    value={form.category}
                                    onChange={(event) =>
                                        setForm({ ...form, category: event.target.value as GoalCategory })
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
                                <Form.Label htmlFor="goal-target-value">Valor da meta</Form.Label>
                                <Form.Input
                                    id="goal-target-value"
                                    value={form.targetValue}
                                    onChange={(event) => setForm({ ...form, targetValue: event.target.value })}
                                    placeholder="1500,00"
                                    inputMode="decimal"
                                    required
                                />
                            </Form.Field>
                            {editingGoal && (
                                <Form.Field>
                                    <Form.Label htmlFor="goal-accumulated-value">Valor acumulado</Form.Label>
                                    <Form.Input
                                        id="goal-accumulated-value"
                                        value={form.accumulatedValue}
                                        onChange={(event) =>
                                            setForm({ ...form, accumulatedValue: event.target.value })
                                        }
                                        placeholder="0,00"
                                        inputMode="decimal"
                                        required
                                    />
                                </Form.Field>
                            )}
                            <Form.Field>
                                <Form.Label htmlFor="goal-target-date">Prazo (opcional)</Form.Label>
                                <Form.Input
                                    id="goal-target-date"
                                    type="date"
                                    value={form.targetDate}
                                    onChange={(event) => setForm({ ...form, targetDate: event.target.value })}
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
                            form="goal-form"
                            disabled={saving}
                            className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                        >
                            {saving ? "Salvando..." : editingGoal ? "Salvar alterações" : "Salvar meta"}
                        </button>
                    </Card.Footer>
                </Card>
            </Modal>

            <Modal open={historyGoal !== null} onClose={closeHistory} labelledBy="goal-history-title">
                <Card>
                    <Card.Header>
                        <h3 id="goal-history-title" className="font-semibold">
                            Histórico{historyGoal ? ` - ${historyGoal.name}` : ""}
                        </h3>
                        <button type="button" onClick={closeHistory} aria-label="Fechar" className="text-gray-500">
                            <X size={20} />
                        </button>
                    </Card.Header>
                    <Card.Body className="max-h-96 overflow-y-auto">
                        {historyLoading && <p className="text-sm text-gray-500">Carregando histórico...</p>}
                        {historyError && (
                            <p role="alert" className="text-sm text-red-600">
                                {historyError}
                            </p>
                        )}
                        {!historyLoading && !historyError && history.length === 0 && (
                            <p className="text-sm text-gray-500">Nenhum registro para esta meta.</p>
                        )}
                        <ul className="flex flex-col divide-y divide-gray-200">
                            {history.map((entry) => {
                                const negative = Number(entry.value) < 0;
                                const isEditing = editingEntryId === entry.id;

                                return (
                                    <li key={entry.id} className="flex items-center justify-between gap-3 py-3">
                                        <span className="text-xs text-gray-500">{formatDateTime(entry.created_at)}</span>
                                        {isEditing ? (
                                            <div className="flex flex-row items-center gap-2">
                                                <input
                                                    value={entryValue}
                                                    onChange={(event) => setEntryValue(event.target.value)}
                                                    inputMode="decimal"
                                                    aria-label="Valor do registro"
                                                    className="w-28 rounded-lg border border-gray-300 px-2 py-1 text-sm"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => saveEntry(entry)}
                                                    disabled={savingEntry}
                                                    className="text-sm text-blue-700 disabled:opacity-60"
                                                >
                                                    {savingEntry ? "Salvando..." : "Salvar"}
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={cancelEditEntry}
                                                    className="text-sm text-gray-500"
                                                >
                                                    Cancelar
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex flex-row items-center gap-3">
                                                <span
                                                    className={`text-sm font-medium ${negative ? "text-red-600" : "text-green-600"}`}
                                                >
                                                    {negative ? "" : "+"}
                                                    {currency.format(Number(entry.value))}
                                                </span>
                                                <button
                                                    type="button"
                                                    onClick={() => startEditEntry(entry)}
                                                    aria-label="Editar registro"
                                                    className="text-gray-500 hover:text-blue-700"
                                                >
                                                    <Pencil size={15} />
                                                </button>
                                            </div>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>
                    </Card.Body>
                    <Card.Footer>
                        <span className="text-sm text-gray-500">
                            {historyGoal &&
                                `Acumulado: ${currency.format(Number(goals.find((goal) => goal.id === historyGoal.id)?.accumulated_value ?? historyGoal.accumulated_value))}`}
                        </span>
                        <button
                            type="button"
                            onClick={closeHistory}
                            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium"
                        >
                            Fechar
                        </button>
                    </Card.Footer>
                </Card>
            </Modal>

            {loading && <p className="text-sm text-gray-500">Carregando metas...</p>}
            {loadError && <ErrorMessage title="Não foi possível carregar as informações." />}
            {!loading && !loadError && goals.length === 0 && (
                <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white px-6 py-12 text-center">
                    <span className="mb-4 grid h-16 w-16 place-items-center rounded-full bg-blue-50 text-blue-700">
                        <Medal size={30} strokeWidth={1.8} />
                    </span>
                    <h2 className="text-lg font-semibold text-slate-800">Nenhuma meta cadastrada.</h2>
                    <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                        Organize seus objetivos financeiros e acompanhe seu progresso criando sua primeira meta.
                    </p>
                    <button
                        type="button"
                        onClick={openCreate}
                        className="mt-5 inline-flex h-10 items-center gap-2 rounded-full bg-blue-700 px-5 text-sm font-semibold text-white hover:bg-blue-800"
                    >
                        <Plus size={16} />
                        Criar primeira meta
                    </button>
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 mt-10">
                {goals.map((goal) => {
                    const goalProgress = progress[goal.id];
                    const completed = goalProgress ? 100 - Number(goalProgress.remaining_percentage) : 0;

                    return (
                        <Card key={goal.id}>
                            <Card.Header>
                                <div className="flex min-w-0 flex-1 flex-row items-center gap-2">
                                    <Medal size={35} className="bg-blue-200 rounded-full p-2" />
                                    <div className="min-w-0">
                                        <h3 className="break-words font-semibold">{goal.name}</h3>
                                        {goal.target_date && (
                                            <p className="text-xs text-gray-500">Prazo: {formatDate(goal.target_date)}</p>
                                        )}
                                    </div>
                                </div>
                                <span className="inline-flex w-fit max-w-[40%] shrink-0 items-center justify-center break-words rounded-2xl bg-green-200 px-2 py-1 text-center text-xs leading-tight whitespace-normal">
                                    {GOAL_CATEGORY_LABELS[goal.category]}
                                </span>
                            </Card.Header>
                            <Card.Body>
                                <p className="text-sm">
                                    {currency.format(Number(goal.accumulated_value))} de{" "}
                                    {currency.format(Number(goal.target_value))}
                                </p>
                                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                                    <div className="h-full rounded-full bg-blue-700" style={{ width: `${completed}%` }} />
                                </div>
                            </Card.Body>
                            <Card.Footer>
                                <span className="text-sm text-gray-500">
                                    {goal.status === "done"
                                        ? "Meta concluída"
                                        : goalProgress &&
                                        `Faltam ${currency.format(Number(goalProgress.remaining_value))} (${goalProgress.remaining_percentage}%)`}
                                </span>
                                <div className="flex flex-row gap-3">
                                    <button
                                        type="button"
                                        onClick={() => openHistory(goal)}
                                        className="flex flex-row items-center gap-1 text-sm text-gray-600"
                                    >
                                        <History size={14} />
                                        Histórico
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => openEdit(goal)}
                                        className="text-sm text-blue-700"
                                    >
                                        Editar
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => handleDelete(goal)}
                                        className="text-sm text-red-600"
                                    >
                                        Excluir
                                    </button>
                                </div>
                            </Card.Footer>
                        </Card>
                    );
                })}
            </div>

            {actionError && (
                <div role="alert" className="fixed bottom-6 right-6 z-[60] max-w-sm">
                    <ErrorMessage title={actionError} />
                </div>
            )}
        </section>
    );
}
