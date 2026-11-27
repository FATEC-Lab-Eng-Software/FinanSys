"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { register } from "../../services/auth";
import {
  validateConfirmPassword,
  validateEmail,
  validateName,
  validatePassword,
} from "../../utils/auth-validation";
import { PasswordInput } from "./password-input";

type FormErrors = {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
};

export function RegisterForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: FormErrors = {
      name: validateName(name),
      email: validateEmail(email),
      password: validatePassword(password),
      confirmPassword: validateConfirmPassword(password, confirmPassword),
    };

    setErrors(nextErrors);
    setServerError("");

    const hasErrors = Object.values(nextErrors).some(Boolean);
    if (hasErrors) return;

    setSubmitting(true);
    try {
      await register({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
      });
      setSuccess(true);
    } catch (err: unknown) {
      if (err instanceof Error && err.message === "email_already_registered") {
        setServerError("Este e-mail já está cadastrado. Tente fazer login.");
        setErrors((current) => ({ ...current, email: "Este e-mail já está em uso." }));
      } else {
        setServerError("Não foi possível concluir o cadastro. Tente novamente.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="grid justify-items-center gap-[15px] text-center" role="status" aria-live="polite">
        <span className="grid size-12 place-items-center rounded-full bg-login-success-background text-2xl text-login-success" aria-hidden="true">✓</span>
        <h2 className="m-0 text-[22px]">Confirme seu e-mail</h2>
        <p className="m-0 mb-[5px] text-[13px] leading-[1.65] text-login-text-muted">Enviamos um link de confirmação para {email.trim().toLowerCase()}. Confirme seu endereço antes de entrar.</p>
        <Link className="inline-flex min-h-12 items-center justify-center rounded-xl border-0 px-5 [background:linear-gradient(100deg,var(--color-login-blue),var(--color-login-navy))] text-[13px] font-semibold text-white transition-[filter,transform] duration-150 hover:text-white hover:brightness-[1.08] active:translate-y-px" href="/login">
          Ir para o login agora
        </Link>
      </div>
    );
  }

  return (
    <form className="grid gap-5 [@media(max-width:620px)]:gap-[17px]" onSubmit={handleSubmit} noValidate>
      {/* Campo Nome Completo */}
      <div className="grid gap-[9px]">
        <label className="text-[12px] font-semibold text-login-label" htmlFor="name">Nome completo</label>
        <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${errors.name ? "border-login-error" : ""}`}>
          <span className="text-login-icon" aria-hidden="true">
            <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </span>
          <input
            className="h-11 w-full min-w-0 border-0 bg-transparent text-xs text-login-text outline-none placeholder:text-login-input-placeholder autofill:[-webkit-text-fill-color:var(--color-login-text)] autofill:[caret-color:var(--color-login-text)]"
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            placeholder="Digite seu nome completo"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setErrors((current) => ({ ...current, name: undefined }));
            }}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "name-error" : undefined}
          />
        </div>
        {errors.name && (
          <p className="-mt-[3px] text-[11px] leading-[1.4] text-login-error" id="name-error">
            {errors.name}
          </p>
        )}
      </div>

      {/* Campo E-mail */}
      <div className="grid gap-[9px]">
        <label className="text-[12px] font-semibold text-login-label" htmlFor="email">E-mail</label>
        <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${errors.email ? "border-login-error" : ""}`}>
          <span className="text-[14px] text-login-icon" aria-hidden="true">✉</span>
          <input
            className="h-11 w-full min-w-0 border-0 bg-transparent text-xs text-login-text outline-none placeholder:text-login-input-placeholder autofill:[-webkit-text-fill-color:var(--color-login-text)] autofill:[caret-color:var(--color-login-text)]"
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="example@finansys.com.br"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setErrors((current) => ({ ...current, email: undefined }));
              if (serverError) setServerError("");
            }}
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? "email-error" : undefined}
          />
        </div>
        {errors.email && (
          <p className="-mt-[3px] text-[11px] leading-[1.4] text-login-error" id="email-error">
            {errors.email}
          </p>
        )}
      </div>

      {/* Campo Senha */}
      <div className="grid gap-[9px]">
        <label className="text-[12px] font-semibold text-login-label" htmlFor="password">Senha</label>
        <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${errors.password ? "border-login-error" : ""}`}>
          <span className="text-login-icon" aria-hidden="true">
            <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </span>
          <PasswordInput
            id="password"
            name="password"
            autoComplete="new-password"
            placeholder="••••••••"
            minLength={8}
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              setErrors((current) => ({ ...current, password: undefined }));
            }}
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? "password-error" : undefined}
          />
        </div>
        {errors.password && (
          <p className="-mt-[3px] text-[11px] leading-[1.4] text-login-error" id="password-error">
            {errors.password}
          </p>
        )}
      </div>

      {/* Campo Confirmar Senha */}
      <div className="grid gap-[9px]">
        <label className="text-[12px] font-semibold text-login-label" htmlFor="confirmPassword">Confirmar senha</label>
        <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${errors.confirmPassword ? "border-login-error" : ""}`}>
          <span className="text-login-icon" aria-hidden="true">
            <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </span>
          <PasswordInput
            id="confirmPassword"
            name="confirmPassword"
            autoComplete="new-password"
            placeholder="••••••••"
            minLength={8}
            visibilityLabel="de confirmação"
            value={confirmPassword}
            onChange={(event) => {
              setConfirmPassword(event.target.value);
              setErrors((current) => ({ ...current, confirmPassword: undefined }));
            }}
            aria-invalid={Boolean(errors.confirmPassword)}
            aria-describedby={errors.confirmPassword ? "confirmPassword-error" : undefined}
          />
        </div>
        {errors.confirmPassword && (
          <p className="-mt-[3px] text-[11px] leading-[1.4] text-login-error" id="confirmPassword-error">
            {errors.confirmPassword}
          </p>
        )}
      </div>

      {/* Erro global retornado pelo servidor */}
      {serverError && (
        <p className="form-alert m-0 rounded-[10px] border border-login-error/20 bg-login-error/5 px-3.5 py-3 text-xs leading-[1.5] text-login-error" role="alert">
          {serverError}
        </p>
      )}

      {/* Botão de Envio */}
      <button className="inline-flex min-h-12 cursor-pointer items-center justify-center rounded-xl border-0 [background:linear-gradient(100deg,var(--color-login-blue),var(--color-login-navy))] text-[13px] font-semibold text-white transition-[filter,transform] duration-150 hover:text-white hover:brightness-[1.08] active:translate-y-px disabled:cursor-wait disabled:opacity-[.72]" type="submit" disabled={submitting}>
        {submitting ? "Criando conta..." : "Criar conta gratuita"}
      </button>
    </form>
  );
}
