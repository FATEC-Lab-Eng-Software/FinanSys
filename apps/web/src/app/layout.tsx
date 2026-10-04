import type { Metadata } from "next";
import { Providers } from "./providers";

import Sidebar from "../components/layout/Sidebar";
import Header from "../components/layout/Header";

import "../styles/variaveis.css";

export const metadata: Metadata = {
    title: "FinanSys",
    description: "Sistema financeiro",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="pt-BR">
            <body className="bg-background text-text">
                <Providers>
                    <div className="flex min-h-screen">
                        <Sidebar />
                        <div className="flex min-w-0 flex-1 flex-col">
                            <Header />
                            <main className="flex-1 p-4 md:p-6">
                                {children}
                            </main>
                        </div>
                    </div>
                </Providers>
            </body>
        </html>
    );
}
