import argparse
import sys
import traceback

import openshift_client as oc
from openshift_client import OpenShiftPythonException, Context


def cli_login(kubeconfig: str, server: str, token: str, timeout_seconds: int = 60 * 30) -> int:
    """
    Log into an OpenShift cluster using openshift_client's Context.
   """
    my_context = Context()
    my_context.kubeconfig_path = kubeconfig
    my_context.api_server = server
    my_context.token = token
    
    with oc.timeout(timeout_seconds), oc.tracking() as t, my_context:
        try:
            if oc.get_config_context() is None:
                print(f" Logging into API server: {my_context.api_server}\n")
                oc.invoke("login")
                return 0

        except OpenShiftPythonException as e:
            # Print specific message if the token is invalid or expired
            err_msg = str(e)
            if "Unauthorized" in err_msg or "token" in err_msg.lower():
                print({"err": "error: The token provided is invalid or expired.\n\n"})
            else:
                print({"err": f"error: {err_msg}\n\n"})
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