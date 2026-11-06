#!/usr/bin/env python3
"""Repo helper for REAPER Video processor scripts. Standard library only.

    python3 tools/vp.py check                       lint every script, verify README catalog (CI runs this)
    python3 tools/vp.py check scripts/foo/foo.eel   lint specific files only
    python3 tools/vp.py new <name> "<description>"  scaffold scripts/<name>/ from templates/script/
    python3 tools/vp.py catalog                     rewrite the script table in README.md

We can't run REAPER in CI, so `check` catches the mistakes that are easy to make
in EEL2 and hard to spot by eye (see docs/video-processor-notes.md, "Gotchas").
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "templates" / "script"
README = ROOT / "README.md"
CAT_START, CAT_END = "<!-- catalog:start -->", "<!-- catalog:end -->"
MAX_PARAMS = 40  # Video processor supports //@param 1..40
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Variables the Video processor defines itself; a //@param must not reuse them.
BUILTINS = {
    "time", "project_w", "project_h", "framerate", "param_wet", "colorspace",
    "gfx_r", "gfx_g", "gfx_b", "gfx_a", "gfx_a2", "gfx_mode", "gfx_dest",
} | {f"param{i}" for i in range(1, MAX_PARAMS + 1)}

PARAM_RE = re.compile(r"^//@param\s*(\d+)\s*(?::\s*([A-Za-z_][\w.]*))?\s+(['\"])(.*?)\3\s*(.*)$")
META_RE = re.compile(r"^//\s*@(description|version|author)\b\s*(.*)$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


class Finding:
    def __init__(self, path, line, msg):
        self.path, self.line, self.msg = path, line, msg

    def __str__(self):
        rel = self.path.relative_to(ROOT) if self.path.is_absolute() and ROOT in self.path.parents else self.path
        return f"{rel}:{self.line}: {self.msg}"


# ---------------------------------------------------------------- parsing

def strip_comments_and_strings(src: str) -> str:
    """Blank out comments and string literals, keeping line/column positions."""
    out, i, n = [], 0, len(src)
    while i < n:
        c, nxt = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j])); i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            seg = src[i:j]
            out.append(seg[0] + re.sub(r"[^\n]", " ", seg[1:-1]) + seg[-1] if len(seg) > 1 else seg); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


TOKEN_RE = re.compile(r"""
    (?P<num>\$x[0-9A-Fa-f]+|0x[0-9A-Fa-f]+|\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+)
  | (?P<ident>[A-Za-z_#][\w.]*)
  | (?P<op>===|!==|==|!=|<=|>=|&&|\|\||<<|>>|[-+*/%|&^]=|[=?:;,()\[\]{}<>!+\-*/%|&^~])
  | (?P<ws>\s+)
  | (?P<other>.)
""", re.X)

ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%=", "|=", "&=", "^="}


def tokens(code: str):
    line = 1
    for m in TOKEN_RE.finditer(code):
        kind, text = m.lastgroup, m.group()
        if kind != "ws":
            yield kind, text, line
        line += text.count("\n")


def parse_header(lines):
    params, meta = [], {}
    for no, raw in enumerate(lines, 1):
        s = raw.strip()
        if s.startswith("//@param"):
            params.append((no, s))
        m = META_RE.match(s)
        if m:
            meta[m.group(1)] = (no, m.group(2).strip())
    return params, meta


# ---------------------------------------------------------------- checks

def check_params(path, params):
    found, seen_idx, seen_var = [], {}, {}
    if len(params) > MAX_PARAMS:
        found.append(Finding(path, params[-1][0], f"{len(params)} params; the Video processor allows {MAX_PARAMS}"))
    for no, s in params:
        m = PARAM_RE.match(s)
        if not m:
            found.append(Finding(path, no, "can't parse //@param line; expected //@paramN:var 'Name' def min max mid step"))
            continue
        idx, var, _, _name, rest = m.groups()
        idx = int(idx)
        if not 1 <= idx <= MAX_PARAMS:
            found.append(Finding(path, no, f"param index {idx} outside 1..{MAX_PARAMS}"))
        if idx in seen_idx:
            found.append(Finding(path, no, f"param index {idx} already used on line {seen_idx[idx]}"))
        seen_idx[idx] = no
        if not var:
            found.append(Finding(path, no, "give the param a variable name (//@paramN:name ...)"))
        else:
            key = var.lower()
            if key in BUILTINS:
                found.append(Finding(path, no, f"param variable '{var}' clashes with built-in '{key}'"))
            if key in seen_var:
                found.append(Finding(path, no, f"param variable '{var}' already used on line {seen_var[key]} (EEL2 names ignore case)"))
            seen_var[key] = no
        nums = rest.split()
        try:
            vals = [float(x) for x in nums]
        except ValueError:
            found.append(Finding(path, no, f"non-numeric value in '{rest}'"))
            continue
        if len(vals) > 5:
            found.append(Finding(path, no, "too many values; expected def min max mid step"))
        if len(vals) >= 3:
            d, lo, hi = vals[:3]
            if lo > hi:
                found.append(Finding(path, no, f"min {lo:g} > max {hi:g}"))
            elif not lo <= d <= hi:
                found.append(Finding(path, no, f"default {d:g} outside {lo:g}..{hi:g}"))
            if len(vals) >= 4 and not lo <= vals[3] <= hi:
                found.append(Finding(path, no, f"mid value {vals[3]:g} outside {lo:g}..{hi:g}"))
    return found


def check_code(path, code):
    """Paren balance, ambiguous ternary/assignment mixes, case-only name clashes."""
    found = []
    stack = [{"assign": None, "q": None, "open": None}]
    spellings = {}
    for kind, text, line in tokens(code):
        st = stack[-1]
        if kind == "ident":
            spellings.setdefault(text.lower(), {}).setdefault(text, line)
        elif text in ("(", "["):
            stack.append({"assign": None, "q": None, "open": (text, line)})
        elif text in (")", "]"):
            if len(stack) == 1:
                found.append(Finding(path, line, f"unmatched '{text}'"))
                continue
            opener = stack.pop()["open"]
            if (opener[0], text) not in (("(", ")"), ("[", "]")):
                found.append(Finding(path, line, f"'{text}' closes '{opener[0]}' from line {opener[1]}"))
        elif text in (";", ","):
            st["assign"] = st["q"] = None
        elif text in ASSIGN_OPS:
            if st["q"] is not None:
                found.append(Finding(path, line,
                    "assignment inside a ternary branch without parentheses; write  c ? (x = 1) : (y = 2)"))
            st["assign"] = line
        elif text == "?":
            if st["assign"] is not None:
                found.append(Finding(path, line,
                    "ternary on the right of an assignment without parentheses; write  x = (c ? a : b)"))
            st["q"] = line
    for st in stack[1:]:
        found.append(Finding(path, st["open"][1], f"'{st['open'][0]}' never closed"))
    for low, forms in spellings.items():
        if len(forms) > 1:
            desc = ", ".join(f"'{k}' (line {v})" for k, v in forms.items())
            found.append(Finding(path, min(forms.values()),
                f"EEL2 names ignore case, so these are the same variable: {desc}"))
    return found


def check_script_file(path: pathlib.Path):
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    params, meta = parse_header(lines)
    found = check_params(path, params)
    for key in ("description", "version", "author"):
        if key not in meta or not meta[key][1]:
            found.append(Finding(path, 1, f"missing header line  // @{key} ..."))
    if "version" in meta and meta["version"][1] and not VERSION_RE.match(meta["version"][1]):
        found.append(Finding(path, meta["version"][0], "version must look like 1.2.3"))
    found += check_code(path, strip_comments_and_strings(src))
    return found, meta


def script_dirs():
    return sorted(p for p in SCRIPTS.iterdir() if p.is_dir()) if SCRIPTS.exists() else []


def check_repo():
    found = []
    for d in script_dirs():
        eel = d / f"{d.name}.eel"
        if not NAME_RE.match(d.name):
            found.append(Finding(d, 0, "folder name must be lowercase-kebab-case"))
        if not eel.exists():
            found.append(Finding(d, 0, f"missing {eel.name} (script file must match folder name)"))
            continue
        f, meta = check_script_file(eel)
        found += f
        readme = d / "README.md"
        if not readme.exists():
            found.append(Finding(d, 0, "missing README.md"))
        elif "version" in meta:
            text = readme.read_text(encoding="utf-8")
            ver = meta["version"][1]
            if "## Changelog" not in text:
                found.append(Finding(readme, 0, "missing '## Changelog' section"))
            elif not re.search(rf"^#+\s*{re.escape(ver)}\b", text.split("## Changelog", 1)[1], re.M):
                found.append(Finding(readme, 0, f"Changelog has no '### {ver}' entry for the script's @version"))
    if README.exists() and render_catalog_into(README.read_text(encoding="utf-8")) != README.read_text(encoding="utf-8"):
        found.append(Finding(README, 0, "script catalog is out of date; run  python3 tools/vp.py catalog"))
    return found


# ---------------------------------------------------------------- catalog

def catalog_table():
    rows = ["| Script | What it does | Version |", "|---|---|---|"]
    for d in script_dirs():
        eel = d / f"{d.name}.eel"
        if not eel.exists():
            continue
        _, meta = parse_header(eel.read_text(encoding="utf-8").splitlines())
        desc = meta.get("description", (0, ""))[1].replace("|", "\\|")
        ver = meta.get("version", (0, "?"))[1]
        rows.append(f"| [{d.name}](scripts/{d.name}/) | {desc} | {ver} |")
    return "\n".join(rows)


def render_catalog_into(text):
    if CAT_START not in text or CAT_END not in text:
        return text
    head, rest = text.split(CAT_START, 1)
    _, tail = rest.split(CAT_END, 1)
    return f"{head}{CAT_START}\n{catalog_table()}\n{CAT_END}{tail}"


def cmd_catalog():
    text = README.read_text(encoding="utf-8")
    new = render_catalog_into(text)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README.md catalog updated")
    else:
        print("README.md catalog already up to date")
    return 0


# ---------------------------------------------------------------- new

def git_author():
    try:
        name = subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        name = ""
    return name or "unknown"


def cmd_new(name, description):
    if not NAME_RE.match(name):
        print(f"name must be lowercase-kebab-case, got '{name}'"); return 2
    dest = SCRIPTS / name
    if dest.exists():
        print(f"{dest.relative_to(ROOT)} already exists"); return 2
    dest.mkdir(parents=True)
    subs = {"{{name}}": name, "{{description}}": description, "{{author}}": git_author()}
    for src in TEMPLATE.iterdir():
        text = src.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        out = dest / (f"{name}.eel" if src.suffix == ".eel" else src.name)
        out.write_text(text, encoding="utf-8")
        print(f"created {out.relative_to(ROOT)}")
    return cmd_catalog()


# ---------------------------------------------------------------- main

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "check":
        found = []
        if args:
            for a in args:
                found += check_script_file(pathlib.Path(a).resolve())[0]
        else:
            found = check_repo()
        for f in found:
            print(f)
        print(f"{len(found)} problem(s)" if found else "all checks passed")
        return 1 if found else 0
    if cmd == "catalog":
        return cmd_catalog()
    if cmd == "new" and len(args) == 2:
        return cmd_new(*args)
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
