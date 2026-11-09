"""GitHub Action entry point: sitemap / URL list -> SpeedyIndex index check or indexing task."""
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

from speedyindex import SpeedyIndex, SpeedyIndexError

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def env(name, default=""):
    return (os.environ.get(name) or default).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "speedyindex-action"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def read_sitemap(url, depth=0):
    """Return [(loc, lastmod)] from a sitemap or a sitemap index (one level of nesting)."""
    root = ET.fromstring(fetch(url))
    out = []
    if root.tag == NS + "sitemapindex" and depth == 0:
        for sm in root.findall(NS + "sitemap"):
            loc = sm.findtext(NS + "loc")
            if loc:
                out += read_sitemap(loc.strip(), depth + 1)
    else:
        for u in root.findall(NS + "url"):
            loc = u.findtext(NS + "loc")
            if loc:
                out.append((loc.strip(), (u.findtext(NS + "lastmod") or "").strip()))
    return out


def output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


def main():
    engine, mode = env("SI_ENGINE", "google"), env("SI_MODE", "check")
    if mode not in ("check", "index"):
        sys.exit("mode must be check or index")
    entries = []
    if env("SI_SITEMAP"):
        entries += read_sitemap(env("SI_SITEMAP"))
    if env("SI_URLS_FILE"):
        with open(env("SI_URLS_FILE"), encoding="utf-8") as f:
            entries += [(line.strip(), "") for line in f if line.strip() and not line.startswith("#")]
    if not entries:
        sys.exit("No URLs: set sitemap or urls-file")
    entries.sort(key=lambda e: e[1], reverse=True)  # newest lastmod first
    seen, urls = set(), []
    for loc, _ in entries:
        if loc not in seen:
            seen.add(loc)
            urls.append(loc)
    urls = urls[: int(env("SI_MAX", "1000"))]

    si = SpeedyIndex()
    task_type = "checker" if mode == "check" else "indexer"
    try:
        task = si.create_task(urls, engine=engine, task_type=task_type, title=f"github-action {os.environ.get('GITHUB_REPOSITORY', '')}")
    except SpeedyIndexError as exc:
        sys.exit(f"SpeedyIndex: {exc}")
    task_id = task.get("task_id", "")
    output("task-id", task_id)
    output("total", len(urls))
    summary(f"### SpeedyIndex {engine} {task_type}\n\nTask `{task_id}` created for {len(urls)} URLs.")

    if mode != "check" or int(env("SI_WAIT", "20")) <= 0:
        output("unindexed", "")
        return
    deadline = time.time() + int(env("SI_WAIT", "20")) * 60
    report = None
    while time.time() < deadline:
        time.sleep(30)
        report = si.report(task_id, engine=engine, task_type="checker")
        if report.get("processed_count", 0) >= report.get("size", len(urls)):
            break
    if not report or report.get("processed_count", 0) < report.get("size", len(urls)):
        output("unindexed", "")
        summary("Report not ready yet; open the task in the SpeedyIndex dashboard later.")
        return
    unindexed = report.get("unindexed_links") or []
    output("unindexed", len(unindexed))
    summary(f"Indexed: {len(report.get('indexed_links') or [])} / {report.get('size')}. Unindexed: {len(unindexed)}.")
    if unindexed:
        summary("\n<details><summary>Unindexed URLs</summary>\n\n" + "\n".join(f"- {u}" for u in unindexed[:500]) + "\n\n</details>")
    if unindexed and env("SI_FAIL").lower() == "true":
        sys.exit(1)


if __name__ == "__main__":
    main()
