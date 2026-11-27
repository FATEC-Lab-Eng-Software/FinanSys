"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { login } from "../../services/auth";
import { useAuthSession } from "../../app/providers";
import { validateEmail, validatePassword } from "../../utils/auth-validation";
import { PasswordInput } from "./password-input";

export function AuthForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setUserId, setUserRole } = useAuthSession();
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
      queryClient.clear();
      setUserId(null);
      setUserRole(null);
      router.push("/dashboard");
    } catch (error) {
      if (error instanceof Error && error.message === "account_locked") {
        console.warn("Conta bloqueada", { email: email.trim() });
        return;
      }
      setServerError("Não foi possível entrar. Confira seus dados e tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="grid gap-5 [@media(max-width:620px)]:gap-[17px]" onSubmit={handleSubmit} noValidate>
      <div className="grid gap-[9px]">
        <label className="text-[12px] font-semibold text-login-label" htmlFor="email">E-mail</label>
        <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${errors.email ? "border-login-error" : ""}`}>
          <span className="text-[14px] text-login-icon" aria-hidden="true">✉</span>
          <input className="h-11 w-full min-w-0 border-0 bg-transparent text-xs text-login-text outline-none placeholder:text-login-input-placeholder autofill:[-webkit-text-fill-color:var(--color-login-text)] autofill:[caret-color:var(--color-login-text)]" id="email" name="email" type="email" autoComplete="email" placeholder="voce@finansys.com.br" value={email} onChange={(event) => { setEmail(event.target.value); setErrors((current) => ({ ...current, email: undefined })); }} aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} />
        </div>
        {errors.email && <p className="-mt-[3px] text-[11px] leading-[1.4] text-login-error" id="email-error">{errors.email}</p>}
      </div>

      <div className="grid gap-[9px]">
        <label className="text-[12px] font-semibold text-login-label" htmlFor="password">Senha</label>
        <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${errors.password ? "border-login-error" : ""}`}>
          <span className="text-[14px] text-login-icon" aria-hidden="true">♙</span>
          <PasswordInput id="password" name="password" autoComplete="current-password" placeholder="Digite sua senha" minLength={8} value={password} onChange={(event) => { setPassword(event.target.value); setErrors((current) => ({ ...current, password: undefined })); }} aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} />
        </div>
        {errors.password && <p className="-mt-[3px] text-[11px] leading-[1.4] text-login-error" id="password-error">{errors.password}</p>}
      </div>

      <div className="-mt-0.5 flex items-center justify-between gap-3 text-[11px] [&_a]:font-semibold">
        <label className="inline-flex cursor-pointer items-center gap-[7px] text-login-option"><input className="m-0 size-[14px] accent-login-blue" type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} /><span>Lembrar-me</span></label>
        <Link href="/esqueci-senha">Esqueci minha senha</Link>
      </div>

      {serverError && <p className="form-alert m-0 rounded-[10px] border border-login-error/20 bg-login-error/5 px-3.5 py-3 text-xs leading-[1.5] text-login-error" role="alert">{serverError}</p>}

      <button className="inline-flex min-h-12 cursor-pointer items-center justify-center rounded-xl border-0 [background:linear-gradient(100deg,var(--color-login-blue),var(--color-login-navy))] text-[13px] font-semibold text-white transition-[filter,transform] duration-150 hover:text-white hover:brightness-[1.08] active:translate-y-px disabled:cursor-wait disabled:opacity-[.72]" type="submit" disabled={submitting}>
        {submitting ? "Entrando…" : "Entrar"}
      </button>
    </form>
  );
}
