import { expect, test } from "@playwright/test";
import type { Notification } from "../types/notifications";

let notifications: Notification[];
let notificationReads: number;

test.beforeEach(async ({ page }) => {
    notifications = [
        {
            id: 1,
            category: "transaction",
            title: "Entrada registrada",
            description: "Salário: R$ 3200.00.",
            created_at: "2026-11-21T10:30:00Z",
        },
        {
            id: 2,
            category: "goal",
            title: "Meta concluída",
            description: "Parabéns! Você concluiu a meta Reserva.",
            created_at: "2026-11-21T10:15:00Z",
        },
    ];
    notificationReads = 0;

    await page.context().addCookies([
        { name: "finansys_access_token", value: "test-session", url: "http://127.0.0.1:3100" },
    ]);
    await page.route("**/auth/me", (route) => route.fulfill({ status: 200 }));
    await page.route("**/transactions**", (route) => route.fulfill({ status: 200, json: [] }));
    await page.route("**/notifications**", async (route) => {
        if (route.request().method() === "GET") {
            notificationReads += 1;
            await route.fulfill({ status: 200, json: notifications });
            return;
        }

        const url = new URL(route.request().url());
        if (url.pathname !== "/notifications") {
            const notificationId = Number(url.pathname.split("/").at(-1));
            notifications = notifications.filter((notification) => notification.id !== notificationId);
        } else {
            notifications = [];
        }
        await route.fulfill({ status: 204 });
    });

    await page.goto("/gastos");
});

test("shows, removes, and clears notifications without repeated reads", async ({ page }) => {
    await page.getByRole("button", { name: "Notificações" }).click();

    const panel = page.locator("#notification-panel");
    await expect(panel.getByRole("heading", { name: "Meta concluída" })).toBeVisible();
    await expect(panel.getByText("Entradas e saídas", { exact: true })).toBeVisible();
    await expect(panel.getByText("Metas", { exact: true })).toBeVisible();
    await expect(panel.getByText("Salário: R$ 3200.00.")).toBeVisible();
    await expect.poll(() => notificationReads).toBe(1);

    await page.getByRole("button", { name: "Excluir notificação: Entrada registrada" }).click();
    await expect(panel.getByRole("heading", { name: "Entrada registrada" })).toHaveCount(0);

    await page.getByRole("button", { name: "Limpar todas" }).click();
    await expect(panel.getByText("Tudo em dia")).toBeVisible();

    await page.getByRole("button", { name: "Fechar notificações" }).click();
    await page.getByRole("button", { name: "Notificações" }).click();
    await expect.poll(() => notificationReads).toBe(1);
});

test("keeps long notification lists scrollable on the current screen", async ({ page }) => {
    notifications = Array.from({ length: 14 }, (_, index) => ({
        id: index + 1,
        category: index % 2 === 0 ? "transaction" : "goal",
        title: `Notificação ${index + 1}`,
        description: "Detalhes da notificação que continuam legíveis em telas estreitas.",
        created_at: "2026-11-21T10:30:00Z",
    }));

    await page.getByRole("button", { name: "Notificações" }).click();

    const list = page.locator("#notification-panel .overflow-y-auto");
    await expect(list.getByRole("heading", { name: "Notificação 1", exact: true })).toBeVisible();
    const dimensions = await list.evaluate((element) => ({
        scrollHeight: element.scrollHeight,
        clientHeight: element.clientHeight,
    }));
    expect(dimensions.scrollHeight).toBeGreaterThan(dimensions.clientHeight);

    await list.evaluate((element) => element.scrollTo(0, element.scrollHeight));
    await expect(list.getByRole("heading", { name: "Notificação 14", exact: true })).toBeInViewport();
});
