"""Print non-secret reference identifiers required by deterministic seed loaders."""
from migrations.run_migrations import _load_dotenv, open_connection, safe_target


def main():
    _load_dotenv()
    label, dsn, conn = open_connection()
    conn.set_session(readonly=True, autocommit=False)
    with conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT explanation_template_id, template_key, locale, version, alert_type
            FROM explanation_templates ORDER BY template_key, locale, version
            """
        )
        templates = cur.fetchall()
    conn.close()
    print(f'target: {safe_target(dsn)} (via {label})')
    for row in templates:
        print(' | '.join(str(value) for value in row))


if __name__ == '__main__':
    main()
