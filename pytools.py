import openshift_client as oc
from openshift_client import Context, OpenShiftPythonException
import traceback
import argparse
import sys
from openshift_client import watch

# modeled off of: https://github.com/openshift/openshift-client-python/blob/main/examples/login.py
# login with oc or login with the cli
def cli_login(kubeconfig: str, server: str, token: str, timeout_seconds: int = 60 * 30) -> int:
    """
    Log into an OpenShift cluster using openshift_client's Context.
    If login fails, print the 'err' message from the JSON.
    """
    my_context = Context()
    my_context.kubeconfig_path = kubeconfig
    my_context.api_server = server
    my_context.token = token

    with oc.timeout(60 * 30), oc.tracking() as t, my_context:
        if oc.get_config_context() is None:
            print(f'Current context not set. Attempting to log onro API server: {my_context.api_server}\n')
            try:
                oc.invoke('login')
            except OpenShiftPythonException:
                # login failed, print error message
                tracking_result = t.get_result().as_dict()
                
                action_error = None
                for action in tracking_result.get('actions', []):
                    if action.get('verb') == 'login' and not action.get('success'):
                        action_error = action.get('err', 'An unknown error occurred during login.')
                        break
                
                print('Login failed.')
                if action_error:
                    # Print ONLY the specific 'err' message from the action
                    print(action_error.strip()) 
                
                exit(1)

        print(f'Current context: {oc.get_config_context()}')

def bj(watch: bool) -> int:
    """
    Display the status of gpu jobs using 'oc get jobs'.
    """
    try:
        with oc.tracking() as t:
            if args.watch:
                print("Getting jobs with -w flag set")
                with oc.watch("jobs") as stream:
                    for event in stream:
                        job = event['object']
                        print(f"[{event['type']}] {job.model.metadata.name}")
            else:
                jobs = oc.selector("jobs").objects()
                if not jobs:
                    print("No jobs found.")
                    return
                print(f"Found {len(jobs)} jobs:\n")
                for job in jobs:
                    print(f"- {job.model.metadata.name}")

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving jobs:")
        print(e)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", description="OpenShift CLI helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="Log into an OpenShift cluster")
    p_login.add_argument("-k", "--kubeconfig", required=True, help="oc kubeconfig")
    p_login.add_argument("-s", "--server", required=True, help="API server URL")
    p_login.add_argument("-t", "--token", required=True, help="Login token (e.g., oc whoami -t)")

    p_bj = sub.add_parser("bj", help="Display the status of your jobs ('oc get jobs').")
    # Add -w / --watch flag, store as a boolean (True/False)
    p_bj.add_argument("-w", "--watch", action="store_true", help="Stay running and display changes in your jobs.")

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "login":
        return cli_login(args.kubeconfig, args.server, args.token)

    elif args.cmd == "bj":
        return bj(args.watch)

    # Should never reach here because subparsers are required
    return 2

if __name__ == "__main__":
    sys.exit(main())