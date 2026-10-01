import type { Metadata } from "next";
import { Providers } from "./providers";

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
            <body><Providers>{children}</Providers></body>
        </html>
    );
}
