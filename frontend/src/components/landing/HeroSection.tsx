import { GetStartedBtn } from "./LandingNav";
import { SectionShell } from "./SectionShell";

function HeroWord({ children }: { children: React.ReactNode }) {
  return (
    <span className="word-reveal-parent">
      <span className="hero-word">{children}</span>
    </span>
  );
}

function BalanceCard({
  stripe,
  title,
  amount,
  status,
  statusColor,
}: {
  stripe: string;
  title: string;
  amount: string;
  status: string;
  statusColor?: string;
}) {
  return (
    <div
      className="balance-card rounded-xl p-4"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderTop: `3px solid ${stripe}`,
      }}
    >
      <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {title}
      </p>
      <p className="font-mono mt-2 text-xl font-medium" style={{ color: "var(--text-primary)" }}>
        {amount}
      </p>
      <p className="mt-2 text-xs font-medium" style={{ color: statusColor ?? "var(--text-muted)" }}>
        {status}
      </p>
    </div>
  );
}

export function HeroSection() {
  return (
    <SectionShell id="hero" variant="hero">
      <div className="hero-grid">
        <div className="hero-copy">
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.08em]" style={{ color: "var(--accent-mid)" }}>
            bKash presents SUST CSE Carnival 2026
          </p>

          <h1
            className="font-display text-[40px] font-black leading-[0.95] tracking-[-0.04em] md:text-[64px]"
            style={{ color: "var(--text-primary)" }}
          >
            <HeroWord>One </HeroWord>
            <HeroWord>outlet view.</HeroWord>
            <br />
            <HeroWord>Four </HeroWord>
            <span className="word-reveal-parent">
              <span
                className="hero-word underline decoration-[3px] underline-offset-4"
                style={{ textDecorationColor: "var(--accent)" }}
              >
                separate reserves.
              </span>
            </span>
          </h1>

          <p className="mx-auto mt-5 max-w-md text-base md:text-lg lg:mx-0" style={{ color: "var(--text-body)" }}>
            Decision-support for multi-provider agents — liquidity shortages, unusual activity, and case coordination.
            No fraud verdicts. No wallet merging.
          </p>

          <div className="mt-8 flex flex-col items-center gap-3 lg:items-start">
            <GetStartedBtn large />
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              Pick a demo role — no login required
            </p>
          </div>
        </div>

        <div className="dashboard-mockup w-full">
          <div className="overflow-hidden rounded-xl" style={{ border: "1.5px solid var(--border)" }}>
            <div
              className="flex items-center gap-2 px-4 py-2.5 text-xs font-mono"
              style={{ background: "var(--surface-raised)", color: "var(--text-muted)" }}
            >
              <span className="flex gap-1">
                <span className="h-2 w-2 rounded-full" style={{ background: "var(--danger)" }} />
                <span className="h-2 w-2 rounded-full" style={{ background: "var(--warning)" }} />
                <span className="h-2 w-2 rounded-full" style={{ background: "var(--success)" }} />
              </span>
              Outlet dashboard preview
            </div>
            <div className="grid grid-cols-2 gap-3 p-4" style={{ background: "var(--canvas)" }}>
              <BalanceCard stripe="var(--cash)" title="Shared Cash" amount="৳ 85,000" status="Fresh" statusColor="var(--success)" />
              <BalanceCard stripe="var(--bkash)" title="bKash" amount="৳ 42,000" status="~2h to shortage" statusColor="var(--warning)" />
              <BalanceCard stripe="var(--nagad)" title="Nagad" amount="৳ 31,000" status="Fresh" statusColor="var(--success)" />
              <BalanceCard stripe="var(--rocket)" title="Rocket" amount="—" status="Feed missing" statusColor="var(--danger)" />
            </div>
            <div
              className="balance-card mockup-alert mx-4 mb-4 rounded-lg px-4 py-3 text-sm font-medium"
              style={{
                background: "var(--accent-pale)",
                border: "1px solid var(--accent-soft)",
                color: "var(--accent-deep)",
              }}
            >
              Alert: bKash unusual activity — evidence attached, requires review
            </div>
          </div>
        </div>
      </div>
    </SectionShell>
  );
}
