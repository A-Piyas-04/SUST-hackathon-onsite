export function resolvePageTitle(pathname: string): string {
  const segments = pathname.split("/").filter(Boolean);

  if (segments.includes("transactions")) return "Transactions";
  if (segments.includes("data-quality")) return "Data Quality";
  if (segments.includes("liquidity")) return "Liquidity";
  if (segments.includes("anomalies")) return "Anomalies";
  if (segments[0] === "alerts") return segments[1] ? "Alert detail" : "Alerts";
  if (segments[0] === "cases") return segments[1] ? "Case detail" : "Cases";
  if (segments[0] === "notifications") return "Notifications";
  if (segments[0] === "scenarios") return "Scenarios";
  if (segments[0] === "metrics") return "Metrics";
  if (segments[0] === "audit") return "Audit";
  if (segments[0] === "outlets" && segments.length === 1) return "Outlets";
  if (segments[0] === "outlets" && segments.length >= 2) return "Dashboard";
  if (segments[0] === "dashboard") return "Dashboard";

  const first = segments[0]?.replace(/-/g, " ") ?? "dashboard";
  return first.charAt(0).toUpperCase() + first.slice(1);
}
