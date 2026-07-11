import { SectionHeader, SectionShell } from "./SectionShell";

const ROLES = [
  {
    name: "Agent",
    desc: "Views own outlet dashboard, alerts, and transactions.",
    tags: ["Dashboard", "Alerts", "Transactions"],
  },
  {
    name: "Area Manager",
    desc: "Monitors outlets in an area — cases, escalation, resolution.",
    tags: ["Outlets", "Cases", "Audit"],
  },
  {
    name: "Provider Ops",
    desc: "Provider-scoped view for bKash, Nagad, or Rocket operations.",
    tags: ["Provider slice", "Cases", "Alerts"],
  },
  {
    name: "Risk Analyst",
    desc: "Reviews unusual patterns with evidence — advisory only.",
    tags: ["Anomalies", "Review", "Metrics"],
  },
  {
    name: "Management",
    desc: "Cross-provider oversight, scenarios, and readiness metrics.",
    tags: ["Metrics", "Scenarios", "Aggregate"],
  },
  {
    name: "Demo Admin",
    desc: "Runs simulations, injects faults, and publishes demo alerts.",
    tags: ["Simulate", "Scenarios", "Publish"],
  },
];

export function RolesSection() {
  return (
    <SectionShell id="roles" variant="roles">
      <SectionHeader
        label="Access control"
        title={
          <>
            Role-based <span className="accent">views and actions.</span>
          </>
        }
        subtitle="Each demo user sees only the pages and workflow steps their role allows — matching the live app permissions."
      />

      <div className="landing-grid-3">
        {ROLES.map((r, i) => (
          <div key={r.name} className={`pop landing-card reveal-d${Math.min(i + 1, 6)}`}>
            <p className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
              {r.name}
            </p>
            <p className="mt-1 flex-1 text-[13px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {r.desc}
            </p>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {r.tags.map((t) => (
                <span key={t} className="tag">
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}
