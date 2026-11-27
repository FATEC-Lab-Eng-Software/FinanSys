"use client";

import type { ComponentType } from "react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthSession } from "@/app/providers";

export function withAdminAccess<Props extends object>(Component: ComponentType<Props>) {
    function AdminOnly(props: Props) {
        const router = useRouter();
        const { userRole } = useAuthSession();

        useEffect(() => {
            if (userRole === "client") router.replace("/gastos");
        }, [router, userRole]);

        if (userRole !== "admin") return <div className="p-6 text-sm text-slate-500" role="status">Verificando acesso…</div>;
        return <Component {...props} />;
    }

    return AdminOnly;
}
