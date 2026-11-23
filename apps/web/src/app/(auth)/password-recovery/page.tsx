"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useSyncExternalStore } from "react";
import { AuthShell } from "../../../components/auth/auth-shell";
import { PasswordRecoveryForm } from "../../../components/auth/password-recovery-form";

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
      <div className="grid justify-items-center gap-4 text-center">
        <p className="form-alert m-0 w-full rounded-[10px] border border-login-error/20 bg-login-error/5 px-3.5 py-3 text-xs leading-[1.5] text-login-error" role="alert">Este link de recuperação é inválido ou expirou.</p>
        <Link className="justify-self-center text-xs font-semibold" href="/esqueci-senha">Solicitar novo link</Link>
      </div>
    );
  }

  return <PasswordRecoveryForm accessToken={accessToken} />;
}

export default function PasswordRecoveryPage() {
  return (
    <AuthShell>
      <div className="mx-auto w-full max-w-[440px] [@media(max-width:620px)]:max-w-[460px]">
        <header className="relative mb-8 [@media(max-width:620px)]:mb-[25px]">
          <h2 className="m-0 text-[30px] font-bold tracking-[-.04em] text-login-text">Redefinir senha</h2>
          <p className="mt-[9px] max-w-[400px] text-[13px] leading-[1.6] text-login-text-muted">Crie uma nova senha segura para sua conta.</p>
        </header>
        <Suspense fallback={<p className="text-[13px] text-login-text-muted">Carregando…</p>}>
          <RecoveryCompletion />
        </Suspense>
      </div>
    </AuthShell>
  );
}
