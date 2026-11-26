"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, BellRing, CircleAlert, Goal, Inbox, LoaderCircle, Trash2, X } from "lucide-react";

import { deleteAllNotifications, deleteNotification, listNotifications } from "../../services/notifications";
import type { Notification } from "../../types/notifications";
import { useAuthSession } from "../../app/providers";

const NOTIFICATIONS_QUERY_KEY = ["notifications"] as const;
const notificationDate = new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
});

export default function NotificationMenu() {
    const [open, setOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const queryClient = useQueryClient();
    const { userId } = useAuthSession();
    const notificationsQueryKey = [...NOTIFICATIONS_QUERY_KEY, userId];
    const notificationsQuery = useQuery({
        queryKey: notificationsQueryKey,
        queryFn: () => listNotifications(userId!),
        enabled: open && userId !== null,
        staleTime: 600_000,
        refetchInterval: open ? 600_000 : false,
        refetchIntervalInBackground: false,
        retry: false,
    });

    const deleteOneMutation = useMutation({
        mutationFn: deleteNotification,
        onSuccess: (_, notificationId) => queryClient.setQueryData<Notification[]>(
            notificationsQueryKey,
            (current) => current?.filter((notification) => notification.id !== notificationId),
        ),
    });
    const deleteAllMutation = useMutation({
        mutationFn: deleteAllNotifications,
        onSuccess: () => queryClient.setQueryData(notificationsQueryKey, []),
    });

    const notifications = notificationsQuery.data ?? [];
    const deleting = deleteOneMutation.isPending || deleteAllMutation.isPending;
    const actionError = deleteOneMutation.isError || deleteAllMutation.isError;

    useEffect(() => {
        if (!open) return;

        function closeOnOutsideClick(event: PointerEvent) {
            if (event.target instanceof Node && !menuRef.current?.contains(event.target)) setOpen(false);
        }
        function closeOnEscape(event: KeyboardEvent) {
            if (event.key === "Escape") setOpen(false);
        }

        document.addEventListener("pointerdown", closeOnOutsideClick);
        document.addEventListener("keydown", closeOnEscape);
        return () => {
            document.removeEventListener("pointerdown", closeOnOutsideClick);
            document.removeEventListener("keydown", closeOnEscape);
        };
    }, [open]);

    return (
        <div className="relative" ref={menuRef}>
            <button
                type="button"
                aria-label="Notificações"
                aria-expanded={open}
                aria-controls="notification-panel"
                onClick={() => setOpen((current) => !current)}
                className="relative flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-primary text-text transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
            >
                <Bell size={16} aria-hidden="true" />
                {notifications.length > 0 && (
                    <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-blue-700 px-1 text-[10px] font-semibold leading-none text-white">
                        {notifications.length > 99 ? "99+" : notifications.length}
                    </span>
                )}
            </button>

            {open && (
                <section
                    id="notification-panel"
                    aria-labelledby="notification-panel-title"
                    className="absolute right-0 top-full z-50 mt-3 flex max-h-[min(36rem,calc(100vh-6rem))] w-[min(24rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl"
                >
                    <header className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-100 px-4 py-4">
                        <div className="min-w-0">
                            <h2 id="notification-panel-title" className="font-semibold text-slate-900">Notificações</h2>
                            <p className="mt-0.5 text-xs text-slate-500">Atualização automática a cada 10 minutos</p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1">
                            <button
                                type="button"
                                onClick={() => deleteAllMutation.mutate()}
                                disabled={notifications.length === 0 || deleting}
                                className="rounded-lg px-2 py-2 text-xs font-medium text-slate-500 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                                Limpar todas
                            </button>
                            <button
                                type="button"
                                aria-label="Fechar notificações"
                                onClick={() => setOpen(false)}
                                className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    </header>

                    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
                        {notificationsQuery.isPending && (
                            <div className="flex items-center justify-center gap-2 px-5 py-10 text-sm text-slate-500" role="status">
                                <LoaderCircle size={16} className="animate-spin" />
                                Carregando notificações...
                            </div>
                        )}
                        {notificationsQuery.isError && (
                            <div className="flex flex-col items-center px-5 py-8 text-center" role="alert">
                                <CircleAlert size={22} className="text-red-500" />
                                <p className="mt-2 text-sm font-medium text-slate-700">Não foi possível carregar as notificações.</p>
                                <p className="mt-2 text-xs text-slate-500">A próxima consulta será feita em até 10 minutos.</p>
                            </div>
                        )}
                        {notificationsQuery.isSuccess && notifications.length === 0 && (
                            <div className="flex flex-col items-center px-5 py-10 text-center">
                                <Inbox size={26} className="text-slate-300" />
                                <p className="mt-3 text-sm font-medium text-slate-700">Tudo em dia</p>
                                <p className="mt-1 text-xs text-slate-500">Suas notificações aparecerão aqui.</p>
                            </div>
                        )}
                        {notifications.map((notification) => (
                            <NotificationItem
                                key={notification.id}
                                notification={notification}
                                deleting={deleting}
                                onDelete={() => deleteOneMutation.mutate(notification.id)}
                            />
                        ))}
                    </div>

                    {actionError && (
                        <p className="shrink-0 border-t border-red-100 bg-red-50 px-4 py-2 text-xs text-red-700" role="alert">
                            Não foi possível excluir as notificações. Tente novamente.
                        </p>
                    )}
                </section>
            )}
        </div>
    );
}

function NotificationItem({
    notification,
    deleting,
    onDelete,
}: {
    notification: Notification;
    deleting: boolean;
    onDelete: () => void;
}) {
    const isGoal = notification.category === "goal";

    return (
        <article className="grid grid-cols-[2.25rem_minmax(0,1fr)_2rem] items-start gap-3 border-b border-slate-100 px-4 py-4 last:border-0">
            <span className={`grid h-9 w-9 place-items-center rounded-xl ${isGoal ? "bg-amber-50 text-amber-600" : "bg-blue-50 text-blue-700"}`} aria-hidden="true">
                {isGoal ? <Goal size={17} /> : <BellRing size={17} />}
            </span>
            <div className="min-w-0">
                <span className="inline-flex max-w-full rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    {isGoal ? "Metas" : "Entradas e saídas"}
                </span>
                <h3 className="mt-2 break-words text-sm font-semibold leading-5 text-slate-800">{notification.title}</h3>
                <p className="mt-1 break-words text-sm leading-5 text-slate-600">{notification.description}</p>
                <time dateTime={notification.created_at} className="mt-2 block text-xs text-slate-400">
                    {notificationDate.format(new Date(notification.created_at))}
                </time>
            </div>
            <button
                type="button"
                aria-label={`Excluir notificação: ${notification.title}`}
                onClick={onDelete}
                disabled={deleting}
                className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-40"
            >
                <Trash2 size={15} />
            </button>
        </article>
    );
}
