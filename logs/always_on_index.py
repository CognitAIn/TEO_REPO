import os, time, hashlib, sqlite3, pathlib
from datetime import datetime, timedelta

CACHE_DB = r"C:\trinity\symbol_cache.db"
ROOTS = [r"C:\Users", r"D:\Data"]        # edit if you want more drives
WINDOW_DAYS = 30                         # user-controlled cache window

cutoff = datetime.now() - timedelta(days=WINDOW_DAYS)
os.makedirs(os.path.dirname(CACHE_DB), exist_ok=True)
conn = sqlite3.connect(CACHE_DB)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS files(
 path TEXT PRIMARY KEY,
 size INTEGER, mtime REAL, checksum TEXT, last_access REAL
)""")

def quick_hash(path):
    h = hashlib.blake2b(digest_size=8)
    with open(path, "rb", buffering=0) as f:
        h.update(f.read(65536))          # hash first 64 KB only
    return h.hexdigest()

for root in ROOTS:
    for dirpath, _, files in os.walk(root):
        for name in files:
            p = pathlib.Path(dirpath) / name
            try:
                st = p.stat()
                if not st.st_mode & 0o400:  # skip unreadable
                    continue
                if st.st_mtime < cutoff.timestamp():
                    continue
                h = quick_hash(p)
                c.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)",
                          (str(p), st.st_size, st.st_mtime, h, time.time()))
            except Exception:
                continue

conn.commit()
conn.close()
print("✅  Trinity always-on index updated:", CACHE_DB)
