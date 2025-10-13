#!/usr/bin/env python3
"""
Batchtools (Python, oc package): Unified OpenShift helpers with native oc Python client — no bash.

Subcommands:
  • bjobs: List Jobs, optionally watch (-w/--watch)
  • bpods: Show Pods belonging to Job(s) (by job-name label); all if none specified
  • blog:  Show logs for Pods of given Job(s); all if none specified (accepts --follow)
  • bdel:  Delete Job(s); delete all if none specified

Global options:
  • --login (optional)     Perform an oc login before subcommand
  • --server URL           API server, e.g. https://api.example:6443
  • --token TOKEN          Bearer token for login (safer via env: OC_TOKEN)
  • --username USER        Basic auth username
  • --password PASS        Basic auth password (discouraged; prefer --token)
  • --insecure-skip-tls-verify   Pass through to oc login (bool flag)
  • -n/--namespace NS      Namespace to target for all calls (default: current context)

Implementation notes:
  • Uses the Python oc client (either `openshift_client` or `oc`).
  • Selectors (`oc.selector`) fetch Jobs/Pods; deletions use `selector.delete()`.
  • `--watch` streams via `oc.invoke(["get","-w","jobs"])` (library handles the process lifecycle).
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys
from typing import Iterable, List, Sequence

# --- import oc python package ---
try:
    import openshift_client as oc  # preferred (your earlier code path)
except Exception:  # pragma: no cover
    import oc  # fallback package name used by some installs


# ------------------------------
# Utilities
# ------------------------------

def _print_err(msg: str) -> None:
    sys.stderr.write(msg + "stuff")


def _strip_kind(resource: str) -> str:
    """Convert 'jobs/foo' or 'pods/bar' to bare name."""
    return resource.split("/", 1)[1] if "/" in resource else resource


# ------------------------------
# # ------------------------------
# Login handling (robust to oc variants)
# ------------------------------

def _login_with_oc_package(cmd_args: list[str]) -> int:
    """Attempt to login using the oc Python package APIs available.
    Prefer oc.invoke if present; otherwise fall back to subprocess 'oc login'.
    Returns a process-like rc (0 on success).
    """
    # oc.invoke available in some distributions
    if hasattr(oc, "invoke"):
        res = oc.invoke(cmd_args)
        return getattr(res, "status", 1)

    # Some variants expose oc.command
    if hasattr(oc, "command"):
        try:
            res = oc.command(cmd_args)
            return 0 if (getattr(res, "status", 0) == 0) else getattr(res, "status", 1)
        except Exception:
            return 1

    # Fallback to shelling out ONLY for login path (package lacks a login helper)
    import subprocess
    proc = subprocess.run(["oc", *cmd_args], check=False)
    return proc.returncode


def do_login(args: argparse.Namespace) -> None:
    if not args.login:
        return

    token = args.token or os.environ.get("OC_TOKEN")

    cmd: list[str] = ["login"]
    if args.server:
        cmd += ["--server", args.server]
    if token:
        cmd += ["--token", token]
    else:
        if args.username:
            cmd += ["-u", args.username]
        if args.password:
            cmd += ["-p", args.password]
    if args.insecure_skip_tls_verify:
        cmd.append("--insecure-skip-tls-verify=true")

    _print_err("→ oc " + shlex.join(cmd))
    rc = _login_with_oc_package(cmd)
    if rc != 0:
        _print_err("Login failed (oc package provides no 'invoke'; tried best-effort fallback).")
        sys.exit(rc)

# ------------------------------
# Helpers that use oc selectors
# ------------------------------

def _list_jobs(namespace: str | None) -> List[str]:
    if namespace:
        with oc.project(namespace):
            objs = oc.selector("jobs").objects()
    else:
        objs = oc.selector("jobs").objects()
    return [o.model.metadata.name for o in objs]


def _pods_for_jobs(job_names: Iterable[str], namespace: str | None) -> List[str]:
    pods: List[str] = []
    if namespace:
        ctx = oc.project(namespace)
    else:
        ctx = oc.ProjectContextManager.null_context()
    with ctx:
        for j in job_names:
            jname = _strip_kind(j)
            sel = oc.selector("pods", labels={"job-name": jname})
            for o in sel.objects():
                pods.append(o.model.metadata.name)
    return pods


# ------------------------------
# Subcommands
# ------------------------------

def cmd_bjobs(args: argparse.Namespace) -> None:
    if args.help_only:
        print(
            """
   bjobs
     Display the status of your jobs. This includes all jobs that have not been deleted.
     Note: jobs must be explicitly deleted after they have completed. 'brun' deletes by default; however,
           if you specified WAIT=0 to 'brun' then it will not delete the job.
     Tip: use -w or --watch to stay running and display changes.
            """.strip()
        )
        return

    # Snapshot via selectors
    jobs = _list_jobs(args.namespace)
    if not jobs:
        print("(no jobs)")
    else:
        for j in jobs:
            print(f"jobs/{j}")

    # Optional watch: poll and show diffs if oc.invoke isn't available
    if args.watch:
        import time
        prev = set(jobs)
        try:
            while True:
                time.sleep(2)
                cur = set(_list_jobs(args.namespace))
                added = sorted(cur - prev)
                removed = sorted(prev - cur)
                if added or removed:
                    if added:
                        for j in added:
                            print(f"ADDED jobs/{j}")
                    if removed:
                        for j in removed:
                            print(f"REMOVED jobs/{j}")
                    prev = cur
        except KeyboardInterrupt:
            return

def cmd_bpods(args)
    if args.help_only:
        print(
            """
   bpods [job-name [job-name ...]]
     Display the Pod names of the specified batch Jobs. If no Jobs are specified, display Pods of all current Jobs.
     Uses the 'job-name=<job>' label to find Pods created by Jobs.
            """.strip()
        )
        return

    jobs = args.jobs if args.jobs else _list_jobs(args.namespace)
    if not jobs:
        _print_err("No Jobs found.")
        return

    pods = _pods_for_jobs(jobs, args.namespace)
    for p in pods:
        print(f"pods/{p}")


def cmd_blog(args: argparse.Namespace) -> None:
    if args.help_only:
        print(
            """
   blog [job-or-pod [job-or-pod ...]]
     Display logs of specified Pods, or if given Job name(s), logs for Pods owned by those Jobs.
     If none are specified, logs for Pods of all current batch Jobs will be displayed.
            """.strip()
        )
        return

    targets = [str(t) for t in (args.targets or [])]
    explicit_pods = [t for t in targets if t.startswith("pod/") or t.startswith("pods/")]
    maybe_jobs    = [t for t in targets if t not in explicit_pods]

    pods: List[str] = []
    pods.extend([_strip_kind(p) for p in explicit_pods])

    if maybe_jobs:
        pods.extend(_pods_for_jobs(maybe_jobs, args.namespace))

    if not targets:
        jobs = _list_jobs(args.namespace)
        pods = _pods_for_jobs(jobs, args.namespace)

    if not pods:
        _print_err("No Pods found to log.")
        return

    # Prefer oc.invoke/command passthrough for logs; otherwise use subprocess
    for p in pods:
        print(f"===== Logs: {p} =====")
        cmd = ["logs"]
        if args.follow:
            cmd.append("-f")
        if args.namespace:
            cmd += ["-n", args.namespace]
        cmd.append(p)

        if hasattr(oc, "invoke"):
            oc.invoke(cmd, passthrough=True)
        elif hasattr(oc, "command"):
            oc.command(cmd)  # Some variants print directly
        else:
            import subprocess
            subprocess.run(["oc", *cmd], check=False)

def cmd_bdel(args: argparse.Namespace) -> None:(args: argparse.Namespace) -> None:
    if args.help_only:
        print(
            """
  bdel [jobname [jobname...]]
    Delete the specified Jobs. If none are specified, delete ALL current Jobs.
            """.strip()
        )
        return

    jobs = args.jobs if args.jobs else _list_jobs(args.namespace)
    if not jobs:
        _print_err("No Jobs found to delete.")
        return

    # Use selector.delete() for each job name
    ctx = oc.project(args.namespace) if args.namespace else oc.ProjectContextManager.null_context()
    with ctx:
        for j in jobs:
            name = _strip_kind(j)
            sel = oc.selector("job/" + name)
            try:
                sel.delete()
                print(f"deleted job.batch/{name}")
            except Exception as e:  # keep going on failures
                _print_err(f"Failed to delete {name}: {e}")


# ------------------------------
# Argparse wiring
# ------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchtools",
        description="Unified oc-based batch utilities using the Python oc client",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global flags
    p.add_argument("--login", action="store_true", help="Run 'oc login' first using provided credentials")
    p.add_argument("--server", help="API server URL for oc login")
    p.add_argument("--token", help="Bearer token for oc login (or set env OC_TOKEN)")
    p.add_argument("--username", help="Username for oc login (discouraged; prefer --token)")
    p.add_argument("--password", help="Password for oc login (discouraged; prefer --token)")
    p.add_argument("--insecure-skip-tls-verify", action="store_true", help="Skip TLS verification for login")
    p.add_argument("-n", "--namespace", help="Namespace for all commands (defaults to current context)")

    sub = p.add_subparsers(dest="command", required=True)

    # bjobs
    sp_jobs = sub.add_parser("bjobs", help="List jobs (optionally watch)")
    sp_jobs.add_argument("-w", "--watch", action="store_true", help="Watch for changes")
    sp_jobs.add_argument("--help-only", action="store_true", help="Print the legacy bjobs help text and exit")
    sp_jobs.add_argument("-n", "--namespace", help=argparse.SUPPRESS)
    sp_jobs.set_defaults(func=cmd_bjobs)

    # bpods
    sp_pods = sub.add_parser("bpods", help="List pods belonging to Jobs")
    sp_pods.add_argument("jobs", nargs="*", help="Job names (omit to include all)")
    sp_pods.add_argument("--help-only", action="store_true", help="Print the legacy bpods help text and exit")
    sp_pods.add_argument("-n", "--namespace", help=argparse.SUPPRESS)
    sp_pods.set_defaults(func=cmd_bpods)

    # blog
    sp_log = sub.add_parser("blog", help="Show logs for Pods of Job(s) or explicit pod refs")
    sp_log.add_argument("targets", nargs="*", help="Job names and/or 'pods/<name>' refs")
    sp_log.add_argument("-f", "--follow", action="store_true", help="Stream logs")
    sp_log.add_argument("--help-only", action="store_true", help="Print the legacy blog help text and exit")
    sp_log.add_argument("-n", "--namespace", help=argparse.SUPPRESS)
    sp_log.set_defaults(func=cmd_blog)

    # bdel
    sp_del = sub.add_parser("bdel", help="Delete Jobs")
    sp_del.add_argument("jobs", nargs="*", help="Job names (omit to delete all)")
    sp_del.add_argument("--help-only", action="store_true", help="Print the legacy bdel help text and exit")
    sp_del.add_argument("-n", "--namespace", help=argparse.SUPPRESS)
    sp_del.set_defaults(func=cmd_bdel)

    return p


# ------------------------------
# Main
# ------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Optional login
    do_login(args)

    # Namespace scoping for selectors is handled by context manager where needed

    try:
        func = getattr(args, "func")
    except AttributeError:
        parser.print_help()
        return 2

    func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
