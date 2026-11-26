"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthSession } from "../../app/providers";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function AuthGate({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const queryClient = useQueryClient();
    const { setUserId } = useAuthSession();
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        let active = true;
        const checkSession = () => fetch(`${API_BASE_URL}/auth/me`, { credentials: "include" })
            .then(async (response) => {
                if (!response.ok) throw new Error("unauthenticated");
                const user = await response.json() as { id?: unknown };
                if (typeof user.id !== "string" || !user.id) throw new Error("invalid_session");
                if (active) setUserId(user.id);
            })
            .catch(() => {
                if (active) {
                    queryClient.clear();
                    setUserId(null);
                    router.replace("/login");
                }
            })
            .finally(() => {
                if (active) setChecking(false);
            });
        void checkSession();
        window.addEventListener("focus", checkSession);

        return () => {
            active = false;
            window.removeEventListener("focus", checkSession);
        };
    }, [queryClient, router, setUserId]);

    if (checking) return <div className="grid min-h-screen place-items-center text-sm text-slate-400" aria-live="polite">Carregando seu painel…</div>;
    return <>{children}</>;
}
