import { UserCheck, UserPlus, UserRoundX } from "lucide-react";

type ActivityOverviewProps = {
    createdThisMonth: number;
    active: number;
    suspended: number;
};

export default function ActivityOverview({ createdThisMonth, active, suspended }: ActivityOverviewProps) {
    const activity = [
        { label: "Novos clientes", detail: "Cadastrados neste mês", value: createdThisMonth, icon: UserPlus, tone: "text-blue-600 bg-blue-50" },
        { label: "Contas ativas", detail: "Acesso liberado", value: active, icon: UserCheck, tone: "text-emerald-600 bg-emerald-50" },
        { label: "Contas suspensas", detail: "Acesso suspenso", value: suspended, icon: UserRoundX, tone: "text-amber-600 bg-amber-50" },
    ];
    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="activity-overview-title">
            <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                    <h2 id="activity-overview-title" className="font-semibold text-slate-800">Situação das contas</h2>
                    <p className="mt-1 text-sm text-slate-400">Resumo das contas cadastradas</p>
                </div>
            </div>
            <div className="divide-y divide-slate-100">
                {activity.map(({ label, detail, value, icon: Icon, tone }) => (
                    <article key={label} className="flex items-center gap-3 py-4 first:pt-0 last:pb-0">
                        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${tone}`}>
                            <Icon size={18} aria-hidden="true" />
                        </span>
                        <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-slate-700">{label}</p>
                            <p className="mt-1 text-xs text-slate-400">{detail}</p>
                        </div>
                        <strong className="text-sm text-slate-700">{new Intl.NumberFormat("pt-BR").format(value)}</strong>
                    </article>
                ))}
            </div>
        </section>
    );
}
