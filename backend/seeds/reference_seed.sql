-- =============================================================================
-- Reference / demo seed — deterministic and idempotent (ADR 0003).
-- Fixed UUIDs + ON CONFLICT DO NOTHING => safe to re-run, never duplicates.
-- SYNTHETIC DATA ONLY: no real phone/account numbers, names, PINs, OTPs, or
-- credentials (docs/schema.md §2.9, §13.19). Emails use the reserved .test TLD.
-- Sections mirror migrations 001 (identity), 002 (scenarios), 003 (anomaly rule),
-- 004 (templates + routing).
-- =============================================================================

-- ------------------------------------------------------------------ providers
INSERT INTO providers (provider_id, code, display_name, display_color) VALUES
  ('11111111-1111-1111-1111-111111111111', 'bkash',  'bKash',  '#E2136E'),
  ('22222222-2222-2222-2222-222222222222', 'nagad',  'Nagad',  '#F7941D'),
  ('33333333-3333-3333-3333-333333333333', 'rocket', 'Rocket', '#8C3494')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------- areas
INSERT INTO areas (area_id, parent_area_id, code, name, level) VALUES
  ('a0000000-0000-0000-0000-000000000001', NULL,
     'REG-DHK', 'Dhaka Region (synthetic)', 'region'),
  ('a0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
     'DIST-DHK-C', 'Central District (synthetic)', 'district'),
  ('a0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002',
     'AREA-MARKET', 'Market Area (synthetic)', 'area'),
  ('a0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000002',
     'AREA-RIVER', 'Riverside Area (synthetic)', 'area')
ON CONFLICT (code) DO NOTHING;

-- -------------------------------------------------------------------- outlets
INSERT INTO outlets (outlet_id, synthetic_code, display_name, area_id) VALUES
  ('0b000000-0000-0000-0000-000000000001', 'OUTLET-001', 'Demo Outlet 001 (Market)',
     'a0000000-0000-0000-0000-000000000003'),
  ('0b000000-0000-0000-0000-000000000002', 'OUTLET-002', 'Demo Outlet 002 (Riverside)',
     'a0000000-0000-0000-0000-000000000004')
ON CONFLICT (synthetic_code) DO NOTHING;

-- ----------------------------------------------------- outlet-provider accounts
INSERT INTO outlet_provider_accounts
  (outlet_provider_account_id, outlet_id, provider_id, synthetic_account_ref) VALUES
  ('e1000000-0000-0000-0000-000000000001', '0b000000-0000-0000-0000-000000000001',
     '11111111-1111-1111-1111-111111111111', 'ACCT-O1-BKASH'),
  ('e2000000-0000-0000-0000-000000000001', '0b000000-0000-0000-0000-000000000001',
     '22222222-2222-2222-2222-222222222222', 'ACCT-O1-NAGAD'),
  ('e3000000-0000-0000-0000-000000000001', '0b000000-0000-0000-0000-000000000001',
     '33333333-3333-3333-3333-333333333333', 'ACCT-O1-ROCKET'),
  ('e1000000-0000-0000-0000-000000000002', '0b000000-0000-0000-0000-000000000002',
     '11111111-1111-1111-1111-111111111111', 'ACCT-O2-BKASH')
ON CONFLICT ON CONSTRAINT uq_opa_outlet_provider DO NOTHING;

-- ----------------------------------------------- demo identities (auth + app)
-- Minimal synthetic auth identities (no credentials). On Supabase these may be
-- created through the admin API instead; here they support RLS verification.
INSERT INTO auth.users (id, email) VALUES
  ('d0000000-0000-0000-0000-000000000a01', 'agent.o1.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000a02', 'agent.o2.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000b01', 'bkash.ops.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000b02', 'nagad.ops.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000b03', 'rocket.ops.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000c01', 'area.mgr.bkash.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000d01', 'risk.bkash.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000e01', 'management.demo@example.test'),
  ('d0000000-0000-0000-0000-000000000f01', 'admin.demo@example.test')
ON CONFLICT (id) DO NOTHING;

INSERT INTO app_users (user_id, display_name, preferred_locale) VALUES
  ('d0000000-0000-0000-0000-000000000a01', 'Demo Agent (Outlet 001)', 'en'),
  ('d0000000-0000-0000-0000-000000000a02', 'Demo Agent (Outlet 002)', 'en'),
  ('d0000000-0000-0000-0000-000000000b01', 'Demo bKash Ops',          'en'),
  ('d0000000-0000-0000-0000-000000000b02', 'Demo Nagad Ops',          'en'),
  ('d0000000-0000-0000-0000-000000000b03', 'Demo Rocket Ops',         'en'),
  ('d0000000-0000-0000-0000-000000000c01', 'Demo Area Manager (bKash/Market)', 'bn'),
  ('d0000000-0000-0000-0000-000000000d01', 'Demo Risk Analyst (bKash)', 'en'),
  ('d0000000-0000-0000-0000-000000000e01', 'Demo Management',         'en'),
  ('d0000000-0000-0000-0000-000000000f01', 'Demo Admin',              'en')
ON CONFLICT (user_id) DO NOTHING;

-- Access scopes (role-shape constraint enforced by 001; a missing provider scope
-- is never a wildcard). Management/admin rows are deliberately un-provider-scoped.
INSERT INTO user_access_scopes (user_id, role, provider_id, area_id, outlet_id) VALUES
  -- agents: outlet-scoped combined context
  ('d0000000-0000-0000-0000-000000000a01', 'agent', NULL, NULL, '0b000000-0000-0000-0000-000000000001'),
  ('d0000000-0000-0000-0000-000000000a02', 'agent', NULL, NULL, '0b000000-0000-0000-0000-000000000002'),
  -- provider ops: provider-wide
  ('d0000000-0000-0000-0000-000000000b01', 'provider_ops', '11111111-1111-1111-1111-111111111111', NULL, NULL),
  ('d0000000-0000-0000-0000-000000000b02', 'provider_ops', '22222222-2222-2222-2222-222222222222', NULL, NULL),
  ('d0000000-0000-0000-0000-000000000b03', 'provider_ops', '33333333-3333-3333-3333-333333333333', NULL, NULL),
  -- area manager: provider + area limited
  ('d0000000-0000-0000-0000-000000000c01', 'area_manager', '11111111-1111-1111-1111-111111111111',
     'a0000000-0000-0000-0000-000000000003', NULL),
  -- risk analyst: provider-scoped
  ('d0000000-0000-0000-0000-000000000d01', 'risk_analyst', '11111111-1111-1111-1111-111111111111', NULL, NULL),
  -- management: aggregate role with NO provider scope (must not act as a wildcard)
  ('d0000000-0000-0000-0000-000000000e01', 'management', NULL, NULL, NULL),
  -- admin: demo/setup only
  ('d0000000-0000-0000-0000-000000000f01', 'admin', NULL, NULL, NULL)
ON CONFLICT ON CONSTRAINT uq_uas_assignment DO NOTHING;

-- --------------------------------------------------------- simulation scenarios
INSERT INTO simulation_scenarios
  (scenario_id, code, name, description, default_seed, default_config, validation_split) VALUES
  ('5c000000-0000-0000-0000-000000000000', 'normal',
     'Normal Operation', 'Baseline synthetic traffic with healthy feeds.', 1001,
     '{"expected": "no_alerts"}'::jsonb, 'demo'),
  ('5c000000-0000-0000-0000-00000000000a', 'scenario_a',
     'Hidden Shared-Cash Shortage',
     'Heavy bKash cash-out demand depletes shared physical cash while bKash e-money rises.',
     2001,
     '{"expected": "liquidity_alert", "target_provider": "bkash", "pressure_reserve": "shared_cash"}'::jsonb,
     'held_out'),
  ('5c000000-0000-0000-0000-00000000000b', 'scenario_b',
     'Liquidity Pressure with Unusual Activity',
     'Near-identical repeated amounts alongside falling shared cash.', 2002,
     '{"expected": "combined_alert", "cluster_provider": "bkash", "cluster_amount": "1000.00", "cluster_count": 6, "cluster_step_minutes": 2}'::jsonb, 'held_out'),
  ('5c000000-0000-0000-0000-00000000000c', 'scenario_c',
     'Data Inconsistency', 'Delayed/conflicting snapshots lower confidence and suppress alerts.', 2003,
     '{"expected": "data_quality", "cluster_provider": "bkash", "cluster_amount": "1000.00", "cluster_count": 6, "cluster_step_minutes": 2}'::jsonb, 'held_out'),
  ('5c000000-0000-0000-0000-00000000000d', 'scenario_d',
     'Coordinated Response and Closure', 'An alert is routed and resolved through a case lifecycle.', 2004,
     '{"expected": "case_closure"}'::jsonb, 'demo')
ON CONFLICT (code) DO NOTHING;

-- Correct stale Scenario A metadata created before transaction directions were
-- aligned with real agent cash movement. This keeps existing seeded databases
-- semantically consistent without modifying an applied migration.
UPDATE simulation_scenarios
SET name = 'Hidden Shared-Cash Shortage',
    description = 'Heavy bKash cash-out demand depletes shared physical cash while bKash e-money rises.',
    default_config = '{"expected": "liquidity_alert", "target_provider": "bkash", "pressure_reserve": "shared_cash"}'::jsonb,
    updated_at = now()
WHERE code = 'scenario_a';

-- ------------------------------------------------- active anomaly rule (MVP)
INSERT INTO anomaly_rules
  (anomaly_rule_id, code, pattern, version, name, description, configuration, is_active) VALUES
  ('a9000000-0000-0000-0000-000000000001', 'near_identical_amounts_v1', 'near_identical_amounts', 'v1',
     'Near-identical repeated amounts',
     'Flags several transactions of nearly the same amount within a short window for one provider/outlet for human review. Being flagged is not a determination of wrongdoing.',
     '{"window_minutes": 15, "amount_tolerance_pct": 2.0, "minimum_count": 5, "minimum_distinct_parties": 1}'::jsonb,
     true),
  ('a9000000-0000-0000-0000-000000000002', 'velocity_spike_v1', 'velocity_spike', 'v1',
     'Transaction velocity spike',
     'Flags a short-window transaction count exceeding the outlet''s same-hour baseline by N standard deviations for human review. Being flagged is not a determination of wrongdoing.',
     '{"window_minutes": 10, "std_dev_threshold": 2.0, "minimum_baseline_windows": 3, "minimum_spike_count": 8}'::jsonb,
     true),
  ('a9000000-0000-0000-0000-000000000003', 'balance_inconsistency_v1', 'balance_inconsistency', 'v1',
     'Balance inconsistency / data conflict',
     'Flags when a provider balance feed disagrees with the transaction log or with itself at the same timestamp. Framed as a data-quality finding, not wallet integrity loss.',
     '{"min_discrepancy_amount": 100.0, "min_discrepancy_pct": 0.5, "staleness_soft_minutes": 120}'::jsonb,
     true)
ON CONFLICT (code) DO NOTHING;

-- --------------------------------------------- explanation templates (EN/BN/BN-Latn)
INSERT INTO explanation_templates
  (explanation_template_id, template_key, locale, version, alert_type,
   situation_template, evidence_template, uncertainty_template, next_step_template, benign_context_template) VALUES
  -- Combined alert (demo) — English
  ('7e000000-0000-0000-0000-0000000000e1', 'combined_default', 'en', 1, 'combined',
     'Possible liquidity pressure on {provider} at {outlet} may require review.',
     '{evidence_summary}',
     'This pattern may reflect normal event-driven demand rather than a problem.',
     'Review the listed synthetic transactions and coordinate through the authorized process.',
     'This may reflect normal pre-event demand.'),
  -- Combined alert (demo) — Bangla
  ('7e000000-0000-0000-0000-0000000000b1', 'combined_default', 'bn', 1, 'combined',
     '{outlet}-{provider} এ সম্ভাব্য তারল্য চাপ পর্যালোচনার প্রয়োজন হতে পারে।',
     '{evidence_summary}',
     'এই ধরণ স্বাভাবিক চাহিদার কারণেও হতে পারে, তাই এটি নিশ্চিত নয়।',
     'তালিকাভুক্ত সিমুলেটেড লেনদেনগুলো পর্যালোচনা করুন এবং অনুমোদিত প্রক্রিয়ায় সমন্বয় করুন।',
     'এটি স্বাভাবিক উৎসব-পূর্ব চাহিদার প্রতিফলন হতে পারে।'),
  -- Combined alert (demo) — Banglish
  ('7e000000-0000-0000-0000-0000000000b2', 'combined_default', 'bn_latn', 1, 'combined',
     '{outlet}-{provider} e possible liquidity pressure review korte hote pare.',
     '{evidence_summary}',
     'Ei pattern ta normal demand er karone o hote pare, tai eta certain na.',
     'Listed synthetic transaction gulo review korun ebong authorized process e coordinate korun.',
     'Eta normal pre-event demand er reflection hote pare.'),
  -- Liquidity alert — English
  ('7e000000-0000-0000-0000-0000000000e2', 'liquidity_default', 'en', 1, 'liquidity',
     'A reserve at {outlet} may approach a shortage around {shortage_at}.',
     '{evidence_summary}',
     'The estimate has a confidence band; timing may shift with new data.',
     'Review the reserve and plan replenishment through the authorized process.',
     NULL),
  -- Anomaly alert — English
  ('7e000000-0000-0000-0000-0000000000e3', 'anomaly_default', 'en', 1, 'anomaly',
     'An unusual repeated-amount pattern on {provider} at {outlet} was flagged for review.',
     '{evidence_summary}',
     'Being flagged is not proof of wrongdoing; it indicates the pattern is unusual.',
     'Review the listed synthetic transactions before any coordination.',
     'This may reflect normal event-driven demand.'),
  -- Data-quality advisory — English
  ('7e000000-0000-0000-0000-0000000000e4', 'data_quality_default', 'en', 1, 'data_quality',
     'Data for {provider} at {outlet} is {status}; figures may be less certain.',
     '{evidence_summary}',
     'Confidence is reduced until fresh data arrives.',
     'Treat current figures cautiously and wait for updated feeds.',
     NULL),
  -- Liquidity alert — Bangla
  ('7e000000-0000-0000-0000-0000000000b3', 'liquidity_default', 'bn', 1, 'liquidity',
     '{outlet}-এর একটি রিজার্ভ প্রায় {shortage_at} নাগাদ ঘাটতির দিকে যেতে পারে।',
     '{evidence_summary}',
     'এই অনুমানে একটি কনফিডেন্স ব্যান্ড রয়েছে; নতুন তথ্যে সময় পরিবর্তিত হতে পারে।',
     'রিজার্ভটি পর্যালোচনা করুন এবং অনুমোদিত প্রক্রিয়ায় পুনরায় সরবরাহের পরিকল্পনা করুন।',
     NULL),
  -- Liquidity alert — Banglish
  ('7e000000-0000-0000-0000-0000000000b4', 'liquidity_default', 'bn_latn', 1, 'liquidity',
     '{outlet} er ekti reserve prai {shortage_at} nagad shortage er dike jete pare.',
     '{evidence_summary}',
     'Ei estimate e ekti confidence band ache; notun data te timing change hote pare.',
     'Reserve ti review korun ebong authorized process e replenishment plan korun.',
     NULL),
  -- Anomaly alert — Bangla
  ('7e000000-0000-0000-0000-0000000000b5', 'anomaly_default', 'bn', 1, 'anomaly',
     '{outlet}-এ {provider}-এর উপর একটি অস্বাভাবিক পুনরাবৃত্ত-পরিমাণের ধরন পর্যালোচনার জন্য চিহ্নিত হয়েছে।',
     '{evidence_summary}',
     'চিহ্নিত হওয়া কোনো অন্যায়ের প্রমাণ নয়; এটি নির্দেশ করে যে ধরনটি অস্বাভাবিক।',
     'যেকোনো সমন্বয়ের আগে তালিকাভুক্ত সিমুলেটেড লেনদেনগুলো পর্যালোচনা করুন।',
     'এটি স্বাভাবিক উৎসব-চালিত চাহিদার প্রতিফলন হতে পারে।'),
  -- Anomaly alert — Banglish
  ('7e000000-0000-0000-0000-0000000000b6', 'anomaly_default', 'bn_latn', 1, 'anomaly',
     '{outlet} e {provider} er upor ekti unusual repeated-amount pattern review er jonno flag kora hoyeche.',
     '{evidence_summary}',
     'Flag howa kono wrongdoing er proof na; eta indicate kore je pattern ta unusual.',
     'Kono coordination er age listed synthetic transaction gulo review korun.',
     'Eta normal event-driven demand er reflection hote pare.')
ON CONFLICT (template_key, locale, version) DO NOTHING;

-- ---------------------------------------------------------------- routing rules
INSERT INTO routing_rules
  (routing_rule_id, name, provider_id, area_id, alert_type, minimum_severity, target_role, priority) VALUES
  ('40000000-0000-0000-0000-000000000001', 'Global fallback',
     NULL, NULL, NULL, 'info', 'field_officer', 1000),
  ('40000000-0000-0000-0000-000000000002', 'bKash provider ops',
     '11111111-1111-1111-1111-111111111111', NULL, NULL, 'low', 'provider_ops', 100),
  ('40000000-0000-0000-0000-000000000003', 'Nagad provider ops',
     '22222222-2222-2222-2222-222222222222', NULL, NULL, 'low', 'provider_ops', 100),
  ('40000000-0000-0000-0000-000000000004', 'Rocket provider ops',
     '33333333-3333-3333-3333-333333333333', NULL, NULL, 'low', 'provider_ops', 100),
  ('40000000-0000-0000-0000-000000000005', 'High-severity risk escalation',
     NULL, NULL, NULL, 'high', 'risk_analyst', 50)
ON CONFLICT (routing_rule_id) DO NOTHING;
