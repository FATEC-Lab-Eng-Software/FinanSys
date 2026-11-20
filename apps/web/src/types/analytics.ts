import type { TransactionCategory } from "./transactions";

export type AnalyticsPeriod = {
    start_date: string;
    end_date: string;
};

export type MonthlyAnalytics = {
    month: string;
    inflow: string;
    outflow: string;
    net_balance: string;
};

export type CategoryAnalytics = {
    category: TransactionCategory;
    total: string;
};

export type FinancialAnalytics = AnalyticsPeriod & {
    total_inflow: string;
    total_outflow: string;
    net_balance: string;
    monthly: MonthlyAnalytics[];
    expenses_by_category: CategoryAnalytics[];
};
