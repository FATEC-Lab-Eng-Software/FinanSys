const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): string | undefined {
  if (!email.trim()) return "Informe seu e-mail.";
  return EMAIL_PATTERN.test(email.trim()) ? undefined : "Informe um e-mail válido.";
}

export function validatePassword(password: string): string | undefined {
  if (!password) return "Informe sua senha.";
  if (Array.from(password).length < 8) return "A senha deve ter pelo menos 8 caracteres.";
  return undefined;
}

export function validateName(name: string): string | undefined {
  const trimmed = name.trim();
  if (!trimmed) return "Informe seu nome completo.";
  if (trimmed.length < 2) return "O nome deve ter pelo menos 2 caracteres.";
  return undefined;
}

export function validateConfirmPassword(password: string, confirmPassword: string): string | undefined {
  if (!confirmPassword) return "Confirme sua senha.";
  if (password !== confirmPassword) return "As senhas não coincidem.";
  return undefined;
}

export function validateTerms(accepted: boolean): string | undefined {
  if (!accepted) return "Você precisa aceitar os termos de uso e política de privacidade.";
  return undefined;
}
