"use client";

import { useEffect } from "react";

export function useLandingAnimations(rootRef: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            entry.target.classList.remove("out-view");
          } else {
            const rect = entry.boundingClientRect;
            if (rect.top < 0) {
              entry.target.classList.add("out-view");
              entry.target.classList.remove("in-view");
            } else {
              entry.target.classList.remove("in-view", "out-view");
            }
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" },
    );

    root.querySelectorAll(".reveal, .pop").forEach((el) => {
      revealObserver.observe(el);
    });

    const words = root.querySelectorAll(".hero-word");
    words.forEach((word, i) => {
      setTimeout(() => word.classList.add("typed"), i * 60 + 200);
    });

    const watermark = root.querySelector<HTMLElement>(".hero-watermark");
    const onScroll = () => {
      if (watermark) {
        watermark.style.transform = `translateX(-50%) translateY(${window.scrollY * 0.3}px)`;
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });

    const mockup = root.querySelector(".dashboard-mockup");
    const mockupObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            entry.target.querySelectorAll(".balance-card").forEach((card, i) => {
              setTimeout(() => card.classList.add("in-view"), i * 120 + 400);
            });
            const alert = entry.target.querySelector(".mockup-alert");
            if (alert) {
              setTimeout(() => alert.classList.add("in-view"), 4 * 120 + 400);
            }
            mockupObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3 },
    );
    if (mockup) mockupObserver.observe(mockup);

    return () => {
      revealObserver.disconnect();
      mockupObserver.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, [rootRef]);
}
