"""JSON storage that works locally AND on Vercel.

Vercel's filesystem is read-only (only /tmp is writable, and it is wiped between
requests/instances), so writing to data/*.json crashes there. Order of backends:

1. Redis over REST (Upstash / Vercel KV)  -> permanent storage, used when env vars exist
2. Normal file in data/                    -> local development
3. File in /tmp                            -> last-resort fallback so the app never crashes
"""
import json, os, tempfile
import requests

_REST_URL = (os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("KV_REST_API_URL") or "").rstrip("/")
_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN") or os.getenv("KV_REST_API_TOKEN") or ""
REDIS_ENABLED = bool(_REST_URL and _REST_TOKEN)
_PREFIX = os.getenv("STORAGE_PREFIX", "nexadesk:")
_TMP_DIR = os.path.join(tempfile.gettempdir(), "nexadesk_data")


def _redis(*cmd):
    r = requests.post(_REST_URL, headers={"Authorization": f"Bearer {_REST_TOKEN}"},
                      data=json.dumps(list(cmd)), timeout=8)
    r.raise_for_status()
    d = r.json()
    if "error" in d:
        raise RuntimeError(d["error"])
    return d.get("result")


def _read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class JsonStore:
    def __init__(self, path, default):
        self.path = path
        self.default = default
        self.key = _PREFIX + os.path.basename(path)
        self.tmp_path = os.path.join(_TMP_DIR, os.path.basename(path))

    # ---- read ----
    def _seed(self):
        """Initial data shipped with the project (data/*.json)."""
        for p in (self.tmp_path, self.path):
            try:
                return _read_file(p)
            except Exception:
                continue
        return self.default

    def read(self):
        if REDIS_ENABLED:
            try:
                raw = _redis("GET", self.key)
                if raw is not None:
                    return json.loads(raw)
                return self._seed()          # first run: use bundled data
            except Exception:
                pass                          # fall back to files
        return self._seed()

    # ---- write ----
    def write(self, data):
        if REDIS_ENABLED:
            try:
                _redis("SET", self.key, json.dumps(data, ensure_ascii=False))
                return
            except Exception:
                pass
        for p in (self.path, self.tmp_path):
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return
            except OSError:
                continue
        raise RuntimeError("Could not save data (no writable storage).")
