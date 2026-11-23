"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { completePasswordRecovery, requestPasswordRecovery } from "../../services/auth";
import { validateEmail, validatePassword } from "../../utils/auth-validation";
import { PasswordInput } from "./password-input";

type RecoveryFormProps = { accessToken?: string };

export function PasswordRecoveryForm({ accessToken }: RecoveryFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [complete, setComplete] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!accessToken) {
      const emailError = validateEmail(email);
      if (emailError) { setError(emailError); return; }
    } else {
      const passwordError = validatePassword(password);
      if (passwordError) { setError(passwordError); return; }
      if (password !== confirmation) { setError("As senhas não coincidem."); return; }
    }

    setLoading(true);
    try {
      if (accessToken) await completePasswordRecovery(accessToken, password);
      else await requestPasswordRecovery(email.trim());
      setComplete(true);
    } catch {
      setError(accessToken ? "Este link de recuperação é inválido ou expirou." : "Não foi possível enviar o e-mail agora. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  if (complete) {
    return (
      <div className="grid justify-items-center gap-[15px] text-center" role="status">
        <span className="grid size-12 place-items-center rounded-full bg-login-success-background text-2xl text-login-success" aria-hidden="true">✓</span>
        <h2 className="m-0 text-[22px]">{accessToken ? "Senha atualizada" : "Verifique seu e-mail"}</h2>
        <p className="m-0 mb-[5px] text-[13px] leading-[1.65] text-login-text-muted">{accessToken ? "Sua senha foi alterada. Agora você já pode entrar na sua conta." : "Se houver uma conta associada a esse e-mail, enviaremos instruções para redefinir sua senha."}</p>
        <Link className="inline-flex min-h-12 items-center justify-center rounded-xl border-0 px-5 [background:linear-gradient(100deg,var(--color-login-blue),var(--color-login-navy))] text-[13px] font-semibold text-white transition-[filter,transform] duration-150 hover:text-white hover:brightness-[1.08] active:translate-y-px" href="/login">Voltar para entrar</Link>
      </div>
    );
  }

  return (
    <form className="grid gap-5 [@media(max-width:620px)]:gap-[17px]" onSubmit={handleSubmit} noValidate>
      {!accessToken ? (
        <div className="grid gap-[9px]">
          <label className="text-[12px] font-semibold text-login-label" htmlFor="recovery-email">E-mail</label>
          <div className={`flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20 ${error ? "border-login-error" : ""}`}>
            <span className="text-[14px] text-login-icon" aria-hidden="true">✉</span>
            <input className="h-11 w-full min-w-0 border-0 bg-transparent text-xs text-login-text outline-none placeholder:text-login-input-placeholder autofill:[-webkit-text-fill-color:var(--color-login-text)] autofill:[caret-color:var(--color-login-text)]" autoFocus id="recovery-email" type="email" autoComplete="email" placeholder="voce@finansys.com.br" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
        </div>
      ) : (
        <>
          <div className="grid gap-[9px]">
            <label className="text-[12px] font-semibold text-login-label" htmlFor="new-password">Nova senha</label>
            <div className="flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20">
              <PasswordInput id="new-password" autoComplete="new-password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} visibilityLabel="para Nova senha" />
            </div>
            <small className="text-[11px] leading-[1.5] text-login-text-muted">Use pelo menos 8 caracteres.</small>
          </div>
          <div className="grid gap-[9px]">
            <label className="text-[12px] font-semibold text-login-label" htmlFor="confirm-password">Confirme a nova senha</label>
            <div className="flex min-h-12 items-center gap-2.5 rounded-xl border border-login-border bg-login-surface px-3.5 transition-[border-color,box-shadow] duration-150 focus-within:border-login-focus-ring focus-within:outline-none focus-within:ring-[3px] focus-within:ring-login-focus-ring/20">
              <PasswordInput id="confirm-password" autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} visibilityLabel="para confirmação" />
            </div>
          </div>
        </>
      )}

      {error && (
        <div>
          <p className="form-alert m-0 rounded-[10px] border border-login-error/20 bg-login-error/5 px-3.5 py-3 text-xs leading-[1.5] text-login-error" role="alert">{error}</p>
          {accessToken && <Link className="justify-self-center text-xs font-semibold" href="/esqueci-senha">Solicitar novo link</Link>}
        </div>
      )}
      <button className="inline-flex min-h-12 cursor-pointer items-center justify-center rounded-xl border-0 [background:linear-gradient(100deg,var(--color-login-blue),var(--color-login-navy))] text-[13px] font-semibold text-white transition-[filter,transform] duration-150 hover:text-white hover:brightness-[1.08] active:translate-y-px disabled:cursor-wait disabled:opacity-[.72]" type="submit" disabled={loading}>{loading ? "Aguarde…" : accessToken ? "Redefinir senha" : "Enviar instruções"}</button>
      <Link className="justify-self-center text-xs font-semibold" href="/login">Voltar para entrar</Link>
    </form>
  );
}
