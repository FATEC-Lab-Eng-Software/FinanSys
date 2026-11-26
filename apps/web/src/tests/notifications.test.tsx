import { expect, test } from "@playwright/test";
import type { Notification } from "../types/notifications";

let notifications: Notification[];
let notificationReads: number;
let activeUserId: string | null;

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
    activeUserId = "user-a";

    await page.context().addCookies([
        { name: "finansys_access_token", value: "test-session", url: "http://127.0.0.1:3100" },
    ]);
    await page.route("**/auth/me", (route) => activeUserId
        ? route.fulfill({ status: 200, json: { id: activeUserId, email: `${activeUserId}@finansys.test` } })
        : route.fulfill({ status: 401, json: { detail: "Unauthenticated" } }));
    await page.route("**/auth/logout", async (route) => {
        activeUserId = null;
        await route.fulfill({
            status: 204,
            headers: { "Set-Cookie": "finansys_access_token=; Path=/; Max-Age=0" },
        });
    });
    await page.route("**/auth/login", async (route) => {
        activeUserId = "user-b";
        await route.fulfill({
            status: 200,
            headers: { "Set-Cookie": "finansys_access_token=user-b-session; Path=/" },
            json: { user: { id: "user-b", email: "user-b@finansys.test" } },
        });
    });
    await page.route("**/transactions**", (route) => route.fulfill({ status: 200, json: [] }));
    await page.route("**/notifications**", async (route) => {
        if (route.request().method() === "GET") {
            notificationReads += 1;
            const response = activeUserId === "user-b"
                ? [{
                    id: 3,
                    category: "transaction",
                    title: "Aviso da conta B",
                    description: "Conteúdo privado da conta B.",
                    created_at: "2026-11-21T10:30:00Z",
                }]
                : notifications;
            await route.fulfill({ status: 200, json: response });
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

test("does not reuse the previous account notifications after logout and login", async ({ page }, testInfo) => {
    await page.getByRole("button", { name: "Notificações" }).click();
    await expect(page.getByRole("heading", { name: "Meta concluída" })).toBeVisible();
    await expect.poll(() => notificationReads).toBe(1);

    if (testInfo.project.name === "mobile-chrome") {
        await page.getByRole("button", { name: "Abrir ou fechar menu" }).click();
    }
    await page.getByRole("button", { name: "Sair" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.getByLabel("E-mail").fill("user-b@finansys.test");
    await page.getByLabel("Senha", { exact: true }).fill("password123");
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(page).toHaveURL(/\/gastos$/);

    await page.getByRole("button", { name: "Notificações" }).click();
    const panel = page.locator("#notification-panel");
    await expect(panel.getByRole("heading", { name: "Aviso da conta B" })).toBeVisible();
    await expect(panel.getByText("Conteúdo privado da conta B.")).toBeVisible();
    await expect(panel.getByRole("heading", { name: "Meta concluída" })).toHaveCount(0);
    await expect.poll(() => notificationReads).toBe(2);
});
