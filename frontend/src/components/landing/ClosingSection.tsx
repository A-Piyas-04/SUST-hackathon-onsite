import { GetStartedBtn } from "./LandingNav";
import { SectionHeader, SectionShell } from "./SectionShell";

export function ClosingCtaSection() {
  return (
    <SectionShell id="start" variant="start">
      <div className="mx-auto max-w-lg text-center">
        <SectionHeader
          label="Try the demo"
          title={
            <>
              Pick a role. <span className="accent">Explore live.</span>
            </>
          }
          subtitle="Walk through outlet dashboards, alerts, cases, liquidity projections, and anomaly review — all on synthetic data."
        />
        <div className="pop reveal-d2">
          <GetStartedBtn large />
        </div>
        <p className="mt-5 text-[11px]" style={{ color: "var(--text-faint)" }}>
          Synthetic data only · No real accounts or funds
        </p>
      </div>
    </SectionShell>
  );
}

export function LandingFooter() {
  return (
    <footer
      className="flex flex-col items-center justify-between gap-4 border-t px-6 py-7 md:flex-row md:px-16 lg:pl-[5rem]"
      style={{ borderColor: "var(--border)", background: "var(--canvas-alt)" }}
    >
      <div className="flex items-center gap-2.5">
        <div className="h-3 w-3 rounded-sm" style={{ background: "var(--accent)" }} />
        <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          LiquidEye
        </span>
      </div>
      <p className="text-center text-[11px]" style={{ color: "var(--text-muted)" }}>
        bKash presents SUST CSE Carnival 2026 · Decision-support prototype
      </p>
    </footer>
  );
}
