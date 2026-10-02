"use client";

import { useState, useEffect, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { register } from "../../services/auth";
import {
  validateConfirmPassword,
  validateEmail,
  validateName,
  validatePassword,
  validateTerms,
} from "../../utils/auth-validation";
import { PasswordInput } from "./password-input";

type FormErrors = {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
};

export function RegisterForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!success) return;
    const timer = setTimeout(() => {
      router.push("/login");
    }, 2000);
    return () => clearTimeout(timer);
  }, [success, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: FormErrors = {
      name: validateName(name),
      email: validateEmail(email),
      password: validatePassword(password),
      confirmPassword: validateConfirmPassword(password, confirmPassword),
      terms: validateTerms(acceptedTerms),
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
      <div className="recovery-success" role="status" aria-live="polite">
        <span className="success-icon" aria-hidden="true">✓</span>
        <h2>Conta criada com sucesso!</h2>
        <p>Seu cadastro foi realizado. Você será redirecionado para a tela de login em instantes.</p>
        <Link className="primary-button primary-button--link" href="/login">
          Ir para o login agora
        </Link>
      </div>
    );
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      {/* Campo Nome Completo */}
      <div className="form-field">
        <label htmlFor="name">Nome completo</label>
        <div className={`input-wrap ${errors.name ? "input-wrap--error" : ""}`}>
          <span className="input-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </span>
          <input
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
          <p className="field-error" id="name-error">
            {errors.name}
          </p>
        )}
      </div>

      {/* Campo E-mail */}
      <div className="form-field">
        <label htmlFor="email">E-mail</label>
        <div className={`input-wrap ${errors.email ? "input-wrap--error" : ""}`}>
          <span className="input-icon" aria-hidden="true">✉</span>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="vinicius@finansys.com.br"
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
          <p className="field-error" id="email-error">
            {errors.email}
          </p>
        )}
      </div>

      {/* Campo Senha */}
      <div className="form-field">
        <label htmlFor="password">Senha</label>
        <div className={`input-wrap ${errors.password ? "input-wrap--error" : ""}`}>
          <span className="input-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
          <p className="field-error" id="password-error">
            {errors.password}
          </p>
        )}
      </div>

      {/* Campo Confirmar Senha */}
      <div className="form-field">
        <label htmlFor="confirmPassword">Confirmar senha</label>
        <div className={`input-wrap ${errors.confirmPassword ? "input-wrap--error" : ""}`}>
          <span className="input-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
          <p className="field-error" id="confirmPassword-error">
            {errors.confirmPassword}
          </p>
        )}
      </div>

      {/* Checkbox Termos de Uso e Privacidade */}
      <div className="form-field">
        <label className="terms-option">
          <input
            id="terms"
            name="terms"
            type="checkbox"
            checked={acceptedTerms}
            onChange={(event) => {
              setAcceptedTerms(event.target.checked);
              setErrors((current) => ({ ...current, terms: undefined }));
            }}
            aria-invalid={Boolean(errors.terms)}
            aria-describedby={errors.terms ? "terms-error" : undefined}
          />
          <span>
            Li e aceito os{" "}
            <Link href="/termos" target="_blank" rel="noopener noreferrer">
              Termos de uso
            </Link>{" "}
            e{" "}
            <Link href="/privacidade" target="_blank" rel="noopener noreferrer">
              Política de privacidade
            </Link>
          </span>
        </label>
        {errors.terms && (
          <p className="field-error" id="terms-error">
            {errors.terms}
          </p>
        )}
      </div>

      {/* Erro global retornado pelo servidor */}
      {serverError && (
        <p className="form-alert" role="alert">
          {serverError}
        </p>
      )}

      {/* Botão de Envio */}
      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Criando conta..." : "Criar conta gratuita"}
      </button>
    </form>
  );
}
