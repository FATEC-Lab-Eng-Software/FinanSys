import type { ReactNode } from "react";
import { BrandPanel } from "./brand-panel";

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <main className="auth-layout">
      <BrandPanel />
      <section className="auth-content">{children}</section>
    </main>
  );
}
