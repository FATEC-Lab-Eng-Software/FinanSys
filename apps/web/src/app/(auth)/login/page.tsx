import { AuthForm } from "../../../components/auth/auth-form";
import { AuthShell } from "../../../components/auth/auth-shell";
import Link from "next/link";

export default function LoginPage() {
  return (
    <AuthShell>
      <div className="mx-auto w-full max-w-[440px] [@media(max-width:620px)]:max-w-[460px]">
        <header className="relative mb-8 [@media(max-width:620px)]:mb-[25px]">
          <h2 className="m-0 text-[30px] font-bold tracking-[-.04em] text-login-text">Entrar</h2>
          <p className="mt-[9px] max-w-[400px] text-[13px] leading-[1.6] text-login-text-muted">Acesse seu painel de demonstração com as credenciais pré-preenchidas.</p>
        </header>
        <AuthForm />
        <div className="my-[27px] mb-[19px] flex items-center gap-[14px] text-[11px] text-login-divider before:h-px before:flex-1 before:bg-login-border before:content-[''] after:h-px after:flex-1 after:bg-login-border after:content-['']"><span>ou</span></div>
        <p className="m-0 text-center text-[11px] text-login-text-muted [&_a]:font-semibold">Ainda não tem conta? <Link href="/cadastro">Cadastre-se</Link></p>
      </div>
    </AuthShell>
  );
}
