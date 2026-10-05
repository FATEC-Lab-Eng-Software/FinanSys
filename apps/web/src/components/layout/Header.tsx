
'use client';

import { usePathname } from "next/navigation";
import { Bell, User } from "lucide-react";

type LinkItem = {
    href: string;
    label: string;
    description: string;
};

export default function Header() {

    const time = new Date();
    const month = time.toLocaleString('pt-BR', { month: 'long' });
    const year = time.getFullYear();

    const pathname = usePathname();

    const links: LinkItem[] = [
        {
            href: "/dashboard",
            label: "Dashboard",
            description: `Seu resumo financeiro de ${month} de ${year}`
        },
        {
            href: "/gastos",
            label: "Controle de gastos",
            description: "Registre suas entradas e saídas"
        },
        {
            href: "/metas",
            label: "Metas",
            description: "Acompanhe o progresso dos seus objetivos financeiros"
        },
        {
            href: "/analises",
            label: "Gráficos e análises",
            description: "Acompanhe a sua evolução financeira de forma inteligente"
        },
        {
            href: "/assistente",
            label: "Assistente de IA",
            description: "Seu copiloto de inteligência financeira pessoal"
        },
    ];

    const currentLink: LinkItem = links.find(
        (link) => link.href === pathname
    ) ?? {
        href: "",
        label: "Página não encontrada",
        description: "A página solicitada não existe"
    };

    return (
        <header className="flex min-h-16 items-center justify-between gap-4 border-b border-text/10 bg-primary px-4 py-3 md:px-6">
            <div className="min-w-0">
                <h2 className="truncate text-lg font-semibold text-text">
                    {currentLink.label}
                </h2>

                <p className="hidden truncate text-sm text-text/70 sm:block">
                    {currentLink.description}
                </p>
            </div>

            <div className="flex shrink-0 items-center gap-3">
                <button className="flex items-center justify-center border-1 border-gray-200 h-9 w-9 rounded-full bg-primary">
                    <Bell size={16} />
                </button>
                <button type="button" aria-label="Perfil do usuário" className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-primary">
                    <User size={16} />
                </button>
            </div>
        </header>
    );
}
