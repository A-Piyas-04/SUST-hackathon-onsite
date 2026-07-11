# Landing Page Design Plan
## Multi-Provider Agent Liquidity & Coordination Platform
**Scope:** Public-facing marketing/entry page only · links to `/login`

---

## 0. Design Constraints (Hard Rules)

These are non-negotiable. Every decision below is filtered through them.

1. **Light mode only.** No dark backgrounds, no terminal aesthetic, no near-black surfaces.
2. **Warm off-white base — not pure white.** `#F5F2EE` as the canvas, not `#FFFFFF`. Pure white feels sterile and AI-generated.
3. **No glassmorphism.** No `backdrop-filter: blur()`, no frosted panels, no semi-transparent overlays with blur. These are the most recognizable AI-generated design tell.
4. **No neon.** No electric blue, no glowing borders, no neon accent on dark surfaces.
5. **No generic AI defaults.** No hero with a large number + small label + gradient accent. No "01 / 02 / 03" decorative step numbers. No mesh gradients. No floating cards with excessive drop shadows. No hero text with a rainbow gradient clip.
6. **Minimal text.** No paragraphs anywhere. Every section lives off headlines, labels, and 1–2 sentence fragments max.
7. **Big everything.** Headlines 64px+, section labels 13px uppercase tracked, amounts in monospace and oversized, icons large and breathing.
8. **Pop-up and vanish animations on elements** as they enter and exit the viewport.
9. **Scroll-driven animations** throughout — not just fade-ins but directional, staggered, and purposeful motion.
10. **One "Get Started" CTA** that routes to `/login`. No secondary CTAs in the hero.

---

## 1. Visual Identity

### 1.1 The Aesthetic Direction

The reference world is **Bangladeshi printed financial documents** — passbooks, agent receipts, government ledger paper — translated into a modern web surface. Think: cream paper, ink-stamped text, ruled lines, deliberate negative space, and the three provider colors used as functional ink marks rather than decorative splashes.

This is the opposite of a SaaS dashboard landing page. It should feel like a well-designed annual report cover — authoritative, legible, calm.

### 1.2 Color Palette

```
/* Canvas & Surfaces */
--canvas:          #F5F2EE   /* warm off-white — the "paper" */
--surface:         #EDEAE5   /* slightly darker card background */
--surface-raised:  #E8E4DE   /* table rows, inset sections */
--ink:             #F0EDE8   /* very subtle rule lines, dividers */

/* Text */
--text-primary:    #1A1714   /* near-black warm ink — headings */
--text-body:       #3D3730   /* warm dark brown — body fragments */
--text-muted:      #857D74   /* metadata, timestamps, labels */
--text-faint:      #B8B0A6   /* placeholders, disabled, watermarks */

/* Accent — one color, used sparingly */
--accent:          #1D5FA8   /* deep ink blue — CTAs, links, focus only */
--accent-light:    #E8F0FA   /* accent tint — badge backgrounds */
--accent-text:     #1A4F8A   /* text on accent tint */

/* Provider colors — used as left-border stripes and chips, never full fills */
--bkash:           #C01060   /* darkened magenta — readable on light */
--nagad:           #D4541A   /* darkened orange — readable on light */
--rocket:          #6B2578   /* darkened purple — readable on light */
--cash:            #2D6B4A   /* deep green for shared cash */

/* Semantic */
--success:         #1A7A3F   /* fresh feed, resolved */
--warning:         #A05C0A   /* stale feed, medium confidence */
--danger:          #B91C1C   /* missing feed, high severity */

/* Borders */
--border:          #D6D0C8   /* default hairline */
--border-strong:   #BFB8AE   /* hover, emphasis */
```

**What makes this palette non-generic:**
- The base is warm `#F5F2EE`, not cold `#F8FAFC` (the SaaS default)
- The accent is a considered deep ink blue, not electric cyan or violet
- Provider colors are darkened versions of their brand colors, usable on light
- Text has warmth — `#1A1714` not `#111827`

### 1.3 Typography

```
Display / Hero:   "Fraunces"     — variable optical serif, weight 800–900
                                   Loaded from Google Fonts
                                   Used only for the hero headline and section titles
                                   Tight tracking: -0.04em
                                   Optical size: large (opsz 144)

Labels / UI:      "Inter"        — weight 400, 500, 600
                                   All navigation, body fragments, badges, metadata

Data / Amounts:   "JetBrains Mono" — weight 400, 500
                                   All BDT amounts, IDs, timestamps, percentages
```

**Pairing logic:** Fraunces is an optical serif with ink-trap details — it looks like it was stamped, not rendered. Against Inter's clean geometry and Mono's numeric precision, the trio creates a hierarchy that reads as designed, not defaulted.

**Type scale:**
```
--text-hero:    80px / lh 0.95 / Fraunces 900   → hero headline
--text-display: 56px / lh 1.0  / Fraunces 800   → section titles
--text-xl:      28px / lh 1.2  / Inter 600       → card titles, callouts
--text-lg:      20px / lh 1.4  / Inter 400       → sub-headlines, fragments
--text-base:    15px / lh 1.6  / Inter 400       → UI text, descriptions
--text-label:   11px / lh 1.4  / Inter 600       → uppercase section labels (tracked 0.1em)
--text-mono:    22px / lh 1.2  / JetBrains Mono  → balance amounts
--text-mono-sm: 13px / lh 1.5  / JetBrains Mono  → table data, IDs
```

### 1.4 Layout System

```
Max content width: 1200px, centered
Horizontal padding: 64px desktop / 24px mobile
Section vertical rhythm: 128px top / 128px bottom
Grid: 12 columns, 24px gutters
Card border-radius: 12px
Input/button border-radius: 8px
Badge border-radius: 4px
```

**No card shadows.** Cards use a `1px solid var(--border)` only. Shadows are a glassmorphism-adjacent tell. Elevation is communicated through background color difference, not shadow depth.

### 1.5 Signature Element

The single most memorable visual decision: **provider identity is shown as a ruled ink stripe.** On the hero dashboard mockup and all balance cards, each provider has a `3px top border` (not left border on the landing page — top border reads better large) in its exact brand color. The card background is `var(--surface)` — warm off-white paper. No gradients, no glows. The color lands like a stamp.

Combined with the Fraunces serif at 80px, this "ink on paper" metaphor is what makes the landing page immediately distinct from every SaaS landing page in its category.

---

## 2. Animation System

### 2.1 Philosophy

Animations serve one purpose: **showing the user what matters and when.** They are not decoration. Every animation either:
- Reveals content that deserves attention (scroll reveal)
- Confirms a user interaction (pop-up on entry)
- Signals a state change (vanish on exit)
- Demonstrates the product story (dashboard card sequence)

**No ambient animations.** No floating, no pulsing gradients, no rotating meshes. Those are the AI-generated default.

### 2.2 Scroll Reveal System

Every section and major element uses `IntersectionObserver` with a threshold of `0.15`. Elements start hidden and animate in when they cross the threshold. Crucially: **they also reverse when scrolling back up** — elements that leave the viewport top edge vanish, so scrolling down re-triggers the entrance animations.

```css
/* Base state — all animatable elements start here */
.reveal {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Triggered by IntersectionObserver adding this class */
.reveal.in-view {
  opacity: 1;
  transform: translateY(0);
}

/* Reversed when element exits viewport top — JS removes .in-view */
/* Result: scrolling down re-plays the entrance animation */
```

**Stagger delays for groups** (role cards, scenario cards, module rows):
```css
.reveal-d1 { transition-delay: 0.05s }
.reveal-d2 { transition-delay: 0.12s }
.reveal-d3 { transition-delay: 0.19s }
.reveal-d4 { transition-delay: 0.26s }
.reveal-d5 { transition-delay: 0.33s }
.reveal-d6 { transition-delay: 0.40s }
```

### 2.3 Pop-Up / Vanish Animations

Distinct from scroll reveals. Used for:
- Elements entering from below with a slight scale (pop-up feel)
- Elements exiting by shrinking slightly and fading (vanish)
- The dashboard balance cards staggering in one by one

```css
/* Pop-up variant — used for cards, chips, badges */
.pop {
  opacity: 0;
  transform: translateY(20px) scale(0.96);
  transition: opacity 0.5s cubic-bezier(0.34, 1.56, 0.64, 1),
              transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}
/* The cubic-bezier here is a spring — gives the slight overshoot
   that reads as "pop" without being bouncy */

.pop.in-view {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* Vanish variant — reversed pop, used when scrolled past */
.pop.out-view {
  opacity: 0;
  transform: translateY(-12px) scale(0.97);
  transition: opacity 0.3s ease, transform 0.3s ease;
}
```

### 2.4 Scroll-Driven Specific Animations

Beyond simple reveals, these scroll-driven effects run on specific sections:

**Hero headline word split:**
Each word of the hero headline is wrapped in a `<span>` and reveals with a 60ms stagger. On page load only (not on scroll re-entry). Words slide up from `translateY(100%)` with `overflow: hidden` on the parent — looks like words printing onto the page.

```css
.word-reveal-parent { overflow: hidden; display: inline-block }
.word { display: inline-block; transform: translateY(100%); opacity: 0 }
.word.typed { transform: translateY(0); opacity: 1;
              transition: transform 0.5s cubic-bezier(0.16,1,0.3,1),
                          opacity 0.4s ease }
```

**Provider pill slide-in:**
The three provider pills (bKash, Nagad, Rocket) slide in from the left, center, and right respectively — not all from the same direction. Left-pill: `translateX(-40px)`. Center-pill: `translateY(20px)`. Right-pill: `translateX(40px)`.

**Data flow module cascade:**
Each module row in the 8-module flow section reveals with a 100ms stagger, top to bottom. Combined with the connector lines between them drawing in using `stroke-dashoffset` animation.

**Dashboard mockup on hero:**
The balance cards in the hero mockup animate in sequentially after a 400ms delay (after headline loads). Order: Shared Cash → bKash → Nagad → Rocket → Alert strip. Each card pops in with the spring cubic-bezier at 120ms intervals.

**Scenario cards:**
On the scenarios section, cards pop in from `scale(0.92) translateY(24px)` with a stagger — creating the feeling of items appearing on a table.

**Role cards:**
Same pop-in, but from alternating sides. Row 1 (Agent, Field, Area): slide from left. Row 2 (Ops, Risk, Management): slide from right. Both rows stagger internally.

### 2.5 Scroll Parallax

**One parallax effect only** — the hero section's stamped watermark text (a large barely-visible "LIQUIDITY" behind the headline) moves at `0.3× scroll speed`, creating a slow drift as you scroll into the providers section.

No other parallax. Multiple parallax layers is an AI-generated default.

### 2.6 Hover Microinteractions

```css
/* Provider pills — border thickens, label gets heavier */
.provider-pill { border: 1.5px solid var(--border); transition: border-color 0.2s, transform 0.2s }
.provider-pill:hover { border-color: [provider-color]; transform: translateY(-3px) }

/* Role cards — background shifts one step warmer */
.role-card { transition: background 0.2s, border-color 0.2s, transform 0.25s }
.role-card:hover { background: var(--surface-raised); border-color: var(--border-strong); transform: translateY(-4px) }

/* Get Started button — no glow, no neon. Just a slight translate + color deepen */
.btn-primary { transition: transform 0.2s, background 0.2s }
.btn-primary:hover { transform: translateY(-2px); background: var(--accent-text) }

/* Flow module nodes — border-left appears in module's color */
.flow-node { border-left: 3px solid transparent; transition: border-color 0.2s }
.flow-node:hover { border-left-color: [node-color] }
```

### 2.7 Easing Reference

```
Standard reveal:   cubic-bezier(0.16, 1, 0.3, 1)   — fast decelerate (Expo Out)
Pop-up entry:      cubic-bezier(0.34, 1.56, 0.64, 1) — spring with overshoot
Pop vanish:        cubic-bezier(0.4, 0, 1, 1)        — fast ease-in (accelerate out)
Hover:             cubic-bezier(0.2, 0, 0, 1)         — smooth decelerate
```

---

## 3. Page Structure

The page has **6 sections** only. No more. Short, bold, non-repetitive.

```
1. NAV
2. HERO         — Headline + CTA + tilted dashboard mockup
3. PROVIDERS    — Three provider identities side by side
4. ROLES        — Six roles in a grid
5. DATA FLOW    — 8-module pipeline
6. SCENARIOS    — Four demo stories
7. CTA CLOSING  — Single large "Get Started"
8. FOOTER
```

---

## 4. Section Specifications

---

### Section 1: Navigation

**Height:** 60px fixed, always visible  
**Background:** `var(--canvas)` with `border-bottom: 1px solid var(--border)`  
**No blur, no transparency, no backdrop-filter**

**Left:** Logo mark (12×12px square stamp icon in `var(--accent)`) + platform name in Inter 600 18px  
**Right:** Single "Get Started" button

**Get Started button styling:**
```
background:    var(--accent)         → deep ink blue
color:         #FFFFFF
padding:       9px 22px
border-radius: 8px
font-size:     14px
font-weight:   600
border:        none
```

**Nav behavior:** On scroll past 80px, a `1px solid var(--border)` bottom border appears (it's already there but becomes visible against the slightly different hero background). No other scroll behavior.

---

### Section 2: Hero

**Full viewport height.** Canvas background `var(--canvas)`.

**Background element:** A large watermark text — the word "LIQUIDITY" — at 240px Fraunces 900, color `var(--ink)` (barely visible), centered behind the headline. This scrolls at 0.3× speed (parallax). It is not readable text — it is texture.

**Layout:**
```
[centered column, max-width 800px]

LABEL: "bKash presents SUST CSE Carnival 2026"
       11px · Inter 500 · var(--text-muted) · letter-spacing 0.08em · uppercase

H1:    "One View.        ← line 1, word-split animated
        Three Providers.  ← line 2
        Zero Confusion."  ← line 3

       80px · Fraunces 900 · var(--text-primary) · tracking -0.04em
       Line 2 "Three Providers." gets a 3px underline in var(--accent)
       This is the only decorative mark on the headline.

SUB:   "Unified liquidity intelligence for Bangladesh's mobile money agents."
       20px · Inter 400 · var(--text-body) · max-width 480px · margin auto

CTA:   [ Get Started → ]
       Single button · centered · 16px · padding 14px 36px

TAGLINE below button:
       "No credentials needed · pick a role and explore"
       12px · Inter 400 · var(--text-muted)
```

**Hero Visual — Dashboard Mockup:**
Below the CTA, a `max-width: 940px` centered mockup of the dashboard.

Transform: `perspective(1400px) rotateX(10deg) rotateY(-3deg)` — subtle tilt, reads as 3D without being gimmicky.

Animation on load: slides up from `translateY(60px)` to final position over 800ms with `cubic-bezier(0.16,1,0.3,1)`, starting after a 300ms delay (after headline words finish printing).

**Mockup structure:**
```
┌─────────────────────────────────────────────────────────┐  ← border: 1.5px solid var(--border)
│ TOPBAR: [●●●] OUTLET-001 · Dhaka North · Dashboard     │  ← bg: var(--surface)
├──────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │▄ Shared Cash │ │▄ bKash       │ │▄ Nagad        │ │▄ Rocket      │ │
│ │ ৳ 85,000     │ │ ৳ 42,000    │ │ ৳ 31,000      │ │ — —          │ │
│ │ ● FRESH      │ │ ⚠ ~2h left  │ │ ● FRESH       │ │ ✕ MISSING    │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │ 🔴 bKash · Unusual activity · 5 transactions ≈ ৳1,000 · HIGH │   │
│ └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

Card details:
- Card backgrounds: `var(--surface)` warm off-white
- Each card has a `3px top border` in the provider brand color
- Cash card: `var(--cash)` green top border
- bKash card: `var(--bkash)` top border
- Nagad card: `var(--nagad)` top border
- Rocket card: `var(--danger)` top border (missing state)
- Balance amounts: `JetBrains Mono 20px var(--text-primary)`
- Cards animate in sequentially (120ms stagger) after the mockup itself appears
- Alert strip: `background: #FEF2F2` · `border: 1px solid #FECACA` · `var(--danger)` text

**No glow around the mockup.** It sits on the canvas with a single clean border.

---

### Section 3: Providers

**Purpose:** Show the three provider identities as peers — separate, equal, never merged.

**Layout:** Full-width centered row.

```
[Shared Cash]  ·  [bKash]  ·  [Nagad]  ·  [Rocket]
```

Each is a pill:
```
padding:       16px 28px
border-radius: 100px
background:    var(--surface)
border:        1.5px solid var(--border)
font-size:     18px · Inter 700
```

Left of each label: a 12×12px circle in the provider's color.

Separators between them: `·` in `var(--text-faint)`, 24px.

**Animation:** The four pills slide in from their respective directions with a stagger. Cash pill slides from left. bKash from left-center. Nagad from right-center. Rocket from right. All with the `pop` cubic-bezier.

Below the pills, in small uppercase text:
```
"Provider balances are always separate — never summed"
11px · Inter 500 · var(--text-muted) · letter-spacing 0.08em
```

---

### Section 4: Roles

**Section label:** `WHO USES IT` (uppercase, 11px, `var(--accent)`, tracked)  
**Section title:** Two lines, Fraunces 800, 56px:
```
"Every stakeholder.
Their own view."
```

**Subtitle:** `"Role-based access — each user sees exactly what they need to act."` — 18px Inter 400 `var(--text-body)`.

**Grid:** 3 columns × 2 rows. `gap: 16px`.

**Card spec:**
```
background:    var(--surface)
border:        1.5px solid var(--border)
border-radius: 12px
padding:       28px
```

**Role icon:** 44×44px square, `border-radius: 10px`, background is a 10% tint of the role's color. Contains a single character glyph or simple shape — not an emoji, not an SVG illustration.

```
Agent:         icon bg rgba(29,95,168,0.08)   char: ◈   color: var(--accent)
Field Officer: icon bg rgba(212,84,26,0.08)   char: ⊞   color: var(--nagad)
Area Manager:  icon bg rgba(45,107,74,0.08)   char: ⬡   color: var(--cash)
Provider Ops:  icon bg rgba(192,16,96,0.08)   char: ◉   color: var(--bkash)
Risk Analyst:  icon bg rgba(185,28,28,0.08)   char: ⚑   color: var(--danger)
Management:    icon bg rgba(26,58,138,0.08)   char: ▦   color: var(--accent-text)
```

**Card content:**
- Role name: 16px Inter 700 `var(--text-primary)`
- One-line description: 13px Inter 400 `var(--text-muted)`
- 2–3 capability tags: 10px Inter 600 `var(--text-muted)` on `var(--surface-raised)` background, `border-radius: 4px`, `padding: 3px 8px`

**Animation:**
- Row 1 (Agent, Field, Area): pop in from `translateX(-32px) scale(0.96)`, staggered 80ms apart
- Row 2 (Ops, Risk, Mgmt): pop in from `translateX(32px) scale(0.96)`, staggered 80ms apart
- Both rows trigger when the section label crosses the 15% viewport threshold
- On scroll past: vanish with `scale(0.97) opacity(0)` in 250ms

---

### Section 5: Data Flow

**Section label:** `UNDER THE HOOD`  
**Section title:**
```
"8 modules.
One connected story."
```
Fraunces 800, 56px.

**Structure:** Vertical pipeline. Not a horizontal flow (horizontal flows break on mobile and look like every other flowchart). This reads top-to-bottom, matching the actual data flow direction.

Each module is a horizontal row:

```
┌─────────────────────────────────────────────────────────┐
│ [number] [module name]           [one-line description] │
└─────────────────────────────────────────────────────────┘
```

- Row background: alternates between `var(--canvas)` and `var(--surface)` — no borders between rows except the outer container border
- Number: `JetBrains Mono 11px var(--text-faint)` — `01`, `02`, etc.
- Module name: `Inter 600 16px var(--text-primary)`
- Description: `Inter 400 13px var(--text-muted)` right-aligned on desktop, below on mobile
- Left accent: `4px solid [module-color]` on the left edge of each row

**Module color assignments:**
```
01 INGEST:    var(--accent)      deep blue
02 QUALITY:   var(--warning)     amber
03 LEDGER:    var(--cash)        green
04 LIQUIDITY: var(--danger)      red
05 ANOMALY:   var(--nagad)       orange
06 ALERT:     var(--bkash)       magenta
07 CASE:      var(--rocket)      purple
08 HUMAN:     var(--success)     green
```

**Connector between rows:** A `1px solid var(--border)` horizontal rule between each row pair — not an arrow. Arrows are a generic diagram default. The vertical stacking implies the flow.

**Animation:**
- Each row reveals independently with a 100ms stagger, top to bottom
- `translateY(20px) opacity(0)` → `translateY(0) opacity(1)`
- The outer container border draws in with a CSS `clip-path` animation: from `inset(0 100% 0 0)` to `inset(0 0% 0 0)` over 400ms, triggering when the section label hits the viewport

---

### Section 6: Scenarios

**Section label:** `DEMO SCENARIOS`  
**Section title:**
```
"Four stories.
Fully live."
```

**Grid:** 2 columns × 2 rows. `gap: 20px`. Cards are slightly taller than role cards.

**Card spec:**
```
background:    var(--surface)
border:        1.5px solid var(--border)
border-radius: 12px
padding:       36px
position:      relative
overflow:      hidden
```

**Watermark letter:** `A`, `B`, `C`, `D` — Fraunces 900, `160px`, `opacity: 0.04`, `var(--text-primary)`, positioned `bottom: -24px, right: 20px`. This is the only decorative element on each card.

**Card content (top to bottom):**
- Scenario tag: `10px Inter 700 uppercase tracked` in a colored chip (scenario-specific color)
- Title: `24px Fraunces 800 var(--text-primary)` — 3–4 words maximum
- Description: `14px Inter 400 var(--text-muted)` — 2 sentences maximum

**Scenario tag colors:**
```
A (Hidden Shortage):   bg #ECFDF5  text var(--success)   border rgba(26,122,63,0.2)
B (Unusual Activity):  bg #FFFBEB  text var(--warning)   border rgba(160,92,10,0.2)
C (Inconsistency):     bg #F5F3FF  text var(--rocket)    border rgba(107,37,120,0.2)
D (Coordination):      bg #EFF6FF  text var(--accent)    border rgba(29,95,168,0.2)
```

**Animation:**
- Cards pop in with `scale(0.94) translateY(24px)` → `scale(1) translateY(0)` using the spring cubic-bezier
- Stagger: A (0ms), B (100ms), C (200ms), D (300ms)
- On scroll past: vanish with `scale(0.96) opacity(0)` — all four simultaneously, no stagger on exit (exits should be faster and unified)

---

### Section 7: Closing CTA

**Background:** `var(--surface)` — one shade warmer than the canvas. This creates a natural "end of page" signal without a dramatic color change.

**Border top:** `1px solid var(--border)`

**Content (centered, max-width 640px):**
```
EYEBROW: "Ready to explore?"
         13px · Inter 500 · var(--text-muted) · uppercase · tracked

TITLE:   "See it live.
          Pick your role."
         64px · Fraunces 800 · var(--text-primary) · -0.04em tracking
         "Pick your role." in var(--accent) — only this phrase, not gradient

SUB:     "No credentials. No setup. Choose a role and walk through the full platform."
         18px · Inter 400 · var(--text-body)

CTA:     [ Get Started → ]
         Same styling as nav CTA but larger: 16px · padding 14px 36px

NOTE:    "Synthetic data only · No real accounts or funds"
         11px · Inter 400 · var(--text-faint) · margin-top 20px
```

**Animation:** The entire block pops in as a unit from `translateY(32px)`. The CTA button pops in 200ms later with the spring bezier.

---

### Section 8: Footer

**Minimal.** `border-top: 1px solid var(--border)`. `padding: 28px 64px`.

```
LEFT:  Logo mark + "LiquidEye" (or platform name)
RIGHT: "bKash presents SUST CSE Carnival 2026 · Synthetic data only"
       11px · Inter 400 · var(--text-muted)
```

No social links, no sitemap, no dark mode toggle.

---

## 5. What to Avoid (Anti-Pattern Reference)

Keep this list open during implementation. If any of these appear, remove them immediately.

| Anti-pattern | Why it's a tell | What to do instead |
|---|---|---|
| `backdrop-filter: blur()` on any element | Glassmorphism — the #1 AI design default | Use solid `var(--surface)` backgrounds |
| Neon or electric accent colors | Looks like dark-mode SaaS from 2021 | Use `var(--accent)` deep ink blue only |
| Rainbow/multi-color text gradient on hero | Every AI landing page does this | Fraunces headline in solid `var(--text-primary)` |
| Floating cards with `box-shadow` | Generic depth pattern | Border `1.5px solid var(--border)` only |
| Mesh or noise gradient backgrounds | AI-generated aesthetic default | Solid `var(--canvas)` only |
| `01 / 02 / 03` decorative numbering outside boxes | Faux-editorial cliché | Module numbers inside the row, `JetBrains Mono` small |
| Multiple parallax layers | Overdesigned, nauseating on mobile | One parallax only (the watermark) |
| Animated counter numbers | The SaaS metric-flex default | Static, large, typographic |
| Scroll-triggered video autoplay | Distracting and heavy | Static mockup with sequential card animation |
| Hero with 3 secondary CTAs | Hedging — dilutes primary action | One CTA: "Get Started" |
| Pure white `#FFFFFF` surfaces | Cold, sterile, AI-default | `var(--canvas) = #F5F2EE` throughout |
| `transition: all` | Performance and flash risk | Explicit property transitions only |

---

## 6. Scroll Animation JS Architecture

```javascript
// IntersectionObserver — bidirectional (in AND out)
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Element entering viewport — add in-view, remove out-view
      entry.target.classList.add('in-view');
      entry.target.classList.remove('out-view');
    } else {
      // Element leaving viewport — determine direction
      const rect = entry.boundingClientRect;
      if (rect.top < 0) {
        // Scrolled past (top edge left viewport) — vanish upward
        entry.target.classList.add('out-view');
        entry.target.classList.remove('in-view');
      } else {
        // Scrolled back up (bottom edge left viewport) — reset to pre-reveal state
        entry.target.classList.remove('in-view');
        entry.target.classList.remove('out-view');
        // This makes the reveal re-trigger on next downscroll
      }
    }
  });
}, {
  threshold: 0.15,
  rootMargin: '0px 0px -40px 0px'
});

// Apply to all reveal elements
document.querySelectorAll('.reveal, .pop').forEach(el => {
  revealObserver.observe(el);
});

// Hero word split — runs once on load
function animateHeroWords() {
  const words = document.querySelectorAll('.hero-word');
  words.forEach((word, i) => {
    setTimeout(() => {
      word.classList.add('typed');
    }, i * 60 + 200); // 200ms initial delay, 60ms per word
  });
}
document.addEventListener('DOMContentLoaded', animateHeroWords);

// Watermark parallax — one element only
const watermark = document.querySelector('.hero-watermark');
window.addEventListener('scroll', () => {
  if (!watermark) return;
  watermark.style.transform = `translateX(-50%) translateY(${window.scrollY * 0.3}px)`;
}, { passive: true });

// Dashboard mockup card stagger — triggered once
const mockupObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const cards = entry.target.querySelectorAll('.balance-card');
      cards.forEach((card, i) => {
        setTimeout(() => card.classList.add('in-view'), i * 120 + 400);
      });
      mockupObserver.unobserve(entry.target); // Only fires once
    }
  });
}, { threshold: 0.3 });
const mockup = document.querySelector('.dashboard-mockup');
if (mockup) mockupObserver.observe(mockup);
```

---

## 7. Performance Requirements

- **No JavaScript animation libraries.** All animations use CSS transitions + `IntersectionObserver`. No GSAP, no Framer Motion, no Anime.js. The landing page must load fast.
- **Fonts preloaded:** Both Fraunces and Inter loaded via `<link rel="preload">` in `<head>` before render. JetBrains Mono is display-optional (can load after).
- **No hero video.** The 3D mockup is pure HTML/CSS — no canvas, no WebGL.
- **Reduced motion:** All animations wrapped in `@media (prefers-reduced-motion: reduce)` fallback — transitions set to `0.01ms`. Never skip `opacity` entirely (content must still appear).

```css
@media (prefers-reduced-motion: reduce) {
  .reveal, .pop {
    transition: opacity 0.01ms !important;
    transform: none !important;
  }
  .hero-word {
    transition: opacity 0.01ms !important;
    transform: none !important;
  }
}
```

- **Images:** None on the landing page. All visuals are CSS + HTML.
- **Target LCP:** Under 1.2s (headline text is the largest content element).

---

## 8. Tech Stack for Landing Page

```
Framework:    Plain HTML + CSS + vanilla JS    → no framework overhead
              (or React component if the app uses React, as a route `/`)
Fonts:        Google Fonts — Fraunces, Inter, JetBrains Mono
Icons:        None (using Unicode glyphs for role icons)
Animation:    IntersectionObserver + CSS transitions only
Charts/3D:    None — dashboard mockup is styled HTML divs
```

If the app is built in React + Vite, the landing page lives at route `/` as a React component with `useEffect` for the observer setup. The observer logic is identical to the vanilla JS above.

---

## 9. Route Behavior

- `/` → Landing page (this document)
- All "Get Started" and "Enter Platform" buttons → `href="/login"`
- The nav CTA and the closing CTA both route to `/login`
- No other external links on the landing page

---

*Landing Page Design Plan v1.0 · July 2026*
*Platform: Multi-Provider Agent Liquidity & Coordination Platform*
*Event: bKash presents SUST CSE Carnival 2026*
