import type { Goal, GoalCreate, GoalFilters, GoalProgress, GoalUpdate } from "../types/goals";

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

function toQueryString(filters: GoalFilters): string {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) params.set(key, String(value));
    });
    const query = params.toString();
    return query ? `?${query}` : "";
}

export function listGoals(filters: GoalFilters = {}): Promise<Goal[]> {
    return request<Goal[]>(`/goals${toQueryString(filters)}`);
}

export function getGoal(goalId: number): Promise<Goal> {
    return request<Goal>(`/goals/${goalId}`);
}

export function getGoalProgress(goalId: number): Promise<GoalProgress> {
    return request<GoalProgress>(`/goals/${goalId}/progress`);
}

export function createGoal(data: GoalCreate): Promise<Goal> {
    return request<Goal>("/goals", { method: "POST", body: JSON.stringify(data) });
}

export function updateGoal(goalId: number, data: GoalUpdate): Promise<Goal> {
    return request<Goal>(`/goals/${goalId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteGoal(goalId: number): Promise<void> {
    return request<void>(`/goals/${goalId}`, { method: "DELETE" });
}