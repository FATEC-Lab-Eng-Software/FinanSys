export type AdminClient = {
    id: string;
    email: string;
    first_name: string | null;
    last_name: string | null;
    is_active: boolean;
    created_at: string;
    last_access_at: string | null;
};

export type AdminClientPage = {
    items: AdminClient[];
    page: number;
    page_size: number;
    has_more: boolean;
};

export type AdminOverview = {
    clients_total: number;
    clients_active: number;
    clients_suspended: number;
    clients_created_this_month: number;
};
