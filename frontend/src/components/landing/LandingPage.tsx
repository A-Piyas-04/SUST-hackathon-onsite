"use client";

import { useRef } from "react";
import { useLandingAnimations } from "@/hooks/useLandingAnimations";
import "@/styles/landing.css";
import { LandingNav } from "./LandingNav";
import { SectionNav } from "./SectionNav";
import { HeroSection } from "./HeroSection";
import { ProvidersSection } from "./ProvidersSection";
import { RolesSection } from "./RolesSection";
import { DataFlowSection } from "./DataFlowSection";
import { ScenariosSection } from "./ScenariosSection";
import { ClosingCtaSection, LandingFooter } from "./ClosingSection";

export function LandingPage() {
  const rootRef = useRef<HTMLDivElement>(null);
  useLandingAnimations(rootRef);

  return (
    <div ref={rootRef} className="landing">
      <LandingNav />
      <SectionNav />
      <main>
        <HeroSection />
        <ProvidersSection />
        <RolesSection />
        <DataFlowSection />
        <ScenariosSection />
        <ClosingCtaSection />
      </main>
      <LandingFooter />
    </div>
  );
}
