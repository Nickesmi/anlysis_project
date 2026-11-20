#!/usr/bin/env python3
"""
Builds the single submission PDF (helper tool, not part of the graded program).

  report/report_body.html          hand-written report text with placeholders
  report/data/benchmark_*.csv      output of `plagiarism benchmark`
  src/*                            source code, pasted as selectable text

-> report/submission.html  and, with --pdf, a PDF printed by headless Google Chrome.

Usage (from the project folder):
  python3 tools/build_report.py --pdf report/submission.pdf
"""
import argparse
import csv
import html
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_FILES = ["src/plagiarism.h", "src/main.cpp", "src/text_processing.cpp", "src/similarity.cpp",
              "src/brute_force.cpp", "src/efficient.cpp", "src/output.cpp", "src/benchmark.cpp", "Makefile"]
DATASETS = [  # (csv file, label)
    ("benchmark_sample.csv", "Sample set, main_doc 30 sentences"),
    ("benchmark_200docs_main30.csv", "200-document set, main_doc 30 sentences"),
    ("benchmark_200docs_main230.csv", "200-document set, main_doc 230 sentences"),
]

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 9.6pt; line-height: 1.38; color: #111; }
h1 { font-size: 16pt; margin: 0 0 8px; } h2 { font-size: 12pt; margin: 12px 0 4px; color: #1d3c78; }
h3 { font-size: 10.5pt; margin: 10px 0 4px; }
.cover { page-break-after: always; padding-top: 40mm; }
.cover h1 { font-size: 22pt; } .uni { color: #555; margin-bottom: 14px; }
.part { page-break-before: always; } .cover + .part { page-break-before: auto; }
table { border-collapse: collapse; margin: 6px 0; } td, th { border: 1px solid #bbb; padding: 2px 6px; vertical-align: top; }
th { background: #eef1f6; text-align: left; }
table.members td, table.members th { padding: 5px 12px; font-size: 11pt; }
table.small { font-size: 8.8pt; width: 100%; }
table.bench { font-size: 8.6pt; margin-right: 10px; } table.bench td { text-align: right; }
.benchrow { display: flex; gap: 8px; align-items: flex-start; flex-wrap: wrap; }
.benchrow .cap { font-size: 8.4pt; font-weight: bold; margin: 2px 0; }
pre { font-family: Menlo, Consolas, monospace; white-space: pre-wrap; word-break: break-word; }
pre.cmd, pre.out, pre.pseudo { background: #f5f6f8; border: 1px solid #dde; padding: 5px 7px; font-size: 8.2pt; margin: 4px 0 8px; }
pre.code { font-size: 7.2pt; line-height: 1.25; border-top: 1px solid #ccc; padding-top: 3px; margin: 0 0 10px; }
.codefile { font-weight: bold; font-size: 9pt; margin-top: 8px; page-break-after: avoid; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; }
ul.ex { margin: 2px 0 6px 0; padding-left: 18px; } .note { color: #444; }
.plot { margin: 6px 0; }
"""


def read_csv(name):
    with open(os.path.join(ROOT, "report", "data", name)) as f:
        return list(csv.DictReader(f))


def tables_html():
    parts = ['<div class="benchrow">']
    for name, label in DATASETS:
        rows = read_csv(name)
        t = ['<div><div class="cap">%s</div><table class="bench"><tr><th>documents</th><th>brute force (ms)</th>'
             '<th>efficient (ms)</th><th>speedup</th></tr>' % html.escape(label)]
        for r in rows:
            t.append("<tr><td>%s</td><td>%.1f</td><td>%.2f</td><td>%.0f×</td></tr>" % (
                r["documents"], float(r["brute_force_ms"]), float(r["efficient_ms"]), float(r["speedup"])))
        t.append("</table></div>")
        parts.append("".join(t))
    parts.append("</div>")
    return "\n".join(parts)


COLORS = ["#1f77b4", "#d62728", "#2ca02c"]
SHORT = ["sample set (n = 30)", "200 docs (n = 30)", "200 docs (n = 230)"]


def nice_step(vmax, ticks=5):
    """Tick step 1, 2 or 5 times a power of ten giving about `ticks` ticks."""
    import math
    raw = vmax / ticks
    p = 10 ** math.floor(math.log10(raw))
    return next(m * p for m in (1, 2, 5, 10) if m * p >= raw)


def panel(series, x0, title, W=345, H=270):
    """One linear plot: series = [(label, color, dash, xs, ys)], drawn at x offset x0."""
    L, R, T, B = 50, 8, 22, 38
    xmax = max(max(s[3]) for s in series)
    ystep = nice_step(max(max(s[4]) for s in series))
    ymax = ystep * (int(max(max(s[4]) for s in series) / ystep) + 1)
    px = lambda x: x0 + L + (W - L - R) * x / xmax
    py = lambda y: T + (H - T - B) * (1 - y / ymax)
    out = ['<text x="%.1f" y="12" text-anchor="middle" font-weight="bold">%s</text>' % (x0 + (L + W - R) / 2, title)]
    y = 0.0
    while y <= ymax + 1e-9:
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#e3e3e3"/>' % (x0 + L, x0 + W - R, py(y), py(y)))
        out.append('<text x="%d" y="%.1f" text-anchor="end">%g</text>' % (x0 + L - 4, py(y) + 3, round(y, 6)))
        y += ystep
    for x in range(0, xmax + 1, 25 if xmax > 50 else 5):
        out.append('<text x="%.1f" y="%d" text-anchor="middle">%d</text>' % (px(x), H - B + 13, x))
    out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#888"/>'
               % (x0 + L, T, W - L - R, H - T - B))
    out.append('<text x="%.1f" y="%d" text-anchor="middle">number of documents</text>' % (x0 + (L + W - R) / 2, H - 8))
    out.append('<text transform="translate(%d,%.1f) rotate(-90)" text-anchor="middle">time (ms)</text>'
               % (x0 + 11, (T + H - B) / 2))
    for label, color, dash, xs, ys in series:
        pts = " ".join("%.1f,%.1f" % (px(a), py(b)) for a, b in zip(xs, ys))
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.8" stroke-dasharray="%s"/>'
                   % (pts, color, dash))
        out += ['<circle cx="%.1f" cy="%.1f" r="2.3" fill="%s"/>' % (px(a), py(b), color) for a, b in zip(xs, ys)]
    return out


def plot_svg():
    """Matching time vs number of documents: left all series, right efficient only (linear axes)."""
    brute, fast = [], []
    for (name, _), short, color in zip(DATASETS, SHORT, COLORS):
        rows = read_csv(name)
        xs = [int(r["documents"]) for r in rows]
        brute.append(("brute force, " + short, color, "6,4", xs, [float(r["brute_force_ms"]) for r in rows]))
        fast.append(("efficient, " + short, color, "", xs, [float(r["efficient_ms"]) for r in rows]))
    W, H = 700, 330
    out = ['<svg class="plot" viewBox="0 0 %d %d" width="100%%" xmlns="http://www.w3.org/2000/svg" '
           'font-family="Helvetica, Arial" font-size="10">' % (W, H)]
    out += panel(brute + fast, 0, "Brute force (dashed) and efficient (solid)")
    out += panel(fast, 355, "Efficient version only (zoomed)")
    for i, (label, color, dash, _, _) in enumerate(brute + fast):
        lx, ly = 20 + (i // 3) * 340, 288 + (i % 3) * 14
        out.append('<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="%s" stroke-width="1.8" stroke-dasharray="%s"/>'
                   % (lx, lx + 24, ly, ly, color, dash))
        out.append('<text x="%d" y="%d" font-size="9">%s</text>' % (lx + 30, ly + 3, html.escape(label)))
    out.append("</svg>")
    return "\n".join(out)


def code_html():
    parts = []
    for rel in CODE_FILES:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            text = f.read()
        parts.append('<div class="codefile">%s</div><pre class="code">%s</pre>' % (rel, html.escape(text)))
    return "\n".join(parts)


def find_chrome():
    for c in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "google-chrome", "chromium", "chromium-browser", "chrome"]:
        if os.path.exists(c) or shutil.which(c):
            return c
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", help="also print a PDF with headless Chrome")
    args = p.parse_args()
    with open(os.path.join(ROOT, "report", "report_body.html"), encoding="utf-8") as f:
        body = f.read()
    body = body.replace("{{CODE}}", code_html()).replace("{{TABLES}}", tables_html()).replace("{{PLOT}}", plot_svg())
    page = ('<!doctype html><html><head><meta charset="utf-8"><title>CMP3005 Plagiarism Detector</title>'
            '<style>%s</style></head><body>%s</body></html>' % (CSS, body))
    out_html = os.path.join(ROOT, "report", "submission.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", out_html)
    if args.pdf:
        chrome = find_chrome()
        if not chrome:
            print("Google Chrome not found: open submission.html in a browser and print it to PDF.")
            return
        pdf = os.path.abspath(args.pdf)
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf-no-header", "--print-to-pdf=" + pdf, "file://" + out_html],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("wrote", pdf)


if __name__ == "__main__":
    main()
