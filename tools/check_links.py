#!/usr/bin/env python3
"""Check the links and references of the documentation.

Usage: python tools/check_links.py [--external]

Checked, in the files git knows (tracked, or new and not ignored):
- Markdown links and pictures with a relative path, and their #anchors
- references to a named section, written as a file name in backticks followed by the title in quotes, also in the
  comments of the code
- file names in backticks that are not in the repository (generated files and foreign sources are listed in KNOWN)
- with --external also the web addresses (needs the network)

The exit code is 1 when something is broken, otherwise 0. Notes (a section title found only in the text, not as a
heading) do not change it. Only the Python standard library and git are needed.
"""
import concurrent.futures
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Names that appear in backticks and are rightly not in the repository.
KNOWN = {
    # generated here, not committed
    "demo_sets.js", "web/demo_sets.js", "firmware/include/user_sounds.h", "shield-3d-kicad.html",
    "solder_stand.stl", "solder_stand_j1_insert.stl", "work/board_full.json", "/voice/pin.wav",
    # examples of what a tool writes, or files of a planned feature
    "speaker_baseline.csv", "truck_raw.wav", "manifest.json",
    # foreign sources and frameworks: CyberBrick, Piper, Arduino
    "bbl/servos.py", "control.py", "parser.py", "src/app_rc/app/control.py", "src/app_rc/app/rc_main.py",
    "src/app_rc/bbl/executor.py", "docs/LICENSING.md", "default_8MB.csv",
}
TICK_NAME = re.compile(r"[\w./\-]+\.(md|png|jpg|svg|py|h|cpp|json|ini|csv|yml|ps1|scad|html|js|txt|wav|stl|3mf"
                       r"|kicad_pcb|kicad_sch)")


def repo_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, text=True, encoding="utf8", check=True).stdout.split("\n")
    return [f for f in out if f and os.path.isfile(os.path.join(ROOT, f))]


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf8", errors="replace") as fh:
        return fh.read()


def joined(base, path):
    return os.path.normpath(os.path.join(base, path)).replace("\\", "/")


def slug(heading):
    """The anchor GitHub makes from a heading."""
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "").strip().lower()
    return re.sub(r"[^\w\- ]", "", h).replace(" ", "-")


def anchors_of(path):
    out, seen, fence = set(), {}, False
    for line in read(path).split("\n"):
        if line.startswith("```"):
            fence = not fence
        m = re.match(r"#{1,6}\s+(.*)", line)
        if m and not fence:
            s = slug(m.group(1))
            n = seen.get(s, 0)
            seen[s] = n + 1
            out.add(s if n == 0 else f"{s}-{n}")
        out.update(re.findall(r"<a\s+(?:name|id)=\"([^\"]+)\"", line))
    return out


def check_markdown(files):
    """Returns (broken links, unknown names in backticks, {url: [places]})."""
    fileset = set(files)
    dirs = {"."}
    for f in files:
        parts = f.split("/")
        dirs.update("/".join(parts[:i]) for i in range(1, len(parts)))
    names = {f.rsplit("/", 1)[-1] for f in files}
    broken, unknown, external = [], [], {}
    for f in (x for x in files if x.lower().endswith(".md")):
        base = os.path.dirname(f)
        fence = False
        for n, line in enumerate(read(f).split("\n"), 1):
            where = f"{f}:{n}"
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            bare = re.sub(r"`[^`]*`", "", line)
            targets = re.findall(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)", bare)
            targets += re.findall(r"(?:src|href)=\"([^\"]+)\"", bare)
            for t in targets:
                if re.match(r"https?://", t):
                    external.setdefault(t, []).append(where)
                    continue
                if t.startswith("mailto:"):
                    continue
                path, _, anchor = t.partition("#")
                full = joined(base, urllib.parse.unquote(path)) if path else f
                if full not in fileset and full.rstrip("/") not in dirs:
                    broken.append(f"{where}  link  {t}")
                elif anchor and full.endswith(".md") and anchor not in anchors_of(full):
                    broken.append(f"{where}  anchor  {t}")
            for url in re.findall(r"(?<![(\"<])https?://[^\s`)<>\"|]+", bare):
                external.setdefault(url.rstrip(".,;:*"), []).append(where)
            for tick in re.findall(r"`([^`]+)`", line):
                t = tick.strip()
                if t in KNOWN or not TICK_NAME.fullmatch(t):
                    continue
                places = [joined(base, t), t] + [d + t for d in ("docs/", "firmware/", "firmware/include/", "tools/")]
                if any(p in fileset for p in places):
                    continue
                if ("/" not in t and t in names) or ("/" in t and any(x.endswith("/" + t) for x in files)):
                    continue
                unknown.append(f"{where}  {t}")
    return broken, unknown, external


def check_sections(files):
    """Returns (missing sections, notes, number of references)."""
    def norm(s):
        return re.sub(r"\s+", " ", re.sub(r"[`*]", "", s)).strip().lower()

    fileset = set(files)
    missing, notes, total = [], [], 0
    for f in files:
        if not f.endswith((".md", ".py", ".h", ".cpp", ".scad", ".html", ".ini")):
            continue
        # one line, so that a reference wrapped over two lines (also in a comment) is found
        flat = re.sub(r"\n[ \t]*(//|#|;)?[ \t]*", " ", read(f))
        for m in re.finditer(r"`?([\w./\-]+\.md)`?,? (?:section )?\(?\"([^\"]{3,80})\"", flat):
            name, title = m.group(1), m.group(2)
            target = next((c for c in (joined(os.path.dirname(f), name), name, "docs/" + name) if c in fileset), None)
            if not target:
                continue
            total += 1
            body = read(target)
            marks = re.findall(r"^#{1,6}\s+(.*)$", body, re.M) + re.findall(r"\*\*(.+?)\*\*", body, re.S)
            want = norm(title).rstrip(".")
            if any(want in norm(x) for x in marks):
                continue
            (notes if want in norm(body) else missing).append(f'{f}  {name}, "{title}"')
    return missing, notes, total


def probe(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link check)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return url, r.status
    except urllib.error.HTTPError as e:
        return url, e.code
    except Exception as e:  # noqa: BLE001
        return url, f"{type(e).__name__}: {e}"[:120]


def report(title, items):
    print(f"{title}: {len(items)}")
    for item in items:
        print("  " + item)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    files = repo_files()
    broken, unknown, external = check_markdown(files)
    missing, notes, total = check_sections(files)
    print(f"{sum(f.lower().endswith('.md') for f in files)} Markdown files, {total} references to named sections")
    report("Broken relative links and anchors", broken)
    report("Sections that do not exist", missing)
    report("File names in backticks that are not in the repository", unknown)
    report("Notes: the section title is only in the text, not a heading", notes)
    failed = list(broken + missing + unknown)
    if "--external" in sys.argv[1:]:
        urls = sorted(u for u in external if not re.search(r"localhost|127\.0\.0\.1|example\.com|\{|\.\.\.", u))
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            bad = [f"{status}  {url}  <- {', '.join(external[url][:3])}"
                   for url, status in ex.map(probe, urls) if status != 200]
        report(f"Web addresses that do not answer 200 (of {len(urls)})", bad)
        failed += bad
    print("FAILED" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
