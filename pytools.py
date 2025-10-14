import argparse
import sys
import traceback

import openshift_client as oc
from openshift_client import OpenShiftPythonException, Context


import openshift_client as oc
from openshift_client import Context, OpenShiftPythonException
import traceback

def cli_login(kubeconfig: str, server: str, token: str, timeout_seconds: int = 60 * 30) -> int:
    """
    Log into an OpenShift cluster using openshift_client's Context.
    If login fails, only print the 'err' message from the JSON.
    """
    my_context = Context()
    my_context.kubeconfig_path = kubeconfig
    my_context.api_server = server
    my_context.token = token

    with oc.tracking() as t:
        try:
            with oc.timeout(timeout_seconds), my_context:
                if oc.get_config_context() is None:
                    oc.invoke("login")

                proj = oc.get_project_name()
                print(f"Successfully logged in. Current project: {proj}")
                return 0

        except OpenShiftPythonException:
            # Extract the 'err' value from the tracking JSON and print it
            try:
                tracking_json = t.get_result().as_json(redact_streams=False)
                actions = tracking_json.get("actions", [])
                if actions:
                    # Find first action with a non-empty 'err'
                    for action in actions:
                        err = action.get("err")
                        if err:
                            print(err.strip())
                            break
                    else:
                        print("Login failed: no error message in tracking JSON.")
                else:
                    print("Login failed: tracking data missing.")
            except:
                print("Login failed and tracking data unavailable.")
                traceback.print_exc()
                return 1

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", description="OpenShift CLI helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="Log into an OpenShift cluster")
    p_login.add_argument("-k", "--kubeconfig", required=True, help="oc kubeconfig")
    p_login.add_argument("-s", "--server", required=True, help="API server URL")
    p_login.add_argument("-t", "--token", required=True, help="Login token (e.g., oc whoami -t)")
    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "login":
        return cli_login(args.kubeconfig, args.server, args.token)

    # Should never reach here because subparsers are required
    return 2

if __name__ == "__main__":
    sys.exit(main())