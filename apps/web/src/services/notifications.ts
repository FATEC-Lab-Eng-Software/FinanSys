import type { Notification } from "../types/notifications";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const MIN_NOTIFICATION_REQUEST_INTERVAL = 600_000;
const lastListRequestAt = new Map<string, number>();
const listRequests = new Map<string, Promise<Notification[]>>();

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init?.headers },
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error("Não foi possível concluir a operação.");
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
}

export function listNotifications(userId: string): Promise<Notification[]> {
    const activeRequest = listRequests.get(userId);
    if (activeRequest) return activeRequest;
    const previousRequestAt = lastListRequestAt.get(userId) ?? 0;
    if (Date.now() - previousRequestAt < MIN_NOTIFICATION_REQUEST_INTERVAL) {
        return Promise.reject(new Error("Aguarde 10 minutos antes de consultar novamente."));
    }

    lastListRequestAt.set(userId, Date.now());
    const listRequest = request<Notification[]>("/notifications").finally(() => {
        listRequests.delete(userId);
    });
    listRequests.set(userId, listRequest);
    return listRequest;
}

export function deleteNotification(notificationId: number): Promise<void> {
    return request<void>(`/notifications/${notificationId}`, { method: "DELETE" });
}

export function deleteAllNotifications(): Promise<void> {
    return request<void>("/notifications", { method: "DELETE" });
}
