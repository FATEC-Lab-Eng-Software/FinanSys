'use client';

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
    House,
    CirclePlus,
    Bot,
    CircleStar,
    ChartPie,
    PanelLeftClose,
    PanelLeftOpen,
    LogOut,
} from "lucide-react";
import { logout } from "../../services/auth";

const links = [
    { href: "/dashboard", label: "Dashboard", icon: House },
    { href: "/gastos", label: "Controle de gastos", icon: CirclePlus },
    { href: "/metas", label: "Metas financeiras", icon: CircleStar },
    { href: "/analises", label: "Gráficos e análises", icon: ChartPie },
    { href: "/assistente", label: "Conversar com o assistente", icon: Bot },
];

const MOBILE_QUERY = "(max-width: 767px)";

export default function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();

    const [isOpen, setIsOpen] = useState<boolean | null>(null);

    const isMobile = () => window.matchMedia(MOBILE_QUERY).matches;

    const variant = (open: string, closed: string, auto: string) =>
        isOpen === null ? auto : isOpen ? open : closed;

    const toggle = () => setIsOpen(!(isOpen ?? !isMobile()));

    const closeOnMobile = () => {
        if (isMobile()) setIsOpen(false);
    };

    const handleLogout = async () => {
        try {
            await logout();
        } finally {
            router.replace("/login");
        }
    };

    return (
        <div className="w-16 shrink-0 md:w-auto">
            {isOpen === true && (
                <div
                    onClick={() => setIsOpen(false)}
                    className="fixed inset-0 z-30 bg-black/40 md:hidden"
                />
            )}
            <aside
                className={`fixed inset-y-0 left-0 z-40 flex h-screen flex-col gap-8 overflow-hidden bg-sidebar px-2 py-6 text-title transition-[width] duration-300 ease-in-out md:sticky md:top-0 ${variant(
                    "w-64",
                    "w-16",
                    "w-16 md:w-64"
                )}`}
            >
                <div className="flex items-start">
                    <div className="min-w-0 flex-1 overflow-hidden">
                        <div
                            className={`whitespace-nowrap px-3 transition-opacity duration-300 ${variant(
                                "opacity-100",
                                "opacity-0",
                                "opacity-0 md:opacity-100"
                            )}`}
                        >
                            <h1 className="text-2xl font-bold">FinanSys</h1>
                            <h2 className="text-sm text-title/60">Finanças pessoais</h2>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={toggle}
                        aria-label="Abrir ou fechar menu"
                        className="flex h-9 w-12 shrink-0 cursor-pointer items-center justify-center rounded-lg hover:bg-title/10"
                    >
                        <PanelLeftClose size={18} className={variant("block", "hidden", "hidden md:block")} />
                        <PanelLeftOpen size={18} className={variant("hidden", "block", "md:hidden")} />
                    </button>
                </div>
                <nav className="flex flex-col gap-1 overflow-y-auto overflow-x-hidden">
                    {links.map((link) => {
                        const Icon = link.icon;
                        const isActive = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);

                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                onClick={closeOnMobile}
                                title={isOpen === false ? link.label : undefined}
                                className={`flex items-center gap-3 whitespace-nowrap rounded-lg border-l-3 px-3 py-2 text-sm transition-colors ${
                                    isActive
                                        ? "bg-primary/15 border-secondary"
                                        : "border-transparent text-title hover:bg-title/10 hover:text-title"
                                }`}
                            >
                                <Icon size={18} className="shrink-0" />
                                <span
                                    className={`transition-opacity duration-300 ${variant(
                                        "opacity-100",
                                        "opacity-0",
                                        "opacity-0 md:opacity-100"
                                    )}`}
                                >
                                    {link.label}
                                </span>
                            </Link>
                        );
                    })}
                </nav>
                <button
                    type="button"
                    onClick={handleLogout}
                    title={isOpen === false ? "Sair" : undefined}
                    className="mt-auto flex items-center gap-3 whitespace-nowrap rounded-lg border-l-3 border-transparent px-3 py-2 text-sm text-title transition-colors hover:bg-title/10 hover:text-title"
                >
                    <LogOut size={18} className="shrink-0" />
                    <span className={`transition-opacity duration-300 ${variant("opacity-100", "opacity-0", "opacity-0 md:opacity-100")}`}>Sair</span>
                </button>
            </aside>
        </div>
    );
}
