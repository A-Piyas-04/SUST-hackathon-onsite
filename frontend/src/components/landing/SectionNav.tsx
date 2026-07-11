"use client";

import { useEffect, useState } from "react";

const SECTIONS = [
  { id: "hero", label: "Home" },
  { id: "providers", label: "Providers" },
  { id: "roles", label: "Roles" },
  { id: "pipeline", label: "Pipeline" },
  { id: "scenarios", label: "Scenarios" },
  { id: "start", label: "Start" },
] as const;

export function SectionNav() {
  const [active, setActive] = useState("hero");

  useEffect(() => {
    const ids = SECTIONS.map((s) => s.id);
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);

    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]?.target.id) {
          setActive(visible[0].target.id);
        }
      },
      { rootMargin: "-20% 0px -55% 0px", threshold: [0.1, 0.25, 0.5] },
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <nav className="section-nav hidden lg:flex" aria-label="Page sections">
      <div className="section-nav-track">
        {SECTIONS.map((s) => {
          const isActive = active === s.id;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => scrollTo(s.id)}
              className={`section-nav-item${isActive ? " is-active" : ""}`}
              aria-current={isActive ? "true" : undefined}
            >
              <span className="section-nav-dot" />
              <span className="section-nav-label">{s.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
