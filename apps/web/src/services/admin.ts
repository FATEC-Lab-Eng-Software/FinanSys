import type { AdminClient, AdminClientPage, AdminOverview } from "../types/admin";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init?.headers },
        credentials: "include",
    });
    if (!response.ok) throw new Error("Não foi possível concluir a operação.");
    return response.json() as Promise<T>;
}

export function listAdminClients(search: string, status: string, page: number): Promise<AdminClientPage> {
    const params = new URLSearchParams({ search, page: String(page), page_size: "20" });
    if (status !== "all") params.set("active", String(status === "active"));
    return request<AdminClientPage>(`/admin/clients?${params.toString()}`);
}

export function updateAdminClientStatus(clientId: string, active: boolean): Promise<AdminClient> {
    return request<AdminClient>(`/admin/clients/${clientId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: active }),
    });
}

export function getAdminOverview(): Promise<AdminOverview> {
    return request<AdminOverview>("/admin/overview");
}
