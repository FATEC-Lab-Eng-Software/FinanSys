import type { Metadata } from "next";
import "./global.css";
import { Providers } from "./providers";
import { AppShell } from "../components/layout/AppShell";

import "../styles/variaveis.css";

export const metadata: Metadata = {
    title: "FinanSys",
    description: "Sistema financeiro",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="pt-BR">
            <body className="bg-background text-text">
                <Providers>
                    <AppShell>{children}</AppShell>
                </Providers>
            </body>
        </html>
    );
}
