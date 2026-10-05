import Sidebar from "../../components/layout/Sidebar";
import Header from "../../components/layout/Header";
import { AuthGate } from "../../components/auth/auth-gate";

export default function DashboardLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    return (
        <AuthGate>
            <div className="flex min-h-screen">
                <Sidebar />
                <div className="flex min-w-0 flex-1 flex-col">
                    <Header />
                    <main className="flex-1">{children}</main>
                </div>
            </div>
        </AuthGate>
    );
}
