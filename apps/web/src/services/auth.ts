const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Credentials = { email: string; password: string };

export type RegisterData = {
  name: string;
  email: string;
  password: string;
};

async function readMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return typeof body?.detail?.message === "string" ? body.detail.message : "";
  } catch {
    return "";
  }
}

export async function login(credentials: Credentials): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(credentials),
  });
  if (!response.ok) throw new Error("login_failed");
}

export async function register(data: RegisterData): Promise<{ message?: string }> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const message = await readMessage(response);
    if (response.status === 409 || message.toLowerCase().includes("já cadastrado") || message.toLowerCase().includes("already")) {
      throw new Error("email_already_registered");
    }
    throw new Error(message || "register_failed");
  }
  return response.json().catch(() => ({ message: "success" }));
}

export async function requestPasswordRecovery(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/password-recovery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email }),
  });
  if (!response.ok) throw new Error(await readMessage(response) || "recovery_failed");
}

export async function completePasswordRecovery(accessToken: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/password-recovery/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ access_token: accessToken, new_password: newPassword }),
  });
  if (!response.ok) throw new Error(await readMessage(response) || "recovery_failed");
}

export function getApiErrorMessage(response: Response): Promise<string> {
  return readMessage(response);
}
