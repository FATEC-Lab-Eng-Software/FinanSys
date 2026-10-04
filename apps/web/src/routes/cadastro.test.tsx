import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/cadastro");
});

test("shows a responsive registration form with Figma elements and link to login", async ({ page }, testInfo) => {
  await expect(page.getByRole("heading", { name: "Criar conta" })).toBeVisible();
  await expect(page.getByText("Preencha os dados abaixo para começar.")).toBeVisible();
  await expect(page.getByLabel("Nome completo")).toBeVisible();
  await expect(page.getByLabel("E-mail")).toBeVisible();
  await expect(page.getByLabel("Senha", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Confirmar senha", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Criar conta gratuita" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Entrar" })).toHaveAttribute("href", "/login");

  // Painel lateral e benefícios do protótipo
  await expect(page.getByRole("heading", { name: "Comece a organizar suas finanças hoje." })).toBeVisible();
  await expect(page.getByText("Cadastro rápido e seguro")).toBeVisible();
  await expect(page.getByText("Painel completo")).toBeVisible();
  await expect(page.getByText("Inteligência financeira")).toBeVisible();

  const pageWidth = await page.locator("body").evaluate((body) => body.scrollWidth);
  expect(pageWidth).toBeLessThanOrEqual(testInfo.project.use.viewport?.width ?? 1280);
});

test("validates required fields before submitting with clear error messages", async ({ page }) => {
  await page.getByRole("button", { name: "Criar conta gratuita" }).click();

  await expect(page.getByText("Informe seu nome completo.")).toBeVisible();
  await expect(page.getByText("Informe seu e-mail.")).toBeVisible();
  await expect(page.getByText("Informe sua senha.")).toBeVisible();
  await expect(page.getByText("Confirme sua senha.")).toBeVisible();
});

test("validates password length and password confirmation match", async ({ page }) => {
  await page.getByLabel("Nome completo").fill("Maria Silva");
  await page.getByLabel("E-mail").fill("maria@example.com");
  await page.getByLabel("Senha", { exact: true }).fill("curta");
  await page.getByLabel("Confirmar senha", { exact: true }).fill("diferente");
  await page.getByRole("button", { name: "Criar conta gratuita" }).click();

  await expect(page.getByText("A senha deve ter pelo menos 8 caracteres.")).toBeVisible();
  await expect(page.getByText("As senhas não coincidem.")).toBeVisible();
});

test("validates that full name does not contain numbers", async ({ page }) => {
  await page.getByLabel("Nome completo").fill("Maria 123");
  await page.getByLabel("E-mail").fill("maria@example.com");
  await page.getByLabel("Senha", { exact: true }).fill("senhaForte123");
  await page.getByLabel("Confirmar senha", { exact: true }).fill("senhaForte123");
  await page.getByRole("button", { name: "Criar conta gratuita" }).click();

  await expect(page.getByText("O nome não pode conter números.")).toBeVisible();
});

test("toggles password visibility for both password and confirm password fields", async ({ page }) => {
  const passwordInput = page.getByLabel("Senha", { exact: true });
  const confirmPasswordInput = page.getByLabel("Confirmar senha", { exact: true });

  await passwordInput.fill("senha1234");
  await confirmPasswordInput.fill("senha1234");

  // Toggle senha
  await page.getByRole("button", { name: "Mostrar senha", exact: true }).click();
  await expect(passwordInput).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Ocultar senha", exact: true }).click();
  await expect(passwordInput).toHaveAttribute("type", "password");

  // Toggle confirmar senha
  await page.getByRole("button", { name: "Mostrar senha de confirmação" }).click();
  await expect(confirmPasswordInput).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Ocultar senha de confirmação" }).click();
  await expect(confirmPasswordInput).toHaveAttribute("type", "password");
});

test("shows a clear message when email is already registered", async ({ page }) => {
  await page.route("**/auth/register", (route) =>
    route.fulfill({
      status: 409,
      json: { detail: { code: "email_already_registered", message: "Este e-mail já está cadastrado." } },
    })
  );

  await page.getByLabel("Nome completo").fill("João Souza");
  await page.getByLabel("E-mail").fill("joao@existente.com");
  await page.getByLabel("Senha", { exact: true }).fill("senhaForte123");
  await page.getByLabel("Confirmar senha", { exact: true }).fill("senhaForte123");
  await page.getByRole("button", { name: "Criar conta gratuita" }).click();

  await expect(page.locator(".form-alert")).toHaveText("Este e-mail já está cadastrado. Tente fazer login.");
});

test("submits valid registration, shows confirmation and redirects to login", async ({ page }) => {
  let submittedPayload: unknown;
  await page.route("**/auth/register", async (route) => {
    submittedPayload = route.request().postDataJSON();
    await route.fulfill({
      status: 201,
      json: { message: "Cadastro realizado com sucesso." },
    });
  });

  await page.getByLabel("Nome completo").fill("Novo Usuário");
  await page.getByLabel("E-mail").fill("novo@finansys.com.br");
  await page.getByLabel("Senha", { exact: true }).fill("senhaSegura123");
  await page.getByLabel("Confirmar senha", { exact: true }).fill("senhaSegura123");
  await page.getByRole("button", { name: "Criar conta gratuita" }).click();

  expect(submittedPayload).toEqual({
    name: "Novo Usuário",
    email: "novo@finansys.com.br",
    password: "senhaSegura123",
  });

  await expect(page.getByRole("status")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Conta criada com sucesso!" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ir para o login agora" })).toHaveAttribute("href", "/login");
});
