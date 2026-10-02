"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login } from "../../services/auth";
import { validateEmail, validatePassword } from "../../utils/auth-validation";
import { PasswordInput } from "./password-input";

export function AuthForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = { email: validateEmail(email), password: validatePassword(password) };
    setErrors(nextErrors);
    setServerError("");
    if (nextErrors.email || nextErrors.password) return;

    setSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      router.push("/");
    } catch {
      setServerError("Não foi possível entrar. Confira seus dados e tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <div className="form-field">
        <label htmlFor="email">E-mail</label>
        <div className={`input-wrap ${errors.email ? "input-wrap--error" : ""}`}>
          <span className="input-icon" aria-hidden="true">✉</span>
          <input id="email" name="email" type="email" autoComplete="email" placeholder="voce@finansys.com.br" value={email} onChange={(event) => { setEmail(event.target.value); setErrors((current) => ({ ...current, email: undefined })); }} aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} />
        </div>
        {errors.email && <p className="field-error" id="email-error">{errors.email}</p>}
      </div>

      <div className="form-field">
        <label htmlFor="password">Senha</label>
        <div className={`input-wrap ${errors.password ? "input-wrap--error" : ""}`}>
          <span className="input-icon" aria-hidden="true">♙</span>
          <PasswordInput id="password" name="password" autoComplete="current-password" placeholder="Digite sua senha" minLength={8} value={password} onChange={(event) => { setPassword(event.target.value); setErrors((current) => ({ ...current, password: undefined })); }} aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} />
        </div>
        {errors.password && <p className="field-error" id="password-error">{errors.password}</p>}
      </div>

      <div className="form-options">
        <label className="remember-option"><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} /><span>Lembrar-me</span></label>
        <Link href="/esqueci-senha">Esqueci minha senha</Link>
      </div>

      {serverError && <p className="form-alert" role="alert">{serverError}</p>}

      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Entrando…" : "Entrar"}
      </button>
    </form>
  );
}
