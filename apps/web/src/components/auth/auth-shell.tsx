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
    <main className="auth-layout">
      <BrandPanel {...brandProps} />
      <section className="auth-content">{children}</section>
    </main>
  );
}
