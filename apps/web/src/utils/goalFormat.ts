const currencyFormatter = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
});

export function formatCurrency(value: string | number): string {
    return currencyFormatter.format(Number(value));
}

export function formatPercentage(value: string | number): string {
    return `${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`;
}