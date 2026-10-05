export type GoalStatus = "pending" | "done";

export type GoalCategory =
    | "work"
    | "housing"
    | "utilities"
    | "food"
    | "transportation"
    | "medical"
    | "pets"
    | "travel"
    | "other";

export const GOAL_CATEGORY_LABELS: Record<GoalCategory, string> = {
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

export type Goal = {
    id: number;
    name: string;
    category: GoalCategory;
    target_date: string | null;
    target_value: string;
    accumulated_value: string;
    status: GoalStatus;
    created_at: string;
    updated_at: string;
};

export type GoalCreate = {
    name: string;
    category: GoalCategory;
    target_value: string;
    target_date?: string | null;
    accumulated_value?: string;
};

export type GoalUpdate = Partial<GoalCreate>;

export type GoalFilters = {
    status?: GoalStatus;
    category?: GoalCategory;
    limit?: number;
    offset?: number;
};

export type GoalProgress = {
    goal_id: number;
    remaining_value: string;
    remaining_percentage: string;
};