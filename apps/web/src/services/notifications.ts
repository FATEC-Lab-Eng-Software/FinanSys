import type { Notification } from "../types/notifications";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const MIN_NOTIFICATION_REQUEST_INTERVAL = 60_000;
let lastListRequestAt = 0;
let listRequest: Promise<Notification[]> | undefined;

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

export function listNotifications(): Promise<Notification[]> {
    if (listRequest) return listRequest;
    if (Date.now() - lastListRequestAt < MIN_NOTIFICATION_REQUEST_INTERVAL) {
        return Promise.reject(new Error("Aguarde um minuto antes de consultar novamente."));
    }

    lastListRequestAt = Date.now();
    listRequest = request<Notification[]>("/notifications").finally(() => {
        listRequest = undefined;
    });
    return listRequest;
}

export function deleteNotification(notificationId: number): Promise<void> {
    return request<void>(`/notifications/${notificationId}`, { method: "DELETE" });
}

export function deleteAllNotifications(): Promise<void> {
    return request<void>("/notifications", { method: "DELETE" });
}
