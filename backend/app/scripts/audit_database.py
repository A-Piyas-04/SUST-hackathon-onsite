"""Write a secret-free PostgreSQL physical-schema and data audit as JSON."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from migrations.run_migrations import _load_dotenv, open_connection, safe_target

OUT = Path(__file__).resolve().parents[3] / "docs" / "data" / "database-audit.json"


def default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def rows(cur, sql):
    cur.execute(sql)
    names = [d.name for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def main():
    _load_dotenv()
    label, dsn, conn = open_connection()
    conn.set_session(readonly=True, autocommit=False)
    with conn, conn.cursor() as cur:
        cur.execute("select version(), current_database(), current_schema(), now()")
        version, database, schema, audited_at = cur.fetchone()
        tables = rows(cur, """
          select n.nspname schema_name, c.relname table_name, c.relkind,
                 obj_description(c.oid) comment
          from pg_class c join pg_namespace n on n.oid=c.relnamespace
          where n.nspname in ('public','app') and c.relkind in ('r','p','v','m')
          order by 1,2
        """)
        columns = rows(cur, """
          select table_schema, table_name, ordinal_position, column_name,
                 data_type, udt_name, is_nullable, column_default
          from information_schema.columns
          where table_schema in ('public','app') order by 1,2,3
        """)
        constraints = rows(cur, """
          select n.nspname schema_name, c.relname table_name, con.conname,
                 con.contype, pg_get_constraintdef(con.oid) definition,
                 con.condeferrable, con.condeferred
          from pg_constraint con join pg_class c on c.oid=con.conrelid
          join pg_namespace n on n.oid=c.relnamespace
          where n.nspname in ('public','app') order by 1,2,3
        """)
        indexes = rows(cur, """
          select schemaname, tablename, indexname, indexdef
          from pg_indexes where schemaname in ('public','app') order by 1,2,3
        """)
        triggers = rows(cur, """
          select event_object_schema, event_object_table, trigger_name,
                 event_manipulation, action_timing, action_statement
          from information_schema.triggers
          where event_object_schema in ('public','app') order by 1,2,3,4
        """)
        functions = rows(cur, """
          select n.nspname schema_name, p.proname function_name,
                 pg_get_function_identity_arguments(p.oid) arguments,
                 pg_get_function_result(p.oid) result, l.lanname language
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          join pg_language l on l.oid=p.prolang
          where n.nspname in ('public','app') order by 1,2,3
        """)
        policies = rows(cur, """
          select schemaname, tablename, policyname, permissive, roles, cmd,
                 qual, with_check from pg_policies
          where schemaname in ('public','app') order by 1,2,3
        """)
        grants = rows(cur, """
          select table_schema, table_name, grantee, privilege_type
          from information_schema.role_table_grants
          where table_schema in ('public','app') order by 1,2,3,4
        """)
        migrations = rows(cur, "select version,name,checksum,applied_at from schema_migrations order by version")
        counts = {}
        ranges = {}
        for t in tables:
            if t['schema_name'] != 'public' or t['relkind'] not in ('r','p'):
                continue
            name=t['table_name']
            cur.execute(f'SELECT count(*) FROM public."{name}"')
            counts[name]=cur.fetchone()[0]
            tcols=[c['column_name'] for c in columns if c['table_schema']=='public' and c['table_name']==name]
            for candidate in ('occurred_at','observed_at','assessed_at','created_at','started_at'):
                if candidate in tcols:
                    cur.execute(f'SELECT min("{candidate}"), max("{candidate}") FROM public."{name}"')
                    lo,hi=cur.fetchone(); ranges[name]={'column':candidate,'min':lo,'max':hi}; break
        report={
          'audit_version':'1.0.0','audited_at':audited_at,'target':safe_target(dsn),
          'connection_source':label,'postgres_version':version,'database':database,
          'current_schema':schema,'migrations':migrations,'tables_and_views':tables,
          'columns':columns,'constraints':constraints,'indexes':indexes,
          'triggers':triggers,'functions':functions,'policies':policies,'grants':grants,
          'row_counts':counts,'date_ranges':ranges,
        }
    conn.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,default=default)+"\n",encoding='utf-8')
    print(f"wrote {OUT} ({len(tables)} relations, {len(columns)} columns)")


if __name__ == '__main__':
    main()
