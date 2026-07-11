import Link from "next/link";

function GetStartedBtn({ large }: { large?: boolean }) {
  return (
    <Link
      href="/login"
      className={`btn-primary inline-block ${large ? "px-9 py-3.5 text-base" : "px-[22px] py-2 text-sm"}`}
    >
      Get Started →
    </Link>
  );
}

export function LandingNav() {
  return (
    <nav
      className="fixed top-0 z-50 flex h-[60px] w-full items-center justify-between border-b px-6 md:px-16 lg:pl-[5rem]"
      style={{ background: "rgba(250, 249, 248, 0.94)", borderColor: "var(--border)", backdropFilter: "blur(8px)" }}
    >
      <div className="flex items-center gap-2.5">
        <div className="h-3 w-3 rounded-sm" style={{ background: "var(--accent)" }} />
        <span className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          LiquidEye
        </span>
      </div>
      <GetStartedBtn />
    </nav>
  );
}

export { GetStartedBtn };
