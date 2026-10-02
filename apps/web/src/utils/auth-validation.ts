const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export function validateEmail(email: string): string | undefined {
  return EMAIL_PATTERN.test(email.trim()) ? undefined : "Informe um e-mail válido.";
}

export function validatePassword(password: string): string | undefined {
  if (Array.from(password).length < 8) return "A senha deve ter pelo menos 8 caracteres.";
  return undefined;
}
