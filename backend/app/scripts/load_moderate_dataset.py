"""Transactional, idempotent loader for validated moderate-demo artifacts."""
from __future__ import annotations
import argparse, csv, json, os
from pathlib import Path
from psycopg2 import sql
from psycopg2.extras import execute_values
from migrations.run_migrations import _load_dotenv, open_connection, safe_target
from app.scripts.validate_moderate_dataset import main as validate

ROOT=Path(__file__).resolve().parents[3]; DATA=ROOT/'data'/'generated'/'moderate_demo'
ORDER=['areas','outlets','outlet_provider_accounts','simulation_runs','fault_injections','ingestion_batches','ingestion_events','transactions','cash_balance_snapshots','provider_balance_snapshots','data_quality_assessments','data_quality_issues','analytics_runs','liquidity_projections','liquidity_signals','liquidity_projection_quality_assessments','anomaly_flags','anomaly_evidence_items','anomaly_flag_transactions','alerts','alert_liquidity_projections','alert_anomaly_flags','alert_quality_assessments','alert_explanations','cases','case_assignments','case_status_history','case_notes','case_reviews','notifications','audit_events','validation_runs','ground_truth_labels','metric_results']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); ap.add_argument('--confirm-development',action='store_true'); args=ap.parse_args()
    validate(); _load_dotenv(); env=os.getenv('APP_ENV','').lower()
    if args.apply and (not args.confirm_development or env not in ('development','local','test')):
        raise SystemExit('REFUSED: --apply requires --confirm-development and APP_ENV=development/local/test')
    label,dsn,conn=open_connection(); print(f"target: {safe_target(dsn)} (via {label}); mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    inserted={}; skipped={}
    try:
      with conn.cursor() as cur:
        cur.execute("select version from schema_migrations order by version")
        versions=[r[0] for r in cur.fetchall()]
        if '007' not in versions: raise SystemExit('REFUSED: database has not applied schema migration 007')
        for table in ORDER:
          path=DATA/f'{table}.csv'
          if not path.exists(): continue
          with path.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
          if not rows: continue
          cols=list(rows[0]); values=[[None if r[c]=='' else r[c] for c in cols] for r in rows]
          query=sql.SQL('INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,cols)))
          execute_values(cur,query.as_string(conn),values,page_size=500)
          before=cur.rowcount
          inserted[table]=before; skipped[table]=len(rows)-before
          print(f'{table}: inserted={before} skipped={len(rows)-before}')
        cur.execute('SET CONSTRAINTS ALL IMMEDIATE')
      if args.apply: conn.commit(); print('COMMITTED')
      else: conn.rollback(); print('DRY-RUN PASSED; transaction rolled back')
    except Exception:
      conn.rollback(); raise
    finally: conn.close()
    report={'mode':'apply' if args.apply else 'dry-run','target':safe_target(dsn),'inserted':inserted,'skipped':skipped,'conflicted':skipped,'committed':args.apply}
    out=DATA/('apply-report.json' if args.apply else 'dry-run-report.json'); out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
