import type { Metadata } from "next";
import "./global.css";
import { Providers } from "./providers";

import "../styles/variaveis.css";

export const metadata: Metadata = {
    title: "FinanSys",
    description: "Sistema financeiro",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="pt-BR">
            <body className="bg-background text-text">
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
