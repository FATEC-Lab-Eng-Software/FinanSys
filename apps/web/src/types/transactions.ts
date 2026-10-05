export type TransactionType = "inflow" | "outflow";

export type TransactionCategory =
    | "work"
    | "housing"
    | "utilities"
    | "food"
    | "transportation"
    | "medical"
    | "pets"
    | "travel"
    | "other";

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
    inflow: "Entrada",
    outflow: "Saída",
};

export const TRANSACTION_CATEGORY_LABELS: Record<TransactionCategory, string> = {
    work: "Trabalho",
    housing: "Moradia",
    utilities: "Contas da casa",
    food: "Alimentação",
    transportation: "Transporte",
    medical: "Saúde",
    pets: "Pets",
    travel: "Viagem",
    other: "Outros",
};

export type Transaction = {
    id: number;
    type: TransactionType;
    category: TransactionCategory;
    transaction_date: string;
    value: string;
    source_money: string;
    created_at: string;
    updated_at: string;
};

export type TransactionCreate = {
    type: TransactionType;
    category: TransactionCategory;
    transaction_date: string;
    value: string;
    source_money: string;
};

export type TransactionUpdate = Partial<TransactionCreate>;

export type TransactionFilters = {
    start_date?: string;
    end_date?: string;
    type?: TransactionType;
    category?: TransactionCategory;
    limit?: number;
    offset?: number;
};
