import type { Dashboard } from "../types/dashboard";
import { ApiError } from "./goals";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getDashboard(): Promise<Dashboard> {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
        headers: { "Content-Type": "application/json" },
        credentials: "include",
    });
    if (!response.ok) {
        throw new ApiError(response.status, "request_failed", "Não foi possível carregar o dashboard.");
    }
    return (await response.json()) as Dashboard;
}