import { expect, test } from "@playwright/test";

test("shows an invalid-link state when the recovery URL has no token", async ({ page }) => {
  await page.goto("/password-recovery");

  await expect(page.locator(".form-alert")).toContainText("inválido ou expirou");
  await expect(page.getByRole("link", { name: "Solicitar novo link" })).toHaveAttribute("href", "/esqueci-senha");
  await expect(page.getByLabel("Nova senha", { exact: true })).toHaveCount(0);
});

test("shows an invalid-link state for Supabase recovery errors in the URL fragment", async ({ page }) => {
  await page.goto("/password-recovery#access_token=&type=recovery&error=access_denied&error_description=Email+link+is+invalid+or+has+expired");

  await expect(page.locator(".form-alert")).toContainText("inválido ou expirou");
  await expect(page.getByLabel("Nova senha", { exact: true })).toHaveCount(0);
});

test("requires eight characters and matching confirmation before completing recovery", async ({ page }) => {
  await page.goto("/password-recovery#access_token=recovery-secret&type=recovery");
  await page.getByLabel("Nova senha", { exact: true }).fill("1234567");
  await page.getByLabel("Confirme a nova senha").fill("1234567");
  await page.getByRole("button", { name: "Redefinir senha" }).click();
  await expect(page.locator(".form-alert")).toHaveText("A senha deve ter pelo menos 8 caracteres.");

  await page.getByLabel("Nova senha", { exact: true }).fill("12345678");
  await page.getByLabel("Confirme a nova senha").fill("87654321");
  await page.getByRole("button", { name: "Redefinir senha" }).click();
  await expect(page.locator(".form-alert")).toHaveText("As senhas não coincidem.");
});

test("allows showing and hiding both recovery password fields", async ({ page }) => {
  await page.goto("/password-recovery#access_token=recovery-secret&type=recovery");

  const password = page.getByLabel("Nova senha", { exact: true });
  const confirmation = page.getByLabel("Confirme a nova senha", { exact: true });
  await password.fill("abcdefgh");
  await confirmation.fill("abcdefgh");

  await page.getByRole("button", { name: "Mostrar senha para Nova senha" }).click();
  await expect(password).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Ocultar senha para Nova senha" }).click();
  await expect(password).toHaveAttribute("type", "password");

  await page.getByRole("button", { name: "Mostrar senha para confirmação" }).click();
  await expect(confirmation).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Ocultar senha para confirmação" }).click();
  await expect(confirmation).toHaveAttribute("type", "password");
});

test("shows recovery success with a path back to login", async ({ page }) => {
  await page.goto("/password-recovery?access_token=recovery-secret&type=recovery");
  await page.route("**/auth/password-recovery/complete", (route) => route.fulfill({ status: 200, json: { message: "Senha redefinida com sucesso." } }));
  await page.getByLabel("Nova senha", { exact: true }).fill("abcdefgh");
  await page.getByLabel("Confirme a nova senha").fill("abcdefgh");
  await page.getByRole("button", { name: "Redefinir senha" }).click();

  await expect(page.getByRole("status")).toContainText("Senha atualizada");
  await expect(page.getByRole("link", { name: "Voltar para entrar" })).toHaveAttribute("href", "/login");
});

test("offers a new recovery request when the backend rejects an expired token", async ({ page }) => {
  await page.goto("/password-recovery#access_token=expired-token&type=recovery");
  await page.route("**/auth/password-recovery/complete", (route) => route.fulfill({ status: 400, json: { detail: { message: "Invalid or expired token" } } }));
  await page.getByLabel("Nova senha", { exact: true }).fill("abcdefgh");
  await page.getByLabel("Confirme a nova senha").fill("abcdefgh");
  await page.getByRole("button", { name: "Redefinir senha" }).click();

  await expect(page.locator(".form-alert")).toContainText("inválido ou expirou");
  await expect(page.getByRole("link", { name: "Solicitar novo link" })).toHaveAttribute("href", "/esqueci-senha");
});
