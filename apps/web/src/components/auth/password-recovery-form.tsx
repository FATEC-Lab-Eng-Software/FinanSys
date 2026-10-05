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
      <div className="recovery-success" role="status">
        <span className="success-icon" aria-hidden="true">✓</span>
        <h2>{accessToken ? "Senha atualizada" : "Verifique seu e-mail"}</h2>
        <p>{accessToken ? "Sua senha foi alterada. Agora você já pode entrar na sua conta." : "Se houver uma conta associada a esse e-mail, enviaremos instruções para redefinir sua senha."}</p>
        <Link className="primary-button primary-button--link" href="/login">Voltar para entrar</Link>
      </div>
    );
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      {!accessToken ? (
        <div className="form-field">
          <label htmlFor="recovery-email">E-mail</label>
          <div className={`input-wrap ${error ? "input-wrap--error" : ""}`}>
            <span className="input-icon" aria-hidden="true">✉</span>
            <input autoFocus id="recovery-email" type="email" autoComplete="email" placeholder="voce@finansys.com.br" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
        </div>
      ) : (
        <>
          <div className="form-field">
            <label htmlFor="new-password">Nova senha</label>
            <div className="input-wrap">
              <PasswordInput id="new-password" autoComplete="new-password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} visibilityLabel="para Nova senha" />
            </div>
            <small className="password-hint">Use pelo menos 8 caracteres.</small>
          </div>
          <div className="form-field">
            <label htmlFor="confirm-password">Confirme a nova senha</label>
            <div className="input-wrap">
              <PasswordInput id="confirm-password" autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} visibilityLabel="para confirmação" />
            </div>
          </div>
        </>
      )}

      {error && (
        <div>
          <p className="form-alert" role="alert">{error}</p>
          {accessToken && <Link className="back-link" href="/esqueci-senha">Solicitar novo link</Link>}
        </div>
      )}
      <button className="primary-button" type="submit" disabled={loading}>{loading ? "Aguarde…" : accessToken ? "Redefinir senha" : "Enviar instruções"}</button>
      <Link className="back-link" href="/login">Voltar para entrar</Link>
    </form>
  );
}
