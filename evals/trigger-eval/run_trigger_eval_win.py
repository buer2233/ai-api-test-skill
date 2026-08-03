#!/usr/bin/env python3
"""Windows-compatible trigger eval for api-test-E10.

Differences from skill-creator run_eval.py:
1. Avoids select() on pipes (broken on Windows).
2. Uses claude.cmd / node cli.js on Windows.
3. Detects the real project skill name (api-test-E10).
4. Supports checkpoint/resume so a long batch is not lost on outer timeout.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def parse_skill_md(skill_path: Path) -> tuple[str, str]:
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    lines = content.split("\n")
    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("SKILL.md missing closing frontmatter")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:") :].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:") :].strip()
            if value in (">", "|", ">-", "|-"):
                continuation: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (
                    frontmatter_lines[i].startswith("  ")
                    or frontmatter_lines[i].startswith("\t")
                ):
                    continuation.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation)
                continue
            description = value.strip('"').strip("'")
        i += 1
    return name, description


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def resolve_claude_cmd() -> list[str]:
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd",
        Path(os.environ.get("LOCALAPPDATA", "")) / "npm" / "claude.cmd",
    ]
    for cand in candidates:
        if cand.is_file():
            return [str(cand)]

    cli_js = (
        Path(os.environ.get("APPDATA", ""))
        / "npm"
        / "node_modules"
        / "@anthropic-ai"
        / "claude-code"
        / "cli.js"
    )
    if cli_js.is_file():
        return ["node", str(cli_js)]
    return ["claude"]


def is_skill_hit(blob: str, skill_name: str) -> bool:
    blob_l = blob.lower()
    name_l = skill_name.lower()
    if name_l in blob_l:
        return True
    tokens = [
        f"skills/{skill_name}",
        f"skills\\{skill_name}",
        f".claude/skills/{skill_name}",
        f".claude\\skills\\{skill_name}",
        f"{skill_name}/SKILL.md",
        f"{skill_name}\\SKILL.md",
    ]
    return any(token.lower() in blob_l for token in tokens)


def run_single_query(
    query: str,
    skill_name: str,
    timeout: int,
    project_root: Path,
    model: str | None = None,
) -> tuple[bool | None, str, float]:
    """Return (triggered, detail, elapsed_sec).

    ``None`` means the runner could not make a trigger decision (for example,
    a timeout).  It must not be treated as a negative result because doing so
    turns infrastructure slowness into a skill failure.
    """
    detail = "no_signal"
    claude_prefix = resolve_claude_cmd()
    cmd = [
        *claude_prefix,
        "-p",
        query,
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--max-turns",
        "1",
        "--no-session-persistence",
    ]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    if "CLAUDE_CODE_GIT_BASH_PATH" not in env:
        for bash in (
            r"D:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\bin\bash.exe",
        ):
            if Path(bash).is_file():
                env["CLAUDE_CODE_GIT_BASH_PATH"] = bash
                break

    t0 = time.time()
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    triggered: bool | None = None
    pending_tool_name = None
    accumulated_json = ""
    done = threading.Event()

    def reader() -> None:
        nonlocal triggered, pending_tool_name, accumulated_json, detail
        assert process.stdout is not None
        try:
            for raw in process.stdout:
                if done.is_set() or triggered:
                    break
                line = raw.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")
                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            if tool_name in ("Skill", "Read"):
                                pending_tool_name = tool_name
                                accumulated_json = ""
                            else:
                                triggered = False
                                detail = f"other_tool:{tool_name}"
                                done.set()
                                return
                    elif se_type == "content_block_delta" and pending_tool_name:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            accumulated_json += delta.get("partial_json", "")
                            if is_skill_hit(accumulated_json, skill_name):
                                triggered = True
                                detail = f"stream:{pending_tool_name}"
                                done.set()
                                return
                    elif se_type in ("content_block_stop", "message_stop"):
                        if pending_tool_name:
                            triggered = is_skill_hit(accumulated_json, skill_name)
                            detail = (
                                f"stream_stop:{pending_tool_name}:"
                                f"{'hit' if triggered else 'miss'}"
                            )
                            done.set()
                            return
                        if se_type == "message_stop":
                            detail = "message_stop_no_tool"
                            triggered = False
                            done.set()
                            return
                elif event.get("type") == "assistant":
                    message = event.get("message", {})
                    for content_item in message.get("content", []):
                        if content_item.get("type") != "tool_use":
                            continue
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        blob = json.dumps(tool_input, ensure_ascii=False)
                        if tool_name == "Skill" and is_skill_hit(blob, skill_name):
                            triggered = True
                            detail = "assistant:Skill"
                        elif tool_name == "Read" and is_skill_hit(blob, skill_name):
                            triggered = True
                            detail = "assistant:Read"
                        else:
                            triggered = False
                            detail = f"assistant_other:{tool_name}"
                        done.set()
                        return
                elif event.get("type") == "result":
                    detail = detail if detail != "no_signal" else "result_no_trigger"
                    if detail == "result_no_trigger":
                        triggered = False
                    done.set()
                    return
        finally:
            done.set()

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    finished = done.wait(timeout=timeout)
    if process.poll() is None:
        process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
    t.join(timeout=2)

    if not finished and detail == "no_signal":
        detail = "timeout"
        triggered = None
    return triggered, detail, time.time() - t0


def load_checkpoint(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    jobs = data.get("jobs", {})
    return jobs if isinstance(jobs, dict) else {}


def save_checkpoint(path: Path, jobs: dict[str, dict], meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "meta": meta,
        "jobs": jobs,
        "completed": len(jobs),
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def job_key(query_idx: int, run_idx: int) -> str:
    return f"q{query_idx}-r{run_idx}"


def aggregate(
    eval_set: list[dict],
    job_results: dict[str, dict],
    skill_name: str,
    description: str,
    branch_map: dict[str, dict],
    runs_per_query: int,
    trigger_threshold: float,
    timeout: int,
    num_workers: int,
    model: str | None,
    project_root: Path,
) -> dict:
    results = []
    for q_idx, item in enumerate(eval_set):
        triggers: list[bool] = []
        inconclusive = 0
        details: list[str] = []
        for run_idx in range(runs_per_query):
            key = job_key(q_idx, run_idx)
            job = job_results.get(key)
            if not job:
                inconclusive += 1
                details.append("pending")
                continue
            value = job.get("triggered")
            if value is None:
                inconclusive += 1
            else:
                triggers.append(bool(value))
            details.append(str(job.get("detail", "")))
        if not triggers and not inconclusive:
            continue
        trigger_rate = sum(triggers) / len(triggers) if triggers else None
        should_trigger = bool(item["should_trigger"])
        did_pass = None
        if trigger_rate is not None:
            did_pass = (
                trigger_rate >= trigger_threshold
                if should_trigger
                else trigger_rate < trigger_threshold
            )
        meta = branch_map.get(item["query"], {})
        results.append(
            {
                "query": item["query"],
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers) + inconclusive,
                "decisive_runs": len(triggers),
                "inconclusive_runs": inconclusive,
                "pass": did_pass,
                "details": details,
                "id": meta.get("id"),
                "branch": meta.get("branch"),
                "category": meta.get("category"),
            }
        )

    branch_stats: dict[str, dict] = {}
    for r in results:
        branch = r.get("branch") or (
            "should_trigger" if r["should_trigger"] else "should_not_trigger"
        )
        stat = branch_stats.setdefault(
            branch,
            {
                "branch": branch,
                "count": 0,
                "passed": 0,
                "inconclusive": 0,
                "inconclusive_runs": 0,
                "mean_trigger_rate": 0.0,
                "should_trigger_values": [],
            },
        )
        stat["count"] += 1
        stat["passed"] += 1 if r["pass"] is True else 0
        stat["inconclusive"] += 1 if r["pass"] is None else 0
        stat["inconclusive_runs"] += r["inconclusive_runs"]
        if r["trigger_rate"] is not None:
            stat["mean_trigger_rate"] += r["trigger_rate"]
        stat["should_trigger_values"].append(r["should_trigger"])
    for stat in branch_stats.values():
        assessed = stat["count"] - stat["inconclusive"]
        stat["assessed"] = assessed
        stat["mean_trigger_rate"] = stat["mean_trigger_rate"] / max(assessed, 1)
        vals = set(stat.pop("should_trigger_values"))
        stat["should_trigger"] = sorted(vals)[0] if len(vals) == 1 else list(vals)
        stat["pass_rate"] = stat["passed"] / max(assessed, 1)

    pos = [r for r in results if r["should_trigger"]]
    neg = [r for r in results if not r["should_trigger"]]
    passed = sum(1 for r in results if r["pass"] is True)
    inconclusive = sum(1 for r in results if r["pass"] is None)
    inconclusive_runs = sum(r["inconclusive_runs"] for r in results)
    decisive_runs = sum(r["decisive_runs"] for r in results)
    total = len(results)
    assessed = total - inconclusive
    summary = {
        "total": total,
        "passed": passed,
        "failed": total - passed - inconclusive,
        "inconclusive": inconclusive,
        "inconclusive_runs": inconclusive_runs,
        "decisive_runs": decisive_runs,
        "assessed": assessed,
        "accuracy": passed / max(assessed, 1),
        "positive_count": len(pos),
        "positive_passed": sum(1 for r in pos if r["pass"] is True),
        "positive_inconclusive": sum(1 for r in pos if r["pass"] is None),
        "positive_mean_trigger_rate": (
            sum(r["trigger_rate"] for r in pos if r["trigger_rate"] is not None)
            / max(sum(r["trigger_rate"] is not None for r in pos), 1)
        ),
        "negative_count": len(neg),
        "negative_passed": sum(1 for r in neg if r["pass"] is True),
        "negative_inconclusive": sum(1 for r in neg if r["pass"] is None),
        "negative_mean_trigger_rate": (
            sum(r["trigger_rate"] for r in neg if r["trigger_rate"] is not None)
            / max(sum(r["trigger_rate"] is not None for r in neg), 1)
        ),
        "jobs_completed": len(job_results),
        "jobs_expected": len(eval_set) * runs_per_query,
    }
    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": summary,
        "branch_stats": sorted(branch_stats.values(), key=lambda x: x["branch"]),
        "config": {
            "runs_per_query": runs_per_query,
            "trigger_threshold": trigger_threshold,
            "timeout": timeout,
            "num_workers": num_workers,
            "model": model,
            "project_root": str(project_root),
        },
    }


def write_report(output: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = out_path.with_suffix(".md")
    s = output["summary"]
    lines = [
        f"# Trigger Eval Report: {output['skill_name']}",
        "",
        f"- accuracy: **{s['accuracy']:.1%}** ({s['passed']}/{s['assessed']} assessed)",
        f"- inconclusive queries: **{s['inconclusive']}** ({s['total']} total)",
        f"- inconclusive runs: **{s['inconclusive_runs']}** "
        f"({s['decisive_runs']} decisive)",
        f"- positive mean trigger rate: **{s['positive_mean_trigger_rate']:.1%}** "
        f"({s['positive_passed']}/{s['positive_count']} passed, "
        f"{s['positive_inconclusive']} inconclusive)",
        f"- negative mean trigger rate: **{s['negative_mean_trigger_rate']:.1%}** "
        f"({s['negative_passed']}/{s['negative_count']} passed as non-trigger, "
        f"{s['negative_inconclusive']} inconclusive)",
        f"- jobs: {s.get('jobs_completed', '?')}/{s.get('jobs_expected', '?')}",
        f"- runs_per_query: {output['config']['runs_per_query']}",
        f"- threshold: {output['config']['trigger_threshold']}",
        f"- model: {output['config']['model'] or '(default)'}",
        "",
        "## Branch stats",
        "",
        "| branch | count | pass_rate | mean_trigger_rate | should_trigger |",
        "|---|---:|---:|---:|---|",
    ]
    for b in output["branch_stats"]:
        lines.append(
            f"| `{b['branch']}` | {b['count']} | {b['pass_rate']:.0%} | "
            f"{b['mean_trigger_rate']:.0%} | {b['should_trigger']} "
            f"({b['inconclusive']} queries, {b['inconclusive_runs']} runs inconclusive) |"
        )
    lines.extend(["", "## Per query", ""])
    for r in output["results"]:
        status = (
            "PASS" if r["pass"] is True
            else "FAIL" if r["pass"] is False
            else "INCONCLUSIVE"
        )
        q = r["query"].replace("\n", " ")[:80]
        branch = r.get("branch") or "-"
        lines.append(
            f"- [{status}] id={r.get('id')} branch=`{branch}` "
            f"rate={r['triggers']}/{r['decisive_runs']} decisive, "
            f"{r['inconclusive_runs']} inconclusive expected={r['should_trigger']} | {q}"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    project_root: Path,
    num_workers: int,
    timeout: int,
    runs_per_query: int,
    trigger_threshold: float,
    model: str | None,
    branch_map: dict[str, dict],
    checkpoint_path: Path,
    output_path: Path,
    verbose: bool,
) -> dict:
    job_results = load_checkpoint(checkpoint_path)
    meta = {
        "skill_name": skill_name,
        "runs_per_query": runs_per_query,
        "timeout": timeout,
        "num_workers": num_workers,
        "model": model,
        "project_root": str(project_root),
    }

    pending: list[tuple[int, int, dict]] = []
    for q_idx, item in enumerate(eval_set):
        for run_idx in range(runs_per_query):
            key = job_key(q_idx, run_idx)
            if key not in job_results:
                pending.append((q_idx, run_idx, item))

    total_jobs = len(eval_set) * runs_per_query
    if verbose:
        print(
            f"checkpoint={checkpoint_path} completed={len(job_results)}/{total_jobs} "
            f"pending={len(pending)}",
            file=sys.stderr,
            flush=True,
        )

    lock = threading.Lock()

    def work(q_idx: int, run_idx: int, item: dict) -> tuple[str, dict]:
        triggered, detail, elapsed = run_single_query(
            query=item["query"],
            skill_name=skill_name,
            timeout=timeout,
            project_root=project_root,
            model=model,
        )
        return job_key(q_idx, run_idx), {
            "query_idx": q_idx,
            "run_idx": run_idx,
            "should_trigger": bool(item["should_trigger"]),
            "triggered": triggered,
            "detail": detail,
            "elapsed_sec": round(elapsed, 2),
            "query_preview": item["query"].replace("\n", " ")[:80],
        }

    completed_now = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_map = {
            executor.submit(work, q_idx, run_idx, item): (q_idx, run_idx, item)
            for q_idx, run_idx, item in pending
        }
        for future in as_completed(future_map):
            q_idx, run_idx, item = future_map[future]
            try:
                key, result = future.result()
            except Exception as exc:  # noqa: BLE001
                key = job_key(q_idx, run_idx)
                result = {
                    "query_idx": q_idx,
                    "run_idx": run_idx,
                    "should_trigger": bool(item["should_trigger"]),
                    "triggered": None,
                    "detail": f"error:{exc}",
                    "elapsed_sec": 0,
                    "query_preview": item["query"].replace("\n", " ")[:80],
                }
            with lock:
                job_results[key] = result
                completed_now += 1
                save_checkpoint(checkpoint_path, job_results, meta)
                # incremental report for crash safety
                partial = aggregate(
                    eval_set=eval_set,
                    job_results=job_results,
                    skill_name=skill_name,
                    description=description,
                    branch_map=branch_map,
                    runs_per_query=runs_per_query,
                    trigger_threshold=trigger_threshold,
                    timeout=timeout,
                    num_workers=num_workers,
                    model=model,
                    project_root=project_root,
                )
                write_report(partial, output_path)
            if verbose:
                short = item["query"].replace("\n", " ")[:60]
                outcome = (
                    "HIT" if result["triggered"] is True
                    else "MISS" if result["triggered"] is False
                    else "INCONCLUSIVE"
                )
                print(
                    f"[{len(job_results)}/{total_jobs}] "
                    f"{outcome} "
                    f"q={q_idx} run={run_idx + 1} "
                    f"detail={result['detail']} elapsed={result['elapsed_sec']}s | {short}",
                    file=sys.stderr,
                    flush=True,
                )

    output = aggregate(
        eval_set=eval_set,
        job_results=job_results,
        skill_name=skill_name,
        description=description,
        branch_map=branch_map,
        runs_per_query=runs_per_query,
        trigger_threshold=trigger_threshold,
        timeout=timeout,
        num_workers=num_workers,
        model=model,
        project_root=project_root,
    )
    write_report(output, output_path)
    return output


def main() -> None:
    # Force UTF-8 stderr/stdout where possible (Windows consoles are often GBK).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--annotated-set", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint", default=None, help="JSON checkpoint path for resume")
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--model", default=None)
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    skill_path = Path(args.skill_path)
    name, description = parse_skill_md(skill_path)
    project_root = (
        Path(args.project_root).resolve()
        if args.project_root
        else find_project_root(skill_path)
    )
    out_path = Path(args.output)
    checkpoint_path = (
        Path(args.checkpoint)
        if args.checkpoint
        else out_path.with_name(out_path.stem + ".checkpoint.json")
    )

    branch_map: dict[str, dict] = {}
    if args.annotated_set:
        annotated = json.loads(Path(args.annotated_set).read_text(encoding="utf-8"))
        for item in annotated:
            branch_map[item["query"]] = {
                "id": item.get("id"),
                "branch": item.get("branch"),
                "category": item.get("category"),
            }

    if args.verbose:
        print(f"skill={name}", file=sys.stderr, flush=True)
        print(f"project_root={project_root}", file=sys.stderr, flush=True)
        print(
            f"queries={len(eval_set)} runs_per_query={args.runs_per_query} "
            f"workers={args.num_workers} timeout={args.timeout}",
            file=sys.stderr,
            flush=True,
        )

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        project_root=project_root,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
        branch_map=branch_map,
        checkpoint_path=checkpoint_path,
        output_path=out_path,
        verbose=args.verbose,
    )
    s = output["summary"]
    if args.verbose:
        print(
            f"Results: {s['passed']}/{s['total']} passed "
            f"(accuracy={s['accuracy']:.1%}) "
            f"jobs={s.get('jobs_completed')}/{s.get('jobs_expected')}",
            file=sys.stderr,
            flush=True,
        )
    print(
        json.dumps(
            {
                "output": str(out_path),
                "checkpoint": str(checkpoint_path),
                "summary": s,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
