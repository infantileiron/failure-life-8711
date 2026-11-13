import json, sqlite3, threading
from dataclasses import asdict
from fastapi import HTTPException
from src.config.settings import DATABASE_URL
TABLES = ("datasets", "rules", "studies", "runs", "reviews", "reports", "users", "audit")
_LOCK = threading.RLock()
def connect():
    if DATABASE_URL.startswith("sqlite:///"):
        conn = sqlite3.connect(DATABASE_URL.removeprefix("sqlite:///"), timeout=30)
        return conn, "?"
    import psycopg
    return psycopg.connect(DATABASE_URL), "%s"
def init_db():
    conn,_ = connect()
    try:
        if not DATABASE_URL.startswith("sqlite:///"):
            conn.execute("SELECT pg_advisory_xact_lock(2301)")
        for table in TABLES:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.commit()
    finally: conn.close()
    upgrade_payloads()
def upgrade_payloads():
    # 旧数据升级：仅给历史数据集的试件行补 failure_cause=None（原因缺失→CIF不可估计）。
    # 运行/复核/报告载荷一律不改写，历史结果保持原样。幂等，可重复执行。
    conn,q = connect()
    try:
        stale = conn.execute("SELECT id,payload FROM datasets").fetchall()
        for ds_id, payload in stale:
            item = json.loads(payload)
            changed = False
            for row in item.get("rows", []):
                if "failure_cause" not in row:
                    row["failure_cause"] = None
                    changed = True
            if changed:
                conn.execute(f"UPDATE datasets SET payload={q} WHERE id={q}",
                             (json.dumps(item, ensure_ascii=False, allow_nan=False), ds_id))
        conn.commit()
    finally: conn.close()
def all_rows(table):
    assert table in TABLES
    conn,_ = connect()
    try: return [json.loads(row[0]) for row in conn.execute(f"SELECT payload FROM {table} ORDER BY id").fetchall()]
    finally: conn.close()
def get(table, id):
    assert table in TABLES
    conn,q = connect()
    try:
        row = conn.execute(f"SELECT payload FROM {table} WHERE id={q}", (id,)).fetchone()
        if row is None: raise HTTPException(404, "记录不存在")
        return json.loads(row[0])
    finally: conn.close()
def put(table, item, insert_only=False):
    assert table in TABLES
    if not isinstance(item, dict): item = asdict(item)
    conn,q = connect()
    clause = "DO NOTHING" if insert_only else "DO UPDATE SET payload=excluded.payload"
    try:
        with _LOCK:
            conn.execute(f"INSERT INTO {table} (id,payload) VALUES ({q},{q}) ON CONFLICT(id) {clause}", (item["id"], json.dumps(item, ensure_ascii=False, allow_nan=False)))
            conn.commit()
        return item
    finally: conn.close()
