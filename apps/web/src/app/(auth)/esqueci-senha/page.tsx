import { AuthShell } from "../../../components/auth/auth-shell";
import { PasswordRecoveryForm } from "../../../components/auth/password-recovery-form";
import Link from "next/link";

export default function PasswordRecoveryPage() {
  return (
    <AuthShell>
      <div className="mx-auto w-full max-w-[440px] [@media(max-width:620px)]:max-w-[460px]">
        <header className="relative mb-8 [@media(max-width:620px)]:mb-[25px]">
          <Link className="mb-[15px] inline-flex text-[22px] text-login-text-muted" href="/login" aria-label="Voltar para entrar">←</Link>
          <h2 className="m-0 text-[30px] font-bold tracking-[-.04em] text-login-text">Esqueci minha senha</h2>
          <p className="mt-[9px] max-w-[400px] text-[13px] leading-[1.6] text-login-text-muted">Informe seu e-mail e enviaremos instruções para redefinir sua senha.</p>
        </header>
        <PasswordRecoveryForm />
      </div>
    </AuthShell>
  );
}
