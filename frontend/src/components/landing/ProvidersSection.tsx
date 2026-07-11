import Image from "next/image";
import { SectionHeader, SectionShell } from "./SectionShell";

const PROVIDERS = [
  { desc: "Physical cash drawer", logo: "/logos/taka.png", alt: "Shared cash (Taka)" },
  { desc: "Provider e-money balance", logo: "/logos/bkash.png", alt: "bKash" },
  { desc: "Provider e-money balance", logo: "/logos/nagad.png", alt: "Nagad" },
  { desc: "Provider e-money balance", logo: "/logos/rocket.png", alt: "Rocket" },
];

export function ProvidersSection() {
  return (
    <SectionShell id="providers" variant="providers">
      <SectionHeader
        label="Ledger"
        title={
          <>
            Four balances. <span className="accent">Never blended.</span>
          </>
        }
        subtitle="The platform tracks shared physical cash and each provider wallet separately. Totals are shown for context — reserves are never merged or converted."
      />

      <div className="provider-logo-grid">
        {PROVIDERS.map((p, i) => (
          <div
            key={p.logo}
            className={`pop provider-logo-card reveal-d${Math.min(i + 1, 4)}`}
          >
            <div className="provider-logo-wrap">
              <Image src={p.logo} alt={p.alt} width={320} height={120} className="provider-logo" />
            </div>
            <p className="provider-logo-desc">{p.desc}</p>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}
