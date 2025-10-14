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
                # The exception is caught, and the tracking object 't' contains
                # the details of the failed 'oc login' action.
                tracking_result = t.get_result().as_dict()
                
                # Look for the 'err' message in the failed action
                action_error = None
                for action in tracking_result.get('actions', []):
                    # The 'login' action is the one that failed with the token error
                    if action.get('verb') == 'login' and not action.get('success'):
                        action_error = action.get('err', 'An unknown error occurred during login.')
                        break
                
                print('Login failed.')
                if action_error:
                    # Print ONLY the specific 'err' message from the action
                    print(action_error.strip()) 
                
                # Exit with a non-zero status code to indicate failure
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