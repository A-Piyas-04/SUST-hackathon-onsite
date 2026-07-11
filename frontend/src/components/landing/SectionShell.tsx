import type { ReactNode } from "react";

export function SectionShell({
  id,
  variant,
  children,
}: {
  id: string;
  variant: "hero" | "providers" | "roles" | "pipeline" | "scenarios" | "start";
  children: ReactNode;
}) {
  return (
    <section id={id} className={`landing-section section-${variant}`}>
      <div className="landing-section-inner">{children}</div>
    </section>
  );
}

export function SectionHeader({
  label,
  title,
  subtitle,
}: {
  label: string;
  title: ReactNode;
  subtitle?: string;
}) {
  return (
    <header className="section-header reveal">
      <p className="section-label">{label}</p>
      <h2 className="section-title font-display">{title}</h2>
      {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
    </header>
  );
}
