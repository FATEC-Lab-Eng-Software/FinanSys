export type DashboardSummary = {
    balance: string;
    month_inflow: string;
    month_outflow: string;
    month_net: string;
};

export type DashboardGoalItem = {
    id: number;
    name: string;
    accumulated_value: string;
    target_value: string;
    percentage: string;
};

export type DashboardGoals = {
    total: number;
    done: number;
    pending: number;
    total_accumulated: string;
    total_target: string;
    in_progress: DashboardGoalItem[];
};

export type DashboardCategoryExpense = {
    category: string;
    total: string;
};

export type DashboardTransaction = {
    id: number;
    type: string;
    category: string;
    transaction_date: string;
    value: string;
    source_money: string;
};

export type Dashboard = {
    month_start: string;
    summary: DashboardSummary;
    goals: DashboardGoals;
    expenses_by_category: DashboardCategoryExpense[];
    recent_transactions: DashboardTransaction[];
};