import type { Transaction, TransactionCreate, TransactionFilters, TransactionUpdate } from "../types/transactions";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
    readonly status: number;
    readonly code: string;

    constructor(status: number, code: string, message: string) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.code = code;
    }
}

async function readError(response: Response): Promise<ApiError> {
    try {
        const body = await response.json();
        const detail = body?.detail;
        if (typeof detail?.message === "string") {
            return new ApiError(response.status, String(detail.code ?? "request_failed"), detail.message);
        }
        if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
            return new ApiError(response.status, "validation_error", detail[0].msg);
        }
    } catch {
        return new ApiError(response.status, "request_failed", "Não foi possível concluir a operação.");
    }
    return new ApiError(response.status, "request_failed", "Não foi possível concluir a operação.");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init.headers },
        credentials: "include",
    });
    if (!response.ok) throw await readError(response);
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
}

function toQueryString(filters: TransactionFilters): string {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) params.set(key, String(value));
    });
    const query = params.toString();
    return query ? `?${query}` : "";
}

export function listTransactions(filters: TransactionFilters = {}): Promise<Transaction[]> {
    return request<Transaction[]>(`/transactions${toQueryString(filters)}`);
}

export function getTransaction(transactionId: number): Promise<Transaction> {
    return request<Transaction>(`/transactions/${transactionId}`);
}

export function createTransaction(data: TransactionCreate): Promise<Transaction> {
    return request<Transaction>("/transactions", { method: "POST", body: JSON.stringify(data) });
}

export function updateTransaction(transactionId: number, data: TransactionUpdate): Promise<Transaction> {
    return request<Transaction>(`/transactions/${transactionId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteTransaction(transactionId: number): Promise<void> {
    return request<void>(`/transactions/${transactionId}`, { method: "DELETE" });
}
