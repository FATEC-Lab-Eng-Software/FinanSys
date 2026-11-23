import type { ReactNode } from "react";
import { BrandPanel, type BrandPanelProps } from "./brand-panel";

export function AuthShell({
  children,
  brandProps,
}: {
  children: ReactNode;
  brandProps?: BrandPanelProps;
}) {
  return (
    <main className="grid min-h-screen grid-cols-[minmax(360px,1.06fr)_minmax(420px,0.94fr)] gap-0 p-0 [@media(max-width:820px)]:grid-cols-[minmax(290px,.82fr)_minmax(360px,1.18fr)] [@media(max-width:620px)]:block [@media(max-width:620px)]:bg-login-surface">
      <BrandPanel {...brandProps} />
      <section className="grid min-w-0 place-items-center p-[clamp(20px,6vw,80px)] [@media(max-width:820px)]:px-6 [@media(max-width:820px)]:py-[30px] [@media(max-width:620px)]:block [@media(max-width:620px)]:px-6 [@media(max-width:620px)]:pt-[34px] [@media(max-width:620px)]:pb-[38px]">{children}</section>
    </main>
  );
}
