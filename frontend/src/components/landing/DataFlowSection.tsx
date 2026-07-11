import { SectionHeader, SectionShell } from "./SectionShell";

type Accent = "red" | "amber" | "analyze" | "purple" | "green";

type Module = {
  num: string;
  name: string;
  subtitle: string;
  chip: string;
  accent: Accent;
};

const MODULES: Module[] = [
  { num: "01", name: "SIMULATE", subtitle: "Synthetic feeds", chip: "feeds", accent: "red" },
  { num: "02", name: "INGEST", subtitle: "Validate · reject bad", chip: "border", accent: "red" },
  { num: "03", name: "LEDGER", subtitle: "4 separate balances", chip: "ledger", accent: "red" },
  { num: "04", name: "QUALITY", subtitle: "Fresh · stale · missing", chip: "confidence", accent: "amber" },
  { num: "05", name: "ANALYZE", subtitle: "Parallel engines", chip: "dual", accent: "analyze" },
  { num: "06", name: "ALERT", subtitle: "Immutable · EN + BN", chip: "evidence", accent: "red" },
  { num: "07", name: "CASE", subtitle: "Route · ack → resolve", chip: "workflow", accent: "purple" },
  { num: "08", name: "HUMAN", subtitle: "Role-filtered UI", chip: "UI", accent: "green" },
];

const ACCENT_BORDER: Record<Accent, string> = {
  red: "#8B1A3A",
  amber: "#A05C0A",
  analyze: "#8B1A3A",
  purple: "#6B4F72",
  green: "#1A5C38",
};

function PipelineChip({ label }: { label: string }) {
  return <span className="pipeline-chip">{label}</span>;
}

function PipelineSeparator() {
  return (
    <div className="pipeline-separator" aria-hidden>
      <div className="pipeline-separator-line" />
      <span className="pipeline-separator-chevron">›</span>
    </div>
  );
}

function PipelineRow({ mod }: { mod: Module }) {
  const borderStyle =
    mod.accent === "analyze"
      ? { borderLeft: `3px dashed ${ACCENT_BORDER.analyze}` }
      : { borderLeft: `3px solid ${ACCENT_BORDER[mod.accent]}` };

  return (
    <div className="pipeline-row pop" style={borderStyle}>
      <div className="pipeline-row-left">
        <span className="pipeline-num font-mono">{mod.num}</span>
        <span className="pipeline-name">{mod.name}</span>
        <span className="pipeline-sub">{mod.subtitle}</span>
      </div>
      <PipelineChip label={mod.chip} />
    </div>
  );
}

function AnalyzeRow({ mod }: { mod: Module }) {
  return (
    <div
      className="pipeline-row pipeline-row-analyze pop"
      style={{ borderLeft: `3px dashed ${ACCENT_BORDER.analyze}` }}
    >
      <div className="pipeline-analyze-header">
        <div className="pipeline-row-left">
          <span className="pipeline-num font-mono">{mod.num}</span>
          <span className="pipeline-name">{mod.name}</span>
          <span className="pipeline-sub">{mod.subtitle}</span>
        </div>
        <PipelineChip label={mod.chip} />
      </div>
      <div className="pipeline-analyze-divider" aria-hidden />
      <div className="pipeline-analyze-engines">
        <span className="pipeline-engine">Liquidity engine</span>
        <span className="pipeline-engine">Anomaly engine</span>
      </div>
    </div>
  );
}

export function DataFlowSection() {
  const before = MODULES.slice(0, 3);
  const quality = MODULES[3];
  const analyze = MODULES[4];
  const after = MODULES.slice(5);

  return (
    <SectionShell id="pipeline" variant="pipeline">
      <SectionHeader
        label="Platform pipeline"
        title={
          <>
            From synthetic feed to <span className="accent">human action.</span>
          </>
        }
        subtitle="Backend data flow — left to right, one screen."
      />

      <div className="pipeline-v-wrap">
        <div className="pipeline-v-stack">
          {before.map((mod, i) => (
            <div key={mod.name}>
              <PipelineRow mod={mod} />
              {i < before.length - 1 ? <PipelineSeparator /> : null}
            </div>
          ))}

          <PipelineSeparator />

          <div className="pipeline-annotated-block">
            <div className="pipeline-annotated-rows">
              <PipelineRow mod={quality} />
              <PipelineSeparator />
              <AnalyzeRow mod={analyze} />
            </div>
            <aside className="pipeline-side-note" aria-label="Quality impact note">
              <div className="pipeline-bracket" aria-hidden />
              <p>Quality degrades → wider projections · some alerts suppressed</p>
            </aside>
          </div>

          {after.map((mod, i) => (
            <div key={mod.name}>
              <PipelineSeparator />
              <PipelineRow mod={mod} />
            </div>
          ))}
        </div>
      </div>
    </SectionShell>
  );
}
