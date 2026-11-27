import type { LucideIcon } from "lucide-react";

type OverviewMetricCardProps = {
    label: string;
    value: string;
    detail: string;
    icon: LucideIcon;
    tone: "blue" | "green" | "violet" | "amber";
};

const tones = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-emerald-50 text-emerald-700",
    violet: "bg-violet-50 text-violet-700",
    amber: "bg-amber-50 text-amber-700",
};

export default function OverviewMetricCard({ label, value, detail, icon: Icon, tone }: OverviewMetricCardProps) {
    return (
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className="text-sm font-medium text-slate-500">{label}</p>
                    <p className="mt-3 text-2xl font-bold tracking-tight text-slate-800">{value}</p>
                </div>
                <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${tones[tone]}`}>
                    <Icon size={20} aria-hidden="true" />
                </span>
            </div>
            <p className="mt-3 text-xs text-slate-400">{detail}</p>
        </article>
    );
}
