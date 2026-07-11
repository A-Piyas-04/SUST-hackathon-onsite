"""Deterministic Bangladesh-context moderate demo dataset (synthetic only)."""
from __future__ import annotations

import csv, hashlib, json, random, shutil, uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data'/'generated'/'moderate_demo'
NS=uuid.UUID('53d4d4fe-a987-5e60-a81f-230ac1bf0600')
MASTER_SEED=2026071201
BASE=datetime(2026,6,26,0,0,tzinfo=timezone.utc)
END=BASE+timedelta(days=9)
PROVIDERS={'bkash':'11111111-1111-1111-1111-111111111111','nagad':'22222222-2222-2222-2222-222222222222','rocket':'33333333-3333-3333-3333-333333333333'}
SCENARIOS={'normal':'5c000000-0000-0000-0000-000000000000','scenario_a':'5c000000-0000-0000-0000-00000000000a','scenario_b':'5c000000-0000-0000-0000-00000000000b','scenario_c':'5c000000-0000-0000-0000-00000000000c','scenario_d':'5c000000-0000-0000-0000-00000000000d'}
SEEDS={'normal':[20261001,20261002],'scenario_a':[20262001,20262002],'scenario_b':[20263001,20263002],'scenario_c':[20264001,20264002],'scenario_d':[20265001,20265002]}
USERS={'bkash':'d0000000-0000-0000-0000-000000000b01','nagad':'d0000000-0000-0000-0000-000000000b02','rocket':'d0000000-0000-0000-0000-000000000b03'}
RISK='d0000000-0000-0000-0000-000000000d01'
RULE='a9000000-0000-0000-0000-000000000001'

def sid(kind,n): return str(uuid.uuid5(NS,f'{kind}:{n}'))
def ts(x): return x.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
def money(x): return str(Decimal(str(x)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
def jd(x): return json.dumps(x,separators=(',',':'),sort_keys=True,ensure_ascii=False)

class Dataset:
    def __init__(self): self.rows=defaultdict(list)
    def add(self,t,**r): self.rows[t].append(r); return r
    def write(self):
        if OUT.exists(): shutil.rmtree(OUT)
        OUT.mkdir(parents=True)
        hashes={}
        for table, rows in self.rows.items():
            path=OUT/f'{table}.csv'; fields=list(rows[0])
            with path.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
            hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        manifest={'generator_version':'1.0.0','schema_version':'007','master_seed':MASTER_SEED,
          'scenario_seeds':SEEDS,'date_range':{'start':ts(BASE),'end':ts(END)},
          'generated_at':'2026-07-12T00:00:00Z','database_compatibility_target':'PostgreSQL migrations 001-007',
          'row_counts':{k:len(v) for k,v in self.rows.items()},'file_hashes':hashes,
          'assumptions':['All records are synthetic','Provider proportions are simulation assumptions, not market share','Asia/Dhaka activity is stored in UTC','No financial action is represented']}
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        return manifest

def generate():
    d=Dataset(); rng=random.Random(MASTER_SEED)
    area_names=[('DHAKA-NORTH-SYN','Dhaka North'),('DHAKA-SOUTH-SYN','Dhaka South'),('CHATTOGRAM-CENTRAL-SYN','Chattogram Central'),('SYLHET-CENTRAL-SYN','Sylhet Central')]
    areas=[]
    for i,(code,name) in enumerate(area_names,1):
        aid=sid('area',i); areas.append(aid); d.add('areas',area_id=aid,parent_area_id='',code=code,name=name,level='area',is_active='true',created_at=ts(BASE-timedelta(days=1)))
    outlet_names=['Mirpur Digital Service Point','Dhanmondi Commerce Point','Chattogram Market Service','Sylhet Online Payment Point','Uttara Synthetic Commerce Hub']
    outlets=[]; accounts={}
    for i,name in enumerate(outlet_names,1):
        oid=sid('outlet',i); outlets.append(oid)
        d.add('outlets',outlet_id=oid,synthetic_code=f'OUTLET-SYN-{i:03}',display_name=name,area_id=areas[(i-1)%4],currency_code='BDT',latitude='',longitude='',is_synthetic='true',is_active='true',created_at=ts(BASE-timedelta(days=1)),updated_at=ts(BASE-timedelta(days=1)))
        for code,pid in PROVIDERS.items():
            aid=sid('account',f'{i}:{code}'); accounts[(oid,code)]=aid
            d.add('outlet_provider_accounts',outlet_provider_account_id=aid,outlet_id=oid,provider_id=pid,synthetic_account_ref=f'ACCT-{code.upper()}-SYN-{i:03}',is_active='true',created_at=ts(BASE-timedelta(days=1)),updated_at=ts(BASE-timedelta(days=1)))
    runs=[]
    for sc,seeds in SEEDS.items():
        for j,seed in enumerate(seeds):
            rid=sid('run',f'{sc}:{j}'); runs.append((sc,rid))
            d.add('simulation_runs',simulation_run_id=rid,scenario_id=SCENARIOS[sc],seed=seed,config_snapshot=jd({'dataset':'moderate_demo_v1','scenario':sc,'seed':seed,'timezone':'Asia/Dhaka','immutable':True}),status='completed',started_by_user_id='',started_at=ts(BASE+timedelta(minutes=j)),completed_at=ts(END+timedelta(minutes=j)),error_summary='')
    runmap={sc:[r for s,r in runs if s==sc] for sc in SEEDS}
    fault_types=['delay','missing_feed','missing_field','conflicting_balance','malformed_payload']
    for i,ft in enumerate(fault_types*2):
        when=BASE+timedelta(days=2+i%5,hours=8+i)
        d.add('fault_injections',fault_injection_id=sid('fault',i),simulation_run_id=runmap['scenario_c'][i%2],outlet_id=outlets[i%5],provider_id=list(PROVIDERS.values())[i%3],fault_type=ft,parameters=jd({'synthetic':True,'fault_index':i}),scheduled_at=ts(when),applied_at=ts(when),ended_at=ts(when+timedelta(hours=2)),is_enabled='true')
    batches={}; event_no=0; txids=[]; tx_by_pair=defaultdict(list)
    for day in range(9):
      for oi,oid in enumerate(outlets):
       for pi,(pc,pid) in enumerate(PROVIDERS.items()):
        bi=f'{day}:{oi}:{pc}'; bid=sid('batch',bi); batches[(day,oid,pc)]=bid
        received=BASE+timedelta(days=day,hours=18)
        d.add('ingestion_batches',ingestion_batch_id=bid,simulation_run_id=runmap[['normal','scenario_a','scenario_b','scenario_c','scenario_d'][day%5]][day%2],outlet_id=oid,provider_id=pid,source_batch_ref=f'BATCH-SYN-{day:02}-{oi:02}-{pc.upper()}',source_generated_at=ts(received-timedelta(minutes=5)),received_at=ts(received),expected_event_count='27',received_event_count='27',rejected_event_count='0',normalization_status='normalized',created_at=ts(received))
        for k in range(27):
            event_no+=1; local_hour=[7,9,11,13,15,17,19,20,21][k%9]; occurred=BASE+timedelta(days=day,hours=local_hour-6,minutes=(k*7+oi*3+pi)%60)
            eid=sid('event',event_no); tid=sid('tx',event_no)
            typ=rng.choices(['cash_out','cash_in','payment','refund','adjustment'],[34,24,31,7,4])[0]
            status=rng.choices(['completed','failed','pending','reversed'],[88,6,4,2])[0]
            common=[500,1000,1500,2000,5000]; amount=Decimal(str(rng.choice(common) if rng.random()<.35 else rng.randint(8,25000)))+Decimal(rng.choice(['0','.25','.50','.75']))
            if day in (5,6) and typ=='payment': amount*=Decimal('1.15')
            ref=f'TXN-{pc.upper()}-SYN-{event_no:06}'; party=f'PARTY-SYN-{(event_no*37)%900+1:06}'
            d.add('ingestion_events',ingestion_event_id=eid,ingestion_batch_id=bid,event_type='transaction',source_event_ref=f'EVENT-SYN-{event_no:06}',source_observed_at=ts(occurred),received_at=ts(occurred+timedelta(minutes=2)),safe_payload=jd({'synthetic_transaction_ref':ref,'synthetic':True}),normalization_status='normalized',rejection_code='',rejection_detail='',created_at=ts(occurred+timedelta(minutes=2)))
            d.add('transactions',transaction_id=tid,ingestion_event_id=eid,simulation_run_id=runmap[['normal','scenario_a','scenario_b','scenario_c','scenario_d'][day%5]][day%2],outlet_provider_account_id=accounts[(oid,pc)],provider_id=pid,outlet_id=oid,synthetic_transaction_ref=ref,synthetic_party_ref=party,transaction_type=typ,status=status,amount=money(amount),currency_code='BDT',occurred_at=ts(occurred),received_at=ts(occurred+timedelta(minutes=2)),created_at=ts(occurred+timedelta(minutes=2)))
            txids.append(tid); tx_by_pair[(oid,pc)].append(tid)
    # 20 snapshots/day/reserve: separate shared cash and provider e-money.
    for day in range(9):
      for oi,oid in enumerate(outlets):
       for k in range(20):
        at=BASE+timedelta(days=day,hours=1+k)
        bal=max(2500,90000+oi*12000-day*1700-k*350+(18000 if day%3==0 else 0))
        d.add('cash_balance_snapshots',cash_balance_snapshot_id=sid('cash',f'{day}:{oi}:{k}'),ingestion_event_id='',simulation_run_id=runmap[['normal','scenario_a','scenario_b','scenario_c','scenario_d'][day%5]][day%2],outlet_id=oid,balance=money(bal),currency_code='BDT',observed_at=ts(at),received_at=ts(at+timedelta(minutes=2)),source_kind='seed',created_at=ts(at+timedelta(minutes=2)))
        for pi,(pc,pid) in enumerate(PROVIDERS.items()):
          pbal=max(1800,70000+oi*9000+pi*7000-day*900-k*(500 if (day==3 and pc=='bkash') else 120))
          d.add('provider_balance_snapshots',provider_balance_snapshot_id=sid('pbal',f'{day}:{oi}:{pc}:{k}'),ingestion_event_id='',simulation_run_id=runmap[['normal','scenario_a','scenario_b','scenario_c','scenario_d'][day%5]][day%2],outlet_provider_account_id=accounts[(oid,pc)],provider_id=pid,outlet_id=oid,balance=money(pbal),currency_code='BDT',observed_at=ts(at),received_at=ts(at+timedelta(minutes=2)),source_kind='seed',created_at=ts(at+timedelta(minutes=2)))
    # Preserve a Scenario C conflict at the same observed time.
    oid=outlets[2]; pc='nagad'; at=BASE+timedelta(days=6,hours=12)
    d.add('provider_balance_snapshots',provider_balance_snapshot_id=sid('pbal','conflict'),ingestion_event_id='',simulation_run_id=runmap['scenario_c'][0],outlet_provider_account_id=accounts[(oid,pc)],provider_id=PROVIDERS[pc],outlet_id=oid,balance='12345.67',currency_code='BDT',observed_at=ts(at),received_at=ts(at+timedelta(minutes=4)),source_kind='seed',created_at=ts(at+timedelta(minutes=4)))
    qids=[]
    statuses=['fresh']*22+['stale']*7+['missing']*5+['conflicting']*6
    issues=['late_arrival','missing_feed','missing_field','conflicting_snapshot','insufficient_samples','malformed_payload']*3
    for i,status in enumerate(statuses):
        oid=outlets[i%5]; pc=list(PROVIDERS)[i%3]; qid=sid('quality',i); qids.append(qid); at=BASE+timedelta(days=i%9,hours=20)
        d.add('data_quality_assessments',data_quality_assessment_id=qid,simulation_run_id=runmap['scenario_c'][i%2] if status!='fresh' else runmap['normal'][i%2],ingestion_batch_id=batches[(i%9,oid,pc)],outlet_id=oid,provider_id=PROVIDERS[pc],status=status,confidence_modifier={'fresh':'.9800','stale':'.6000','missing':'.0000','conflicting':'.3500'}[status],sample_count='27' if status=='fresh' else '4',latest_source_at=ts(at-timedelta(minutes=3)) if status!='missing' else '',assessed_at=ts(at),engine_version='quality-1.0.0',summary='Synthetic feed is '+status+'; human review recommended.' if status!='fresh' else 'Synthetic feed is fresh.',created_at=ts(at))
        if i>=22:
            it=issues[(i-22)%len(issues)]; d.add('data_quality_issues',data_quality_issue_id=sid('qissue',i),data_quality_assessment_id=qid,issue_type=it,severity='medium' if status!='missing' else 'high',field_name='source_observed_at' if it=='missing_field' else '',evidence=jd({'synthetic':True,'fault_type':it,'requires_review':True}),created_at=ts(at))
    aruns=[]
    for i in range(12):
        eng=['liquidity','anomaly','data_quality'][i%3]; aid=sid('analytics',i); aruns.append(aid)
        d.add('analytics_runs',analytics_run_id=aid,simulation_run_id=runmap[list(SEEDS)[i%5]][i%2],engine=eng,engine_version=f'{eng}-1.0.0',configuration=jd({'deterministic':True,'master_seed':MASTER_SEED}),input_window_start=ts(BASE),input_window_end=ts(END),status='completed',started_at=ts(END+timedelta(minutes=i)),completed_at=ts(END+timedelta(minutes=i+1)),error_summary='')
    projections=[]
    for i in range(60):
        oid=outlets[i%5]; shared=i%4==0; pc=list(PROVIDERS)[i%3]; actionable=i%10 in (0,1); burn=Decimal('850.00') if actionable else (Decimal('-120.00') if i%9==0 else Decimal('210.00')); current=Decimal('4800') if actionable else Decimal('52000')
        pid=sid('projection',i); projections.append(pid); asof=END-timedelta(hours=i%24); shortage=asof+timedelta(hours=float(current/burn)) if burn>0 else None
        conf='low' if i%8==0 else ('high' if i%3 else 'medium'); score={'low':'.3500','medium':'.7200','high':'.9100'}[conf]
        d.add('liquidity_projections',liquidity_projection_id=pid,analytics_run_id=aruns[(i//5)*3%12],outlet_id=oid,reserve_type='shared_cash' if shared else 'provider_e_money',outlet_provider_account_id='' if shared else accounts[(oid,pc)],provider_id='' if shared else PROVIDERS[pc],primary_data_quality_assessment_id=qids[i%40],as_of_at=ts(asof),current_balance=money(current),burn_rate_per_hour=money(burn),projected_shortage_at=ts(shortage) if shortage else '',lower_bound_at=ts(shortage-timedelta(hours=1)) if shortage else '',upper_bound_at=ts(shortage+timedelta(hours=2)) if shortage else '',confidence_score=score,confidence_level=conf,sample_count=str(12+i%37),is_actionable=str(actionable).lower(),non_actionable_reason='' if actionable else ('non-positive burn rate' if burn<=0 else 'reserve remains above threshold'),created_at=ts(asof))
        d.add('liquidity_signals',liquidity_signal_id=sid('signal',i),liquidity_projection_id=pid,signal_code='burn_rate',label='Observed synthetic burn rate',numeric_value=money(burn),unit='BDT/hour',direction='increases_pressure' if burn>0 else 'reduces_pressure',details=jd({'samples':12+i%37,'synthetic':True}),display_order='1')
        d.add('liquidity_projection_quality_assessments',liquidity_projection_id=pid,data_quality_assessment_id=qids[i%40])
    flags=[]
    dispositions=['requires_review']*10+['suppressed_data_quality']*5+['dismissed_benign']*4+['inconclusive']*3+['confirmed_unusual']*2
    for i,disp in enumerate(dispositions):
        oid=outlets[i%5]; pc=list(PROVIDERS)[i%3]; fid=sid('flag',i); flags.append(fid); degraded=disp=='suppressed_data_quality'
        d.add('anomaly_flags',anomaly_flag_id=fid,analytics_run_id=aruns[(i%4)*3+1],anomaly_rule_id=RULE,outlet_id=oid,provider_id=PROVIDERS[pc],outlet_provider_account_id=accounts[(oid,pc)],data_quality_assessment_id=qids[30+i%10] if degraded else qids[i%20],window_start=ts(BASE+timedelta(days=i%9,hours=12)),window_end=ts(BASE+timedelta(days=i%9,hours=13)),confidence_score='.3000' if degraded else '.8200',confidence_level='low' if degraded else 'high',disposition=disp,reason_code='near_identical_amounts',evidence_summary='Repeated near-identical synthetic amounts from a small opaque party cluster.',plausible_benign_explanation='' if degraded else 'Possible festival demand, salary-period activity, or recurring bill payment.',suppression_reason='Degraded source quality prevents an actionable conclusion.' if degraded else '',created_at=ts(END+timedelta(minutes=i)))
        d.add('anomaly_evidence_items',anomaly_evidence_item_id=sid('evidence',i),anomaly_flag_id=fid,evidence_type='transaction_cluster',label='Linked synthetic transaction cluster',value=jd({'count':6,'amount_band_bdt':'1500.00-1510.00','human_review_recommended':True}),display_order='1',created_at=ts(END+timedelta(minutes=i)))
        for tid in tx_by_pair[(oid,pc)][:6]: d.add('anomaly_flag_transactions',anomaly_flag_id=fid,transaction_id=tid)
    alerts=[]
    for i in range(24):
        typ=['liquidity','anomaly','combined','data_quality'][i%4]; oid=outlets[i%5]; pc=list(PROVIDERS)[i%3]; aid=sid('alert',i); alerts.append(aid); detected=END+timedelta(hours=i)
        d.add('alerts',alert_id=aid,simulation_run_id=runmap['scenario_d' if i<15 else 'scenario_c'][i%2],outlet_id=oid,provider_id=PROVIDERS[pc],alert_type=typ,severity=['medium','high','low'][i%3],state='active',deduplication_key=f'MODERATE-DEMO-V1-{i:03}',title_key=f'{typ}_default',structured_payload=jd({'synthetic':True,'advisory_only':True,'human_review_recommended':True}),requires_case=str(i<15).lower(),detected_at=ts(detected),created_at=ts(detected),supersedes_alert_id='')
        if typ in ('liquidity','combined'): d.add('alert_liquidity_projections',alert_id=aid,liquidity_projection_id=projections[i])
        if typ in ('anomaly','combined'): d.add('alert_anomaly_flags',alert_id=aid,anomaly_flag_id=flags[i%10])
        if typ=='data_quality': d.add('alert_quality_assessments',alert_id=aid,data_quality_assessment_id=qids[30+i%10])
        locales=['en']+(['bn_latn'] if i<8 else [])
        for loc in locales:
            template={'en':'7e000000-0000-0000-0000-0000000000e1','bn_latn':'7e000000-0000-0000-0000-0000000000b4'}[loc]
            d.add('alert_explanations',alert_explanation_id=sid('explanation',f'{i}:{loc}'),alert_id=aid,explanation_template_id=template,locale=loc,situation_text='Synthetic activity indicates possible liquidity pressure or unusual activity.',evidence_text='Typed analytical evidence is linked to this alert.',uncertainty_text='This is an advisory simulation; confidence depends on source quality.',next_step_text='Human review recommended using approved operational procedures.',benign_context_text='Festival demand or recurring e-commerce payments may explain the pattern.',rendered_at=ts(detected))
    status_plan=['open']*3+['acknowledged']*3+['escalated']*3+['resolved']*6
    for i,status in enumerate(status_plan):
        pc=list(PROVIDERS)[i%3]; oid=outlets[i%5]; cid=sid('case',i); opened=END+timedelta(hours=i); owner=USERS[pc]
        ack=opened+timedelta(minutes=15) if status!='open' else None; esc=opened+timedelta(minutes=45) if status in ('escalated','resolved') else None; res=opened+timedelta(hours=3) if status=='resolved' else None
        d.add('cases',case_id=cid,case_number=f'CASE-SYN-{i+1:04}',alert_id=alerts[i],outlet_id=oid,provider_id=PROVIDERS[pc],routing_rule_id={'bkash':'40000000-0000-0000-0000-000000000002','nagad':'40000000-0000-0000-0000-000000000003','rocket':'40000000-0000-0000-0000-000000000004'}[pc],status=status,current_owner_user_id=owner,current_owner_role='provider_ops',recommended_next_step='Review evidence and coordinate through approved provider-scoped procedures.',opened_at=ts(opened),acknowledged_at=ts(ack) if ack else '',escalated_at=ts(esc) if esc else '',resolved_at=ts(res) if res else '',resolution_summary='Reviewed as synthetic unusual activity; service conditions stabilized.' if res else '',version='1',updated_at=ts(res or esc or ack or opened))
        d.add('case_assignments',case_assignment_id=sid('assignment',i),case_id=cid,assigned_to_user_id=owner,assigned_to_role='provider_ops',assigned_by_user_id='',reason='initial_route',routing_rule_id={'bkash':'40000000-0000-0000-0000-000000000002','nagad':'40000000-0000-0000-0000-000000000003','rocket':'40000000-0000-0000-0000-000000000004'}[pc],comment='Provider-isolated synthetic routing.',assigned_at=ts(opened))
        transitions=[(None,'open',opened)]+([('open','acknowledged',ack)] if ack else [])+([('acknowledged','escalated',esc)] if esc else [])+([('escalated','resolved',res)] if res else [])
        for j,(fr,to,at) in enumerate(transitions): d.add('case_status_history',case_status_history_id=sid('history',f'{i}:{j}'),case_id=cid,from_status=fr or '',to_status=to,changed_by_user_id=owner if j else '',reason='Synthetic legal workflow transition.',changed_at=ts(at))
        for j in range(2): d.add('case_notes',case_note_id=sid('note',f'{i}:{j}'),case_id=cid,author_user_id=owner,note_text='Synthetic provider-scoped review note; human review recommended.',note_type='general' if j==0 else ('resolution' if res else 'evidence'),created_at=ts(opened+timedelta(minutes=30+j*20)))
        if res: d.add('case_reviews',case_review_id=sid('review',i),case_id=cid,reviewed_by_user_id=owner,disposition='benign_operational' if i%2 else 'confirmed_unusual',was_false_positive=str(i%2==1).lower(),review_summary='Evidence reviewed without making a final wrongdoing determination.',reviewed_at=ts(res))
        d.add('notifications',notification_id=sid('notification',i),case_id=cid,recipient_user_id=owner,recipient_role='provider_ops',channel='in_app',status='delivered',payload=jd({'synthetic':True,'case_number':f'CASE-SYN-{i+1:04}'}),queued_at=ts(opened),delivered_at=ts(opened+timedelta(minutes=1)),read_at=ts(ack) if ack else '',failure_reason='')
        for j,action in enumerate(['case_opened','case_assigned']+(['case_acknowledged'] if ack else [])+(['case_escalated'] if esc else [])+(['case_resolved'] if res else [])):
            d.add('audit_events',audit_event_id=sid('audit',f'{i}:{j}'),case_id=cid,alert_id=alerts[i],provider_id=PROVIDERS[pc],outlet_id=oid,actor_user_id=owner if j else '',actor_type='user' if j else 'routing_engine',action=action,entity_type='case',entity_id=cid,previous_values='',new_values=jd({'status':status,'synthetic':True}),request_id=f'REQUEST-SYN-{i:03}-{j}',occurred_at=ts(opened+timedelta(minutes=j*10)),hash='')
    # Labels and metrics: values are derived from explicit deterministic confusion counts.
    for vr_i,split in enumerate(['demo','held_out']):
        vid=sid('validation',vr_i); start=END+timedelta(days=2+vr_i)
        d.add('validation_runs',validation_run_id=vid,name=f'Moderate demo {split} validation',dataset_split=split,engine_version='validation-1.0.0',configuration=jd({'master_seed':MASTER_SEED,'population':'moderate_demo_v1'}),started_at=ts(start),completed_at=ts(start+timedelta(minutes=5)),status='completed',created_by_user_id='')
        for i in range(30):
            lt=['normal','shortage','anomaly','data_quality_incident'][i%4]
            d.add('ground_truth_labels',ground_truth_label_id=sid('label',f'{vr_i}:{i}'),validation_run_id=vid,simulation_run_id=runmap[['normal','scenario_a','scenario_b','scenario_c'][i%4]][i%2],outlet_id=outlets[i%5],provider_id=list(PROVIDERS.values())[i%3] if lt!='normal' else '',label_type=lt,expected_value=jd({'positive':lt!='normal','synthetic':True}),window_start=ts(BASE+timedelta(days=i%9)),window_end=ts(BASE+timedelta(days=i%9,hours=1)),created_at=ts(start))
        vals=[('anomaly_precision','analytics','.8000','ratio',10,'TP=8/(TP=8+FP=2)'),('anomaly_recall','analytics','.8000','ratio',10,'TP=8/(TP=8+FN=2)'),('anomaly_false_positive_rate','analytics','.1000','ratio',20,'FP=2/(FP=2+TN=18)'),('data_quality_handling_rate','reliability','1.0000','ratio',10,'10 degraded windows safely suppressed / 10'),('alert_explanation_coverage','explainability','1.0000','ratio',24,'24 alerts with English explanation / 24'),('audit_completeness','reliability','1.0000','ratio',15,'15 cases with assignment, history, notification, and audit / 15'),('provider_denial_success_rate','reliability','1.0000','ratio',6,'6 expected cross-provider denials / 6'),('shortage_detection_lead_time','analytics','180.0000','minutes',6,'Median lead time across 6 actionable shortage labels')]
        for j,(code,cat,val,unit,n,method) in enumerate(vals): d.add('metric_results',metric_result_id=sid('metric',f'{vr_i}:{j}'),validation_run_id=vid,metric_code=code,category=cat,value=val,unit=unit,sample_size=str(n),method=method,limitations='Synthetic deterministic population; not representative of provider market behavior.',details=jd({'engine_version':'validation-1.0.0','configuration':'moderate_demo_v1','reproducible':True}),computed_at=ts(start+timedelta(minutes=5)))
    return d

def main():
    manifest=generate().write()
    print(json.dumps(manifest['row_counts'],sort_keys=True))

if __name__=='__main__': main()
