#!/usr/bin/env python3
"""
🚀 AI Studio Local Code Bridge — bridge.py
Run: python bridge.py
No pip installs or external dependencies required — pure Python standard library.

Usage:
  - Put bridge.py directly inside your project folder and run: python bridge.py
  - Or run with a target path: python bridge.py "C:\\path\\to\\my-project"
  - Or specify port: python bridge.py --port 4545
"""

import sys
import io
import http.server
import json
import os
import re
import difflib
import pathlib
import argparse
import socketserver
import shutil
from datetime import datetime

# Force UTF-8 output and enable line buffering so terminal logs appear instantly
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Global config defaults
DEFAULT_PORT = 4545
PROJECT_DIR  = str(pathlib.Path.cwd().resolve())
PORT         = DEFAULT_PORT
BACKUP_DIR   = ".ai_backups"

# ── File / dir filters ─────────────────────────────────────────
BINARY_EXTS = {
    ".png",".jpg",".jpeg",".gif",".webp",".ico",".bmp",".tiff",
    ".pdf",".zip",".tar",".gz",".rar",".7z",
    ".ttf",".woff",".woff2",".eot",".otf",
    ".mp3",".mp4",".avi",".mov",".webm",".ogg",
    ".exe",".dll",".so",".dylib",".bin",
    ".pyc",".pyo",".pyd",".class",".jar",
    ".db",".sqlite",".sqlite3",".map",
}

SKIP_DIRS = {
    "node_modules",".next",".git",".svn",".hg",
    "dist","build",".cache","coverage",".turbo",
    "__pycache__",".venv","venv",
    ".vercel",".netlify","out",".nuxt",".idea",".vscode",
    ".ai_backups",
}

SKIP_FILES = {
    "package-lock.json","yarn.lock","pnpm-lock.yaml",
    ".DS_Store","Thumbs.db",
    ".env.local",".env.production",".env.development",
    "bridge.py","bridge.bat","START-BRIDGE.bat","start-bridge.bat",
    "start-bridge.sh","start-bridge.command","fix_js.py","codebase_digest.txt"
}

ALLOWED_DOTFILES = {
    ".env", ".env.example", ".eslintrc", ".eslintrc.json", ".eslintrc.js",
    ".gitignore", ".prettierrc", ".babelrc"
}

def is_binary(path: str) -> bool:
    return pathlib.Path(path).suffix.lower() in BINARY_EXTS

def backup_file(full_path: str, rel_path: str):
    """Silently create a timestamped backup in .ai_backups before modifying/overwriting."""
    try:
        if not os.path.exists(full_path):
            return
        backup_root = pathlib.Path(PROJECT_DIR) / BACKUP_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = backup_root / f"{rel_path}.{timestamp}.bak"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full_path, dest)
    except Exception:
        pass

def sanitize_text(text: str) -> str:
    """
    Sanitize text before comparisons:
      - Strips UTF-8 BOM (\ufeff).
      - Replaces zero-width spaces (\u200b, \u200c, \u200d, \u2060).
      - Replaces non-breaking space (\u00a0, \u202f, \u2007) with standard space ' '.
      - Normalizes CRLF and CR to LF.
    """
    if not text:
        return ""
    text = text.lstrip("\ufeff")
    text = text.replace("\u00a0", " ").replace("\u202f", " ").replace("\u2007", " ")
    for zw in ("\u200b", "\u200c", "\u200d", "\ufeff", "\u2060"):
        text = text.replace(zw, "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text

def normalize_for_matching(line: str) -> str:
    """
    Produce a canonical representation of a line for fuzzy matching:
      - Strips leading and trailing whitespace.
      - Collapses internal multiple spaces/tabs into a single space.
      - Normalizes repeated separator characters (3+ '=', '-', '*', '~', '_', '#', '/') down to 3 chars.
      - Normalizes duplicate slashes in URLs or paths (e.g. 'https://domain.com//file' -> 'https://domain.com/file').
    """
    s = line.strip()
    if not s:
        return ""
    # Normalize duplicate slashes in paths/URLs (preserve http:// or https://)
    s = re.sub(r'(?<!:)//+', '/', s)
    # Normalize repeated separator characters (3 or more -> 3)
    s = re.sub(r'={3,}', '===', s)
    s = re.sub(r'-{3,}', '---', s)
    s = re.sub(r'\*{3,}', '***', s)
    s = re.sub(r'~{3,}', '~~~', s)
    s = re.sub(r'_{3,}', '___', s)
    s = re.sub(r'#{3,}', '###', s)
    s = re.sub(r'/{3,}', '///', s)
    # Collapse multiple internal spaces/tabs to a single space
    s = re.sub(r'[ \t]+', ' ', s)
    return s

def normalize_lines(text: str) -> list[str]:
    """Return lines stripped of leading/trailing whitespace for fuzzy comparison."""
    return [line.strip() for line in text.splitlines()]

def _reindent_replacement(replace_text: str, base_indent: str) -> str:
    """Re-indent replacement lines to match the file's base indentation level."""
    repl_lines = replace_text.splitlines()
    if not repl_lines:
        return replace_text
    repl_base = ""
    for rl in repl_lines:
        if rl.strip():
            repl_base = rl[: len(rl) - len(rl.lstrip())]
            break
    reindented = []
    for rl in repl_lines:
        if rl.strip() == "":
            reindented.append("")
        elif rl.startswith(repl_base):
            reindented.append(base_indent + rl[len(repl_base):])
        else:
            reindented.append(base_indent + rl.lstrip())
    return "\n".join(reindented)

def _rebuild(orig_lines: list, i: int, flen: int, replace_text: str, original: str) -> str:
    """Splice replacement into orig_lines at position i, preserving line endings."""
    new_lines = orig_lines[:i] + replace_text.splitlines() + orig_lines[i + flen:]
    ending = "\r\n" if "\r\n" in original else "\n"
    result = ending.join(new_lines)
    if original.endswith("\r\n"):
        result += "\r\n"
    elif original.endswith("\n"):
        result += "\n"
    return result

def fuzzy_find_and_replace(original: str, find_text: str, replace_text: str) -> str | None:
    """
    Bulletproof multi-tiered find & replace strategies:

      1. Exact match (on sanitized text)
      2. Indent-normalised exact line match
      3. Canonical line match (normalizes 3+ separators, duplicate slashes, whitespace)
      4. Blank-line-tolerant canonical match
      5. Character-level & token-level fuzzy sequence match (sliding window with difflib)
    """
    find_norm = sanitize_text(find_text)
    orig_norm = sanitize_text(original)
    repl_norm = sanitize_text(replace_text)

    if not find_norm.strip():
        return None

    # ── 1. Exact match (on sanitized text) ──────────────────────
    if find_norm in orig_norm:
        new_content = orig_norm.replace(find_norm, repl_norm, 1)
        if "\r\n" in original:
            new_content = new_content.replace("\n", "\r\n")
        return new_content

    find_lines = find_norm.splitlines()
    orig_lines = orig_norm.splitlines()

    if not find_lines:
        return None

    flen = len(find_lines)

    # ── 2. Indent-normalised match ───────────────────────────────
    find_stripped = [l.strip() for l in find_lines]
    orig_stripped = [l.strip() for l in orig_lines]

    if not all(s == "" for s in find_stripped):
        for i in range(len(orig_lines) - flen + 1):
            if orig_stripped[i:i + flen] == find_stripped:
                base_indent = ""
                for orig_line in orig_lines[i:i + flen]:
                    if orig_line.strip():
                        base_indent = orig_line[: len(orig_line) - len(orig_line.lstrip())]
                        break
                new_repl = _reindent_replacement(repl_norm, base_indent)
                return _rebuild(orig_lines, i, flen, new_repl, original)

    # ── 3. Canonical line match (separators, duplicate slashes, whitespace) ──
    find_canon = [normalize_for_matching(l) for l in find_lines]
    orig_canon = [normalize_for_matching(l) for l in orig_lines]

    for i in range(len(orig_lines) - flen + 1):
        if orig_canon[i:i + flen] == find_canon:
            base_indent = ""
            for orig_line in orig_lines[i:i + flen]:
                if orig_line.strip():
                    base_indent = orig_line[: len(orig_line) - len(orig_line.lstrip())]
                    break
            new_repl = _reindent_replacement(repl_norm, base_indent)
            return _rebuild(orig_lines, i, flen, new_repl, original)

    # ── 4. Blank-line-tolerant canonical match ────────────────────
    find_nb = [(idx, normalize_for_matching(l)) for idx, l in enumerate(find_lines) if l.strip()]
    orig_nb = [(idx, normalize_for_matching(l)) for idx, l in enumerate(orig_lines) if l.strip()]

    if find_nb:
        find_nb_content = [pair[1] for pair in find_nb]
        flen_nb = len(find_nb_content)

        for j in range(len(orig_nb) - flen_nb + 1):
            window_content = [orig_nb[j + k][1] for k in range(flen_nb)]
            if window_content == find_nb_content:
                first_orig_idx = orig_nb[j][0]
                last_orig_idx  = orig_nb[j + flen_nb - 1][0]
                actual_flen    = last_orig_idx - first_orig_idx + 1

                base_indent = ""
                first_line = orig_lines[first_orig_idx]
                if first_line.strip():
                    base_indent = first_line[: len(first_line) - len(first_line.lstrip())]

                new_repl = _reindent_replacement(repl_norm, base_indent)
                return _rebuild(orig_lines, first_orig_idx, actual_flen, new_repl, original)

    # ── 5. Character-Level & Token-Level Sequence Matching (Resilient) ──────
    find_nb_lines = [normalize_for_matching(l) for l in find_lines if l.strip()]
    find_canon_joined = "\n".join(find_nb_lines)

    if find_canon_joined and orig_nb:
        flen_nb = len(find_nb_lines)
        total_orig_nb = len(orig_nb)

        # Allow flexible window sizes: exact, +1 line, -1 line, +2, -2
        candidate_lens = []
        for delta in (0, 1, -1, 2, -2):
            target_len = flen_nb + delta
            if 1 <= target_len <= total_orig_nb and target_len not in candidate_lens:
                candidate_lens.append(target_len)

        best_ratio = 0.0
        best_slice = None

        for w_len in candidate_lens:
            for j in range(total_orig_nb - w_len + 1):
                window_slice = orig_nb[j : j + w_len]
                window_joined = "\n".join(pair[1] for pair in window_slice)
                ratio = difflib.SequenceMatcher(None, find_canon_joined, window_joined).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_slice = window_slice

        # Threshold: 78% for normal files, 70% for short files (<= 30 lines)
        threshold = 0.70 if len(orig_lines) <= 30 else 0.78
        if best_ratio >= threshold and best_slice:
            first_orig_idx = best_slice[0][0]
            last_orig_idx  = best_slice[-1][0]
            actual_flen    = last_orig_idx - first_orig_idx + 1

            base_indent = ""
            first_line = orig_lines[first_orig_idx]
            if first_line.strip():
                base_indent = first_line[: len(first_line) - len(first_line.lstrip())]

            new_repl = _reindent_replacement(repl_norm, base_indent)
            print(f"  ⚠️  Fuzzy sequence match used (similarity: {best_ratio:.1%}) — applied at lines {first_orig_idx + 1}-{last_orig_idx + 1}")
            return _rebuild(orig_lines, first_orig_idx, actual_flen, new_repl, original)

    return None  # no match found after all 5 strategies

def build_tree(startpath: str) -> str:
    """Generate an ASCII visual directory tree matching AI Studio reference."""
    lines = ["=== PROJECT_STRUCTURE_START ==="]
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [
            d for d in sorted(dirs)
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        level = root.replace(startpath, '').count(os.sep)
        indent = '    ' * level
        if os.path.abspath(root) == os.path.abspath(startpath):
            lines.append("📁 ./")
        else:
            lines.append(f"{indent}📁 {os.path.basename(root)}/")
        file_indent = '    ' * (level + 1)
        for f in sorted(files):
            if f in SKIP_FILES or is_binary(f):
                continue
            if f.startswith(".") and f not in ALLOWED_DOTFILES:
                continue
            lines.append(f"{file_indent}📄 {f}")
    lines.append("=== PROJECT_STRUCTURE_END ===")
    return "\n".join(lines)

def walk_project():
    """Yield all non-binary, non-skipped files under PROJECT_DIR."""
    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for fname in files:
            if fname in SKIP_FILES:
                continue
            if fname.startswith(".") and fname not in ALLOWED_DOTFILES:
                continue
            full = os.path.join(root, fname)
            if not is_binary(full):
                yield full

def safe_resolve(rel_path: str) -> str:
    """Resolve rel_path inside PROJECT_DIR; raise on traversal or invalid path."""
    if not rel_path or not str(rel_path).strip():
        raise ValueError("File path cannot be empty")
    clean_rel = str(rel_path).strip().replace("\\", "/").lstrip("/")
    if clean_rel in ("", ".", "./"):
        raise ValueError("Invalid file path (cannot target project directory root)")
    proj = pathlib.Path(PROJECT_DIR).resolve()
    target = (proj / clean_rel).resolve()
    if not target.is_relative_to(proj) or target == proj:
        raise ValueError("Path traversal or root directory target not allowed")
    return str(target)

# ── HTTP Handler ───────────────────────────────────────────────
class BridgeHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Custom clean log line matching standard Python http.server output
        print(f'{self.address_string()} - - [{self.log_date_time_string()}] {fmt % args}')

    # ── CORS ──────────────────────────────────────────────────
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    # ── Helpers ───────────────────────────────────────────────
    def send_json(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_cors_headers()
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    # ── GET ───────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "projectDir": PROJECT_DIR, "port": PORT})
        else:
            self.send_json(404, {"error": "Not found"})

    # ── POST ──────────────────────────────────────────────────
    def do_POST(self):
        routes = {
            "/digest":    self.route_digest,
            "/edit":      self.route_edit,
            "/replace":   self.route_edit,      # alias for /edit
            "/write":     self.route_write,
            "/push-file": self.route_write,     # alias for /write
            "/push-all":  self.route_push_all,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_json(404, {"error": "Not found"})

    # ── POST /digest ──────────────────────────────────────────
    def route_digest(self):
        files = list(walk_project())
        tree  = build_tree(PROJECT_DIR)
        SEP   = "=" * 80
        lines = [
            "Current Project Context:",
            tree,
            ""
        ]

        for fpath in files:
            rel = pathlib.Path(fpath).relative_to(PROJECT_DIR).as_posix()
            try:
                content = pathlib.Path(fpath).read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = "[Could not read file]"
            lines.append(SEP)
            lines.append(f"FILE: {rel}")
            lines.append(SEP)
            lines.append(content)
            lines.append("")

        codebase       = "\n".join(lines)
        token_estimate = len(codebase) // 4
        print(f"  📦 Codebase digested: {len(files)} files (~{token_estimate} tokens)")
        self.send_json(200, {
            "codebase":      codebase,
            "tokenEstimate": token_estimate,
            "fileCount":     len(files),
        })

    # ── POST /edit & /replace ─────────────────────────────────
    def route_edit(self):
        body         = self.read_body()
        file_path    = body.get("filePath") or body.get("path") or body.get("file")
        find_text    = body.get("findText") or body.get("find") or body.get("search")
        replace_text = body.get("replaceText") or body.get("replace")
        content      = body.get("content") or body.get("code") or body.get("text")

        if not file_path:
            self.send_json(400, {"error": "Missing filePath"})
            return

        try:
            full = safe_resolve(file_path)
        except ValueError as e:
            self.send_json(400, {"error": str(e)})
            return

        # Case 1: Targeted find & replace
        if find_text is not None and replace_text is not None:
            if not os.path.exists(full):
                self.send_json(404, {"error": f"File not found: {file_path}"})
                return
            if not os.path.isfile(full):
                self.send_json(400, {"error": f"Target is a directory, not a file: {file_path}"})
                return

            try:
                original = pathlib.Path(full).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                self.send_json(500, {"error": f"Failed to read file: {e}"})
                return

            new_content = fuzzy_find_and_replace(original, find_text, replace_text)
            if new_content is None:
                print(f"  \u274c Edit failed for {file_path}: No match found after all 5 fuzzy strategies.")
                preview = repr(find_text[:120].strip()) if find_text else '""'
                print(f"     Target FIND block ({len(find_text.splitlines())} lines): {preview}...")
                self.send_json(400, {"error": "Target string not found in file (tried exact, canonical & character fuzzy matching)"})
                return

            try:
                backup_file(full, file_path)
                pathlib.Path(full).write_text(new_content, encoding="utf-8")
                print(f"  \u2705 Successfully updated {file_path}")
                self.send_json(200, {"success": True, "filePath": file_path})
            except Exception as e:
                self.send_json(500, {"error": f"Failed to write file: {e}"})
            return

        # Case 2: Full file content overwrite (for an updated file)
        if content is not None:
            if os.path.exists(full) and not os.path.isfile(full):
                self.send_json(400, {"error": f"Target is a directory, not a file: {file_path}"})
                return
            try:
                if os.path.exists(full):
                    backup_file(full, file_path)
                pathlib.Path(full).parent.mkdir(parents=True, exist_ok=True)
                pathlib.Path(full).write_text(content, encoding="utf-8")
                print(f"  \u2705 Successfully updated {file_path}")
                self.send_json(200, {"success": True, "filePath": file_path})
            except Exception as e:
                self.send_json(500, {"error": f"Failed to write file: {e}"})
            return

        self.send_json(400, {"error": "Missing findText/replaceText or content"})

    # ── POST /write & /push-file ──────────────────────────────
    def route_write(self):
        body      = self.read_body()
        file_path = body.get("filePath") or body.get("path") or body.get("file")
        content   = body.get("content") or body.get("code") or body.get("text")

        if file_path is None or content is None:
            self.send_json(400, {"error": "Missing fields: filePath, content"})
            return

        try:
            full = safe_resolve(file_path)
        except ValueError as e:
            self.send_json(400, {"error": str(e)})
            return

        if os.path.exists(full) and not os.path.isfile(full):
            self.send_json(400, {"error": f"Target is a directory, not a file: {file_path}"})
            return

        try:
            if os.path.exists(full):
                backup_file(full, file_path)
            pathlib.Path(full).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(full).write_text(content, encoding="utf-8")
            self.send_json(200, {"success": True, "filePath": file_path})
        except Exception as e:
            self.send_json(500, {"error": f"Failed to write file: {e}"})

    # ── POST /push-all ────────────────────────────────────────
    def route_push_all(self):
        ops = self.read_body()
        if not isinstance(ops, list):
            self.send_json(400, {"error": "Expected an array of operations"})
            return

        results = []
        for op in ops:
            fp = op.get("filePath") or op.get("path") or op.get("file") or ""
            
            try:
                full = safe_resolve(fp)
            except ValueError as e:
                results.append({"filePath": fp, "success": False, "error": str(e)})
                continue

            # If find & replace
            find = op.get("findText") or op.get("find") or op.get("search")
            repl = op.get("replaceText") or op.get("replace")

            if find is not None and repl is not None:
                if not os.path.exists(full):
                    results.append({"filePath": fp, "success": False, "error": "File not found"})
                    continue
                if not os.path.isfile(full):
                    results.append({"filePath": fp, "success": False, "error": "Target is a directory, not a file"})
                    continue

                try:
                    original = pathlib.Path(full).read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    results.append({"filePath": fp, "success": False, "error": f"Failed to read file: {e}"})
                    continue

                new_content = fuzzy_find_and_replace(original, find, repl)
                if new_content is None:
                    print(f"  \u274c Edit failed for {fp}: No match found after all 5 fuzzy strategies.")
                    results.append({"filePath": fp, "success": False, "error": "Target string not found in file"})
                    continue

                try:
                    backup_file(full, fp)
                    pathlib.Path(full).write_text(new_content, encoding="utf-8")
                    print(f"  \u2705 Successfully updated {fp}")
                    results.append({"filePath": fp, "success": True})
                except Exception as e:
                    results.append({"filePath": fp, "success": False, "error": f"Failed to write file: {e}"})
                continue

            # Otherwise, full write
            content = op.get("content") or op.get("code") or op.get("text")
            if content is not None:
                if os.path.exists(full) and not os.path.isfile(full):
                    results.append({"filePath": fp, "success": False, "error": "Target is a directory, not a file"})
                    continue
                try:
                    if os.path.exists(full):
                        backup_file(full, fp)
                    pathlib.Path(full).parent.mkdir(parents=True, exist_ok=True)
                    pathlib.Path(full).write_text(content, encoding="utf-8")
                    if op.get("isEdit"):
                        print(f"  \u2705 Successfully updated {fp}")
                    results.append({"filePath": fp, "success": True})
                except Exception as e:
                    results.append({"filePath": fp, "success": False, "error": f"Failed to write file: {e}"})
                continue

        ok  = sum(1 for r in results if r["success"])
        bad = len(results) - ok
        self.send_json(200, {"results": results, "summary": {"ok": ok, "failed": bad}})


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Studio Local Code Bridge Server")
    parser.add_argument("project_dir", nargs="?", default=None, help="Target project directory (defaults to current folder or bridge.py location)")
    parser.add_argument("--dir", "-d", dest="dir_opt", default=None, help="Target project directory")
    parser.add_argument("--port", "-p", type=int, default=None, help="Port to listen on (default: 4545)")

    args = parser.parse_args()

    # Determine PORT
    if args.port:
        PORT = args.port
    elif "PORT" in os.environ and os.environ["PORT"]:
        PORT = int(os.environ["PORT"])
    else:
        PORT = DEFAULT_PORT

    # Determine PROJECT_DIR:
    # 1. CLI positional arg or --dir
    # 2. Environment variable PROJECT_DIR
    # 3. Location of bridge.py (or current working directory)
    if args.dir_opt:
        chosen_dir = args.dir_opt
    elif args.project_dir:
        chosen_dir = args.project_dir
    elif "PROJECT_DIR" in os.environ and os.environ["PROJECT_DIR"]:
        chosen_dir = os.environ["PROJECT_DIR"]
    else:
        # Default to script directory or working directory
        script_dir = pathlib.Path(__file__).parent.resolve()
        chosen_dir = os.getcwd() if os.getcwd() != str(script_dir) else str(script_dir)

    PROJECT_DIR = str(pathlib.Path(chosen_dir).resolve())

    if not os.path.isdir(PROJECT_DIR):
        print(f"\n  ⚠️  WARNING: Project directory does not exist: {PROJECT_DIR}")
        print("  Please provide a valid project folder path.\n")

    # Allow address reuse so quick restarts don't fail
    socketserver.TCPServer.allow_reuse_address = True

    print("=" * 55)
    print("   🚀 AI Studio Local Code Bridge (Python)")
    print("=" * 55)
    print(f"  📍 Project Root : {PROJECT_DIR}")
    print(f"  🌐 Bridge Port  : {PORT}")
    print(f"  🔗 Health URL   : http://127.0.0.1:{PORT}/health")
    print("  ⏳ Waiting for Chrome Extension commands...")
    print("  👉 Press Ctrl+C to stop.")
    print("=" * 55 + "\n")

    try:
        with socketserver.TCPServer(("127.0.0.1", PORT), BridgeHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  🛑 Bridge stopped by user.\n")
        sys.exit(0)
    except OSError as e:
        print(f"\n  ❌ Failed to bind to port {PORT}: {e}")
        print("  Is another instance of bridge.py or server.js already running?")
        sys.exit(1)
