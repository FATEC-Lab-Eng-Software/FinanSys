type ClientsToolbarProps = {
    search: string;
    status: string;
    onSearchChange: (value: string) => void;
    onStatusChange: (value: string) => void;
};

export default function ClientsToolbar({ search, status, onSearchChange, onStatusChange }: ClientsToolbarProps) {
    return (
        <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-[minmax(0,1fr)_190px]">
            <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Buscar cliente
                <input value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Nome ou e-mail" className="h-11 w-full rounded-xl border border-slate-200 px-3 font-normal outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
            </label>
            <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Situação da conta
                <select value={status} onChange={(event) => onStatusChange(event.target.value)} className="h-11 rounded-xl border border-slate-200 bg-white px-3 font-normal outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
                    <option value="all">Todas</option>
                    <option value="active">Ativas</option>
                    <option value="inactive">Suspensas</option>
                </select>
            </label>
        </div>
    );
}
