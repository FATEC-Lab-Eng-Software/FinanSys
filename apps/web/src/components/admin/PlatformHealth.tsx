import { UsersRound } from "lucide-react";

type PlatformHealthProps = {
    total: number;
    active: number;
    suspended: number;
};

export default function PlatformHealth({ total, active, suspended }: PlatformHealthProps) {
    const activePercentage = total ? Math.round((active / total) * 100) : 0;
    const suspendedPercentage = total ? Math.round((suspended / total) * 100) : 0;
    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="platform-health-title">
            <div className="mb-5 flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-emerald-700">
                    <UsersRound size={20} aria-hidden="true" />
                </span>
                <div>
                    <h2 id="platform-health-title" className="font-semibold text-slate-800">Distribuição de contas</h2>
                    <p className="mt-1 text-sm text-slate-400">Total de {new Intl.NumberFormat("pt-BR").format(total)} clientes</p>
                </div>
            </div>
            <div className="space-y-2">
                <div className="rounded-xl bg-slate-50 px-4 py-4">
                    <div className="mb-2 flex justify-between gap-3 text-sm"><span className="font-medium text-slate-700">Ativas</span><span className="text-slate-500">{activePercentage}%</span></div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${activePercentage}%` }} /></div>
                </div>
                <div className="rounded-xl bg-slate-50 px-4 py-4">
                    <div className="mb-2 flex justify-between gap-3 text-sm"><span className="font-medium text-slate-700">Suspensas</span><span className="text-slate-500">{suspendedPercentage}%</span></div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-amber-500" style={{ width: `${suspendedPercentage}%` }} /></div>
                </div>
            </div>
        </section>
    );
}
