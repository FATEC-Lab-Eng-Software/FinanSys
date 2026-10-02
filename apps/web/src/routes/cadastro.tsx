import Link from "next/link";
import { AuthShell } from "../components/auth/auth-shell";
import { RegisterForm } from "../components/auth/register-form";
import type { Benefit } from "../components/auth/brand-panel";

const registrationBenefits: Benefit[] = [
  {
    title: "Cadastro rápido e seguro",
    detail: "Seus dados protegidos com criptografia de ponta.",
    icon: "🔒",
  },
  {
    title: "Painel completo",
    detail: "Visualize tudo em um só lugar de maneira simples.",
    icon: "◫",
  },
  {
    title: "Inteligência financeira",
    detail: "Receba orientações personalizadas com nossa IA.",
    icon: "💬",
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
        copyright: "© 2026 FinanSys. Demonstração com dados fictícios.",
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
