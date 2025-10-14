import argparse
import sys
import traceback

import openshift_client as oc
from openshift_client import OpenShiftPythonException, Context


def cli_login(server: str, token: str, timeout_seconds: int = 60 * 1440) -> int:
    my_context = Context()
    my_context.kubeconfig_path = "/tmp/kc"
    my_context.api_server = server
    my_context.token = token

    # Make stdout line-buffered so prints appear even if we crash later
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    # Start tracking FIRST so we can read it even if entering my_context fails
    with oc.tracking() as t:
        try:
            with oc.timeout(timeout_seconds), my_context:
                # If already logged in, get_config_context() won't be None
                if oc.get_config_context() is None:
                    print(f"Logging into API server: {my_context.api_server}", flush=True)
                    oc.invoke("login")  # uses server/token from Context

                proj = oc.get_project_name()
                print(f"Current project: {proj}", flush=True)
                return 0

        except OpenShiftPythonException:
            print("Login failed or cluster call failed.", flush=True)
            traceback.print_exc()
            # We have tracking even if failure happened during __enter__
            try:
                print(f"Tracking:\n{t.get_result().as_json(redact_streams=False)}\n", flush=True)
            except Exception:
                pass
            return 1
        except Exception as e:
            print(f"Unexpected error: {e!r}", flush=True)
            try:
                print(f"Tracking:\n{t.get_result().as_json(redact_streams=False)}\n", flush=True)
            except Exception:
                pass
            return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", description="OpenShift CLI helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="Log into an OpenShift cluster")
    p_login.add_argument("-s", "--server", required=True, help="API server URL")
    p_login.add_argument("-t", "--token", required=True, help="Login token (e.g., oc whoami -t)")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "login":
        return cli_login(args.server, args.token)

    # Should never reach here because subparsers are required
    return 2

if __name__ == "__main__":
    sys.exit(main())