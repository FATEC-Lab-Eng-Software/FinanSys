import { AuthForm } from "../components/auth/auth-form";
import { AuthShell } from "../components/auth/auth-shell";
import Link from "next/link";

export default function LoginPage() {
  return (
    <AuthShell>
      <div className="auth-card">
        <header className="auth-heading">
          <span className="auth-heading__mark" aria-hidden="true">●</span>
          <h2>Entrar</h2>
          <p>Acesse seu painel de demonstração com as credenciais pré-preenchidas.</p>
        </header>
        <AuthForm />
        <div className="auth-divider"><span>ou</span></div>
        <p className="auth-footer">Ainda não tem conta? <Link href="/cadastro">Cadastre-se</Link></p>
      </div>
    </AuthShell>
  );
}
