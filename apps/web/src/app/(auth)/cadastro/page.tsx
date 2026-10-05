import Link from "next/link";
import { AuthShell } from "../../../components/auth/auth-shell";
import { RegisterForm } from "../../../components/auth/register-form";
import type { Benefit } from "../../../components/auth/brand-panel";

function LockBenefitIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function DashboardBenefitIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  );
}

function AiBenefitIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

const registrationBenefits: Benefit[] = [
  {
    title: "Cadastro rápido e seguro",
    detail: "Seus dados protegidos com criptografia de ponta.",
    icon: <LockBenefitIcon />,
  },
  {
    title: "Painel completo",
    detail: "Visualize tudo em um só lugar de maneira simples.",
    icon: <DashboardBenefitIcon />,
  },
  {
    title: "Inteligência financeira",
    detail: "Receba orientações personalizadas com nossa IA.",
    icon: <AiBenefitIcon />,
  },
];

export default function CadastroPage() {
  return (
    <AuthShell
      brandProps={{
        title: "Comece a organizar suas finanças hoje.",
        description:
          "Crie sua conta gratuita e tenha controle total sobre receitas, despesas e metas financeiras.",
        benefits: registrationBenefits,
        copyright: "© 2026 FinanSys. Desenvolvido com foco em você.",
      }}
    >
      <div className="auth-card">
        <header className="auth-heading">
          <h2>Criar conta</h2>
          <p>Preencha os dados abaixo para começar.</p>
        </header>

        <RegisterForm />

        <div className="auth-divider">
          <span>ou</span>
        </div>

        <p className="auth-footer">
          Já tem uma conta? <Link href="/login">Entrar</Link>
        </p>
      </div>
    </AuthShell>
  );
}
