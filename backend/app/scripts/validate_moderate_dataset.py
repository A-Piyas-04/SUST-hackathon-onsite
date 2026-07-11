"""Validate generated moderate-demo CSVs before any database write."""
from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]; DATA=ROOT/'data'/'generated'/'moderate_demo'; REPORT=DATA/'validation-report.json'
def load(name):
    with (DATA/f'{name}.csv').open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8')); checks=[]
    def check(name,ok,detail): checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    for fn,h in manifest['file_hashes'].items(): check('hash:'+fn,hashlib.sha256((DATA/fn).read_bytes()).hexdigest()==h,h)
    outlets=load('outlets'); accounts=load('outlet_provider_accounts'); tx=load('transactions'); runs=load('simulation_runs'); faults=load('fault_injections'); q=load('data_quality_assessments'); qi=load('data_quality_issues'); cash=load('cash_balance_snapshots'); pbal=load('provider_balance_snapshots'); proj=load('liquidity_projections'); flags=load('anomaly_flags'); evidence=load('anomaly_evidence_items'); links=load('anomaly_flag_transactions'); alerts=load('alerts'); cases=load('cases'); hist=load('case_status_history'); assign=load('case_assignments'); metrics=load('metric_results')
    providers={a['provider_id'] for a in accounts}; check('exactly_three_providers',len(providers)==3,str(sorted(providers)))
    check('target_outlets',len(outlets)==5,f'{len(outlets)} outlets')
    acct_pairs={(a['outlet_id'],a['provider_id']) for a in accounts}; check('one_account_per_outlet_provider',len(accounts)==15 and len(acct_pairs)==15,'15 unique pairs')
    tx_outlets={r['outlet_id'] for r in tx}; check('every_outlet_active',tx_outlets=={o['outlet_id'] for o in outlets},f'{len(tx_outlets)} outlets')
    check('moderate_transaction_volume',3000<=len(tx)<=5000,str(len(tx)))
    check('transaction_types',set(r['transaction_type'] for r in tx)=={'cash_in','cash_out','payment','refund','adjustment'},str(Counter(r['transaction_type'] for r in tx)))
    check('transaction_statuses',set(r['status'] for r in tx)=={'completed','pending','failed','reversed'},str(Counter(r['status'] for r in tx)))
    amap={a['outlet_provider_account_id']:(a['outlet_id'],a['provider_id']) for a in accounts}; check('transaction_account_consistency',all(amap[r['outlet_provider_account_id']]==(r['outlet_id'],r['provider_id']) for r in tx),'all rows match')
    check('positive_two_decimal_money',all(Decimal(r['amount'])>0 and Decimal(r['amount']).as_tuple().exponent==-2 for r in tx),'all transaction amounts')
    times=[r['occurred_at'] for r in tx]+[r['observed_at'] for r in cash+pbal]; check('utc_timestamps',all(x.endswith('Z') and datetime.fromisoformat(x.replace('Z','+00:00')).utcoffset().total_seconds()==0 for x in times),f'{len(times)} timestamps')
    check('fixed_date_coverage',(max(datetime.fromisoformat(r['occurred_at'].replace('Z','+00:00')) for r in tx)-min(datetime.fromisoformat(r['occurred_at'].replace('Z','+00:00')) for r in tx)).days>=8,'9 simulated dates')
    check('cash_history_separate',len(cash)==900 and all('provider_id' not in r for r in cash),'900 shared-cash snapshots')
    check('provider_history_separate',len(pbal)==2701 and all(amap[r['outlet_provider_account_id']]==(r['outlet_id'],r['provider_id']) for r in pbal),'2701 provider snapshots')
    dup=defaultdict(set)
    for r in pbal: dup[(r['outlet_id'],r['provider_id'],r['observed_at'])].add(r['balance'])
    check('conflicting_snapshots_coexist',any(len(v)>1 for v in dup.values()),'same reserve/time has distinct balances')
    run_counts=Counter(r['scenario_id'] for r in runs); check('scenario_runs',len(runs)==10 and len(run_counts)==5 and set(run_counts.values())=={2},str(run_counts))
    check('scenario_c_fault_types',set(r['fault_type'] for r in faults)=={'delay','missing_feed','missing_field','conflicting_balance','malformed_payload'},str(Counter(r['fault_type'] for r in faults)))
    check('quality_volume',30<=len(q)<=50 and 12<=len(qi)<=20,f'{len(q)} assessments, {len(qi)} issues')
    check('projection_volume_samples',50<=len(proj)<=80 and all(12<=int(r['sample_count'])<=48 for r in proj),f'{len(proj)} projections')
    evid={r['anomaly_flag_id'] for r in evidence}; linked={r['anomaly_flag_id'] for r in links}; check('anomaly_evidence',all(r['anomaly_flag_id'] in evid and r['anomaly_flag_id'] in linked for r in flags),f'{len(flags)} flags')
    check('actionable_benign_context',all(r['plausible_benign_explanation'] for r in flags if r['disposition'] in ('requires_review','confirmed_unusual')),'all actionable flags')
    check('suppressed_has_reason_quality',all(r['suppression_reason'] and r['data_quality_assessment_id'] for r in flags if r['disposition']=='suppressed_data_quality'),'all suppressed flags')
    source_alerts={r['alert_id'] for n in ('alert_liquidity_projections','alert_anomaly_flags','alert_quality_assessments') for r in load(n)}; check('typed_alert_sources',all(r['alert_id'] in source_alerts for r in alerts),f'{len(alerts)} alerts')
    check('case_volume',12<=len(cases)<=18,f'{len(cases)} cases')
    legal={(None,'open'),('open','acknowledged'),('acknowledged','escalated'),('escalated','resolved')}; check('legal_case_transitions',all(((r['from_status'] or None),r['to_status']) in legal for r in hist),f'{len(hist)} transitions')
    bycase=defaultdict(list)
    for r in hist: bycase[r['case_id']].append(r)
    check('case_current_state',all(sorted(bycase[c['case_id']],key=lambda x:x['changed_at'])[-1]['to_status']==c['status'] for c in cases),'all current states agree')
    latest_owner={r['case_id']:r['assigned_to_user_id'] for r in assign}; check('case_current_owner',all(latest_owner[c['case_id']]==c['current_owner_user_id'] for c in cases),'all owners agree')
    check('resolved_summary',all(c['resolution_summary'] and c['resolved_at'] for c in cases if c['status']=='resolved'),'all resolved cases')
    external=' '.join(r['synthetic_transaction_ref']+' '+r['synthetic_party_ref'] for r in tx); check('opaque_synthetic_refs',all(r['synthetic_transaction_ref'].startswith('TXN-') and '-SYN-' in r['synthetic_transaction_ref'] and r['synthetic_party_ref'].startswith('PARTY-SYN-') for r in tx),'all references synthetic')
    prohibited=re.compile(r'fraud confirmed|fraudster|criminal|block this account|freeze funds|wallet refill|cross-provider wallet conversion',re.I); corpus=' '.join(str(v) for name in manifest['row_counts'] for r in load(name) for v in r.values()); check('prohibited_language_absent',not prohibited.search(corpus),'no prohibited phrases')
    expected={'anomaly_precision':Decimal('.8'),'anomaly_recall':Decimal('.8'),'anomaly_false_positive_rate':Decimal('.1'),'data_quality_handling_rate':Decimal('1'),'alert_explanation_coverage':Decimal('1'),'audit_completeness':Decimal('1'),'provider_denial_success_rate':Decimal('1'),'shortage_detection_lead_time':Decimal('180')}; check('metrics_recompute',all(Decimal(r['value'])==expected[r['metric_code']] for r in metrics),f'{len(metrics)} metric rows match deterministic evidence formulas')
    report={'validation_version':'1.0.0','manifest_sha256':hashlib.sha256((DATA/'manifest.json').read_bytes()).hexdigest(),'summary':{'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks)},'checks':checks}
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report['summary']))
    if report['summary']['failed']: raise SystemExit(1)
if __name__=='__main__':main()
