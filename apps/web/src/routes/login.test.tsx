import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
});

test("shows a responsive login form and links to registration and recovery", async ({ page }, testInfo) => {
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
  await expect(page.getByLabel("E-mail")).toBeVisible();
  await expect(page.getByLabel("Senha", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Cadastre-se" })).toHaveAttribute("href", "/cadastro");
  await expect(page.getByRole("link", { name: "Esqueci minha senha" })).toHaveAttribute("href", "/esqueci-senha");

  const pageWidth = await page.locator("body").evaluate((body) => body.scrollWidth);
  expect(pageWidth).toBeLessThanOrEqual(testInfo.project.use.viewport?.width ?? 1280);

  if (!testInfo.project.use.isMobile) {
    const panel = await page.locator(".brand-panel").evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      return { top: bounds.top, left: bounds.left, height: bounds.height, viewportHeight: window.innerHeight };
    });
    expect(panel.top).toBe(0);
    expect(panel.left).toBe(0);
    expect(panel.height).toBe(panel.viewportHeight);
  }
});

test("validates email and password rules before submitting", async ({ page }) => {
  await page.getByLabel("E-mail").fill("email-invalido");
  await page.getByLabel("Senha", { exact: true }).fill("fraca");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByText("Informe um e-mail válido.")).toBeVisible();
  await expect(page.getByText("A senha deve ter pelo menos 8 caracteres.")).toBeVisible();
  await expect(page.locator(".form-alert")).toHaveCount(0);
});

test("toggles password visibility without submitting the form", async ({ page }) => {
  const password = page.getByLabel("Senha", { exact: true });
  await password.fill("abcdefgh");

  await page.getByRole("button", { name: "Mostrar senha" }).click();
  await expect(password).toHaveAttribute("type", "text");
  await expect(page.getByRole("button", { name: "Ocultar senha" })).toHaveAttribute("aria-pressed", "true");

  await page.getByRole("button", { name: "Ocultar senha" }).click();
  await expect(password).toHaveAttribute("type", "password");
  await expect(page.getByRole("button", { name: "Mostrar senha" })).toHaveAttribute("aria-pressed", "false");
  await expect(page).toHaveURL(/\/login$/);
});

test("shows a generic error when credentials are rejected", async ({ page }) => {
  await page.route("**/auth/login", (route) => route.fulfill({ status: 401, json: { detail: { message: "E-mail ou senha inválidos." } } }));
  await page.getByLabel("E-mail").fill("user@example.com");
  await page.getByLabel("Senha", { exact: true }).fill("abcdefgh");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.locator(".form-alert")).toHaveText("Não foi possível entrar. Confira seus dados e tente novamente.");
});

test("sends credentials and redirects to the home page", async ({ page }) => {
  let requestBody: unknown;
  await page.route("**/auth/login", async (route) => {
    requestBody = route.request().postDataJSON();
    await route.fulfill({ status: 200, json: { user: { id: "user-1", email: "user@example.com" }, expires_in: 3600 } });
  });
  await page.getByLabel("E-mail").fill("user@example.com");
  await page.getByLabel("Senha", { exact: true }).fill("abcdefgh");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/127\.0\.0\.1:3100\/$/);
  expect(requestBody).toEqual({ email: "user@example.com", password: "abcdefgh" });
});

test("requests password recovery and shows a generic confirmation", async ({ page }) => {
  await page.getByRole("link", { name: "Esqueci minha senha" }).click();
  await expect(page.getByRole("heading", { name: "Esqueci minha senha" })).toBeVisible();
  await page.route("**/auth/password-recovery", (route) => route.fulfill({ status: 202, json: { message: "Se houver uma conta associada, enviaremos instruções para redefinir sua senha." } }));
  await page.getByLabel("E-mail").fill("user@example.com");
  await page.getByRole("button", { name: "Enviar instruções" }).click();
  await expect(page.getByRole("status")).toContainText("Verifique seu e-mail");
  await expect(page.getByRole("status")).toContainText("Se houver uma conta associada");
});

test("validates and submits a recovery password", async ({ page }) => {
  await page.goto("/password-recovery#access_token=recovery-secret&type=recovery");
  await page.getByLabel("Nova senha", { exact: true }).fill("abcdefgh");
  await page.getByLabel("Confirme a nova senha").fill("abcdefgh");
  await page.route("**/auth/password-recovery/complete", async (route) => {
    expect(route.request().postDataJSON()).toEqual({ access_token: "recovery-secret", new_password: "abcdefgh" });
    await route.fulfill({ status: 200, json: { message: "Senha redefinida com sucesso." } });
  });
  await page.getByRole("button", { name: "Redefinir senha" }).click();
  await expect(page.getByRole("status")).toContainText("Senha atualizada");
});
