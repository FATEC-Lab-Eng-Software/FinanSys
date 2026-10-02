import Link from "next/link";

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M4 17.5 9.1 12l3.1 3.1L20 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M15.5 7H20v4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

const benefits = [
  { title: "Fluxo mensal em tempo real", detail: "Receitas e despesas sob controle." },
  { title: "Previsibilidade em primeiro lugar", detail: "Saiba o que vem pela frente." },
  { title: "Metas inteligentes", detail: "Saiba exatamente quanto guardar por mês." },
];

export function BrandPanel() {
  return (
    <aside className="brand-panel" aria-label="Sobre o FinanSys">
      <div className="brand-panel__content">
        <Link className="brand" href="/" aria-label="FinanSys início">
          <BrandMark />
          <span>FinanSys</span>
        </Link>

        <div className="brand-panel__message">
          <h1>Clareza total sobre o seu dinheiro.</h1>
          <p>
            Centralize contas, acompanhe orçamentos por categoria e conquiste suas metas com um painel construído para decisões rápidas.
          </p>
        </div>

        <ul className="benefit-list">
          {benefits.map((benefit, index) => (
            <li key={benefit.title}>
              <span className="benefit-list__icon" aria-hidden="true">{index === 0 ? "↗" : index === 1 ? "◷" : "✧"}</span>
              <span><strong>{benefit.title}</strong><small>{benefit.detail}</small></span>
            </li>
          ))}
        </ul>
      </div>
      <small className="brand-panel__copyright">© 2026 FinanSys. Desenvolvido com foco em você.</small>
    </aside>
  );
}
