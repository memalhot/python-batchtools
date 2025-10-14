import openshift_client as oc
from openshift_client import Context, OpenShiftPythonException
import traceback
import argparse
import sys

def cli_login(kubeconfig: str, server: str, token: str, timeout_seconds: int = 60 * 30) -> int:
    """
    Log into an OpenShift cluster using openshift_client's Context.
    If login fails, only print the 'err' message from the JSON.
    """
    my_context = Context()
    my_context.kubeconfig_path = kubeconfig
    my_context.api_server = server
    my_context.token = token

    with oc.timeout(60 * 30), oc.tracking() as t, my_context:
        if oc.get_config_context() is None:
            print(f'Current context not set! Logging into API server: {my_context.api_server}\n')
            try:
                oc.invoke('login')
            except OpenShiftPythonException:
                print('error occurred logging into API Server')
                traceback.print_exc()
                print(f'Tracking:\n{t.get_result().as_json(redact_streams=False)}\n\n')
                exit(1)

        print(f'Current context: {oc.get_config_context()}')


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