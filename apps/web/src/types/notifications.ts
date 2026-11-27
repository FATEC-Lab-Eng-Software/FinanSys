export type NotificationCategory = "transaction" | "goal";

export type Notification = {
    id: number;
    category: NotificationCategory;
    title: string;
    description: string;
    created_at: string;
};
