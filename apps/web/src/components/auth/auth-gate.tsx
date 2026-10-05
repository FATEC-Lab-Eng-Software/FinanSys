"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function AuthGate({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        let active = true;
        fetch(`${API_BASE_URL}/auth/me`, { credentials: "include" })
            .then((response) => {
                if (!response.ok) throw new Error("unauthenticated");
            })
            .catch(() => {
                if (active) router.replace("/login");
            })
            .finally(() => {
                if (active) setChecking(false);
            });
        return () => { active = false; };
    }, [router]);

    if (checking) return <div className="grid min-h-screen place-items-center text-sm text-slate-400" aria-live="polite">Carregando seu painel…</div>;
    return <>{children}</>;
}
