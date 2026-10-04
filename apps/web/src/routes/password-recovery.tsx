"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useSyncExternalStore } from "react";
import { AuthShell } from "../components/auth/auth-shell";
import { PasswordRecoveryForm } from "../components/auth/password-recovery-form";

function RecoveryCompletion() {
  const searchParams = useSearchParams();
  const hash = useSyncExternalStore(
    () => () => undefined,
    () => window.location.hash,
    () => "",
  );
  const fragment = new URLSearchParams(hash.replace(/^#/, ""));
  const accessToken = searchParams.get("access_token") || fragment.get("access_token") || undefined;
  const recoveryType = searchParams.get("type") ?? fragment.get("type");
  const error = searchParams.get("error") ?? fragment.get("error");

  if (error || (recoveryType && recoveryType !== "recovery") || !accessToken) {
    return (
      <div className="recovery-invalid">
        <p className="form-alert" role="alert">Este link de recuperação é inválido ou expirou.</p>
        <Link className="back-link" href="/esqueci-senha">Solicitar novo link</Link>
      </div>
    );
  }

  return <PasswordRecoveryForm accessToken={accessToken} />;
}

export default function PasswordRecoveryPage() {
  return (
    <AuthShell>
      <div className="auth-card">
        <header className="auth-heading">
          <h2>Redefinir senha</h2>
          <p>Crie uma nova senha segura para sua conta.</p>
        </header>
        <Suspense fallback={<p className="recovery-loading">Carregando…</p>}>
          <RecoveryCompletion />
        </Suspense>
      </div>
    </AuthShell>
  );
}
