import { AuthShell } from "../../../components/auth/auth-shell";
import { PasswordRecoveryForm } from "../../../components/auth/password-recovery-form";
import Link from "next/link";

export default function PasswordRecoveryPage() {
  return (
    <AuthShell>
      <div className="auth-card">
        <header className="auth-heading">
          <Link className="recovery-back" href="/login" aria-label="Voltar para entrar">←</Link>
          <h2>Esqueci minha senha</h2>
          <p>Informe seu e-mail e enviaremos instruções para redefinir sua senha.</p>
        </header>
        <PasswordRecoveryForm />
      </div>
    </AuthShell>
  );
}
