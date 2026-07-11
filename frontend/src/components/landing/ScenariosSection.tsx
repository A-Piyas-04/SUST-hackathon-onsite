import { SectionHeader, SectionShell } from "./SectionShell";

const SCENARIOS = [
  {
    code: "A",
    tag: "Liquidity",
    title: "Hidden cash shortage",
    desc: "Provider cash-out demand drains shared physical cash while e-money balances look healthy.",
  },
  {
    code: "B",
    tag: "Anomaly",
    title: "Pressure + unusual activity",
    desc: "Liquidity pressure coincides with near-identical cash-outs — flagged for review, not a determination of wrongdoing.",
  },
  {
    code: "C",
    tag: "Data quality",
    title: "Stale or missing feeds",
    desc: "Incomplete provider data lowers confidence, widens projections, and suppresses some alerts.",
  },
  {
    code: "D",
    tag: "Coordination",
    title: "Full case lifecycle",
    desc: "Alert routes to owner, moves through acknowledged → escalated → resolved with audit trail.",
  },
];

export function ScenariosSection() {
  return (
    <SectionShell id="scenarios" variant="scenarios">
      <SectionHeader
        label="Demo scenarios"
        title={
          <>
            Four live <span className="accent">demo stories.</span>
          </>
        }
        subtitle="Pre-built simulation scenarios you can run from the app — matching backend scenario A through D."
      />

      <div className="landing-grid-2">
        {SCENARIOS.map((s, i) => (
          <div key={s.code} className={`pop landing-card reveal-d${Math.min(i + 1, 4)}`}>
            <div className="mb-3 flex items-center justify-between">
              <span className="tag">{s.tag}</span>
              <span className="font-mono text-xs font-bold" style={{ color: "var(--accent-mid)" }}>
                Scenario {s.code}
              </span>
            </div>
            <h3 className="font-display text-xl font-extrabold" style={{ color: "var(--text-primary)" }}>
              {s.title}
            </h3>
            <p className="mt-2 flex-1 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {s.desc}
            </p>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}
