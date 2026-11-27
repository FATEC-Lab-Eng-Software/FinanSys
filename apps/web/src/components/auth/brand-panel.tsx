import type { ReactNode } from "react";
import Link from "next/link";

function BrandMark() {
  return (
    <span className="grid size-[34px] place-items-center rounded-full border border-white/30 bg-white/10" aria-hidden="true">
      <svg className="size-[18px]" viewBox="0 0 24 24" fill="none">
        <path d="M4 17.5 9.1 12l3.1 3.1L20 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M15.5 7H20v4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

export type Benefit = {
  title: string;
  detail: string;
  icon?: ReactNode;
};

export type BrandPanelProps = {
  title?: string;
  description?: string;
  benefits?: Benefit[];
  copyright?: string;
};

const defaultBenefits: Benefit[] = [
  { title: "Fluxo mensal em tempo real", detail: "Receitas e despesas sob controle." },
  { title: "Previsibilidade em primeiro lugar", detail: "Saiba o que vem pela frente." },
  { title: "Metas inteligentes", detail: "Saiba exatamente quanto guardar por mês." },
];

export function BrandPanel({
  title = "Clareza total sobre o seu dinheiro.",
  description = "Centralize contas, acompanhe orçamentos por categoria e conquiste suas metas com um painel construído para decisões rápidas.",
  benefits = defaultBenefits,
  copyright = "© 2026 FinanSys. Desenvolvido com foco em você.",
}: BrandPanelProps = {}) {
  return (
    <aside className="brand-panel relative flex min-h-screen flex-col justify-between overflow-hidden rounded-r-[20px] p-[clamp(30px,5vw,64px)] text-login-text-on-primary [background:linear-gradient(145deg,var(--color-login-navy)_2%,var(--color-login-blue)_55%,var(--color-login-blue-light)_100%)] before:absolute before:right-[-230px] before:top-[-190px] before:size-[360px] before:rounded-full before:border before:border-white/10 before:content-[''] before:pointer-events-none after:absolute after:right-[-180px] after:bottom-[-240px] after:size-[440px] after:rounded-full after:border after:border-white/10 after:content-[''] after:pointer-events-none [@media(max-width:820px)]:rounded-r-2xl [@media(max-width:820px)]:px-6 [@media(max-width:820px)]:py-[30px] [@media(max-width:620px)]:min-h-0 [@media(max-width:620px)]:rounded-r-none [@media(max-width:620px)]:rounded-b-[22px] [@media(max-width:620px)]:px-6 [@media(max-width:620px)]:pt-[22px] [@media(max-width:620px)]:pb-[26px]" aria-label="Sobre o FinanSys">
      <div className="relative z-[1]">
        <Link className="inline-flex items-center gap-[10px] text-[15px] font-bold tracking-[-.02em] text-white hover:text-white" href="/" aria-label="FinanSys início">
          <BrandMark />
          <span>FinanSys</span>
        </Link>

        <div className="mt-[clamp(60px,14vh,148px)] max-w-[520px] [@media(max-width:620px)]:mt-[35px]">
          <h1 className="m-0 max-w-[480px] text-[clamp(30px,3.3vw,48px)] leading-[1.12] tracking-[-.045em] [@media(max-width:820px)]:text-[clamp(27px,4vw,36px)] [@media(max-width:620px)]:max-w-[360px] [@media(max-width:620px)]:text-[30px]">{title}</h1>
          <p className="mt-[18px] max-w-[440px] text-[14px] leading-[1.75] text-white/75 [@media(max-width:620px)]:mt-[10px] [@media(max-width:620px)]:text-[12px]">{description}</p>
        </div>

        <ul className="mt-[clamp(32px,7vh,74px)] grid list-none gap-[22px] p-0 [@media(max-width:820px)]:gap-[18px] [@media(max-width:620px)]:hidden">
          {benefits.map((benefit, index) => (
            <li className="flex items-center gap-[15px]" key={benefit.title}>
              <span className="grid size-[38px] flex-[0_0_38px] place-items-center rounded-xl bg-white/15 text-[18px] text-white" aria-hidden="true">
                {benefit.icon ?? (index === 0 ? "↗" : index === 1 ? "◷" : "✧")}
              </span>
              <span><strong className="block text-[13px] font-semibold">{benefit.title}</strong><small className="mt-1 block text-[11px] text-white/70">{benefit.detail}</small></span>
            </li>
          ))}
        </ul>
      </div>
      <small className="relative z-[1] text-[10px] text-white/60 [@media(max-width:620px)]:hidden">{copyright}</small>
    </aside>
  );
}
