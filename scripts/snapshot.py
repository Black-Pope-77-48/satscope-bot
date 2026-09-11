#!/usr/bin/env python3
"""Fetch live mempool.space fees and write STATUS files for ScopeBot."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone

OWNER = "Black-Pope-77-48"
REPO = "satscope-bot"
ISSUE = 1
UA = "ScopeBot/1.0"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode())


def fetch(path: str) -> dict:
    hosts = ("https://mempool.space", "https://mempool.emzy.de")
    last = None
    for host in hosts:
        try:
            return get_json(f"{host}{path}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            last = err
    raise RuntimeError(f"mempool fetch failed for {path}: {last}")


def classify(fastest: int) -> str:
    if fastest >= 50:
        return "congested"
    if fastest >= 8:
        return "busy"
    if fastest <= 2:
        return "empty"
    return "calm"


def write_status(payload: dict, markdown: str) -> None:
    with open("STATUS.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    with open("STATUS.md", "w", encoding="utf-8") as handle:
        handle.write(markdown)


def post_issue_comment(body: str) -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GH_TOKEN; skip issue comment")
        return
    data = json.dumps({"body": body}).encode()
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{ISSUE}/comments"
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            print(f"commented issue #{ISSUE} ({res.status})")
    except urllib.error.HTTPError as err:
        print(f"issue comment failed: {err.code} {err.read()[:200]!r}")


def maybe_commit() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    subprocess.check_call(["git", "config", "user.name", "github-actions[bot]"])
    subprocess.check_call(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ]
    )
    subprocess.check_call(["git", "add", "STATUS.json", "STATUS.md"])
    dirty = subprocess.call(["git", "diff", "--cached", "--quiet"])
    if dirty == 0:
        print("No STATUS change")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    subprocess.check_call(["git", "commit", "-m", f"chore: mempool snapshot {stamp}"])
    subprocess.check_call(["git", "push"])


def main() -> None:
    fees = fetch("/api/v1/fees/recommended")
    pool = fetch("/api/mempool")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fastest = int(fees.get("fastestFee") or 0)
    condition = classify(fastest)
    count = int(pool.get("count") or 0)
    vsize = int(pool.get("vsize") or 0)
    total_fee = int(pool.get("total_fee") or 0)
    mvb = vsize / 1e6

    payload = {
        "bot": "ScopeBot",
        "updatedAt": now,
        "source": "https://mempool.space",
        "github": f"{OWNER}/{REPO}",
        "fork": f"{OWNER}/mempool",
        "fees": fees,
        "mempool": {"count": count, "vsize": vsize, "totalFee": total_fee},
        "condition": condition,
    }

    markdown = "\n".join(
        [
            "# ScopeBot snapshot",
            "",
            f"Updated `{now}` from [mempool.space](https://mempool.space).",
            "",
            f"- GitHub: [{OWNER}/{REPO}](https://github.com/{OWNER}/{REPO})",
            f"- Fork: [{OWNER}/mempool](https://github.com/{OWNER}/mempool)",
            f"- Condition: {condition}",
            f"- Next block: {fees.get('fastestFee')} sat/vB",
            f"- 30 min: {fees.get('halfHourFee')} sat/vB",
            f"- 1 hour: {fees.get('hourFee')} sat/vB",
            f"- Economy: {fees.get('economyFee')} sat/vB",
            f"- Unconfirmed: {count:,}",
            f"- Mempool vsize: {mvb:.1f} MvB",
            "",
            "Posted by ScopeBot.",
            "",
        ]
    )

    write_status(payload, markdown)
    comment = (
        f"ScopeBot {now} — next block {fastest} sat/vB ({condition}), "
        f"{count:,} unconfirmed. Source: mempool.space"
    )
    print(comment)
    post_issue_comment(comment)
    maybe_commit()


if __name__ == "__main__":
    main()
