"use client";

import Sidebar from "./Sidebar";
import Header from "./Header";
import { AuthGate } from "../auth/auth-gate";

export default function AppShell({ children }: { children: React.ReactNode }) {
    return <AuthGate><div className="flex min-h-screen"><Sidebar /><div className="flex min-w-0 flex-1 flex-col"><Header /><main className="flex-1 p-4 md:p-6">{children}</main></div></div></AuthGate>;
}
