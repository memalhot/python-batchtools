import sys
import subprocess
import openshift_client as oc


def is_logged_in() -> bool:
    try:
        oc.invoke("whoami")
        return True
    except oc.OpenShiftPythonException:
        print(
            "You are not logged in to the oc cli. Retrieve the token using 'oc login --web' or retrieving the login token from the openshift UI."
        )
        return False


def get_cmd(command: str) -> str:
    """
    Helper function to print the hostname using subprocess.
    """
    try:
        return subprocess.check_output([command], text=True).strip()
    except subprocess.CalledProcessError as e:
        sys.exit(
            f"Error: command failed with exit code {e.returncode}{': ' + e.stderr.strip() if e.stderr else ''}"
        )


def pretty_print(pod: oc.APIObject) -> str:
    formatted_logs: str = ""
    try:
        logs: dict[str, str] = pod.logs()
        # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚
        formatted_logs = str(logs).replace("\\n", "\n")
    except oc.OpenShiftPythonException as e:
        print(f"Error occurred while retrieving logs: {e}")

    return formatted_logs


def oc_delete(job_name: str) -> None:
    try:
        print(f"Deleting {job_name}")
        oc.invoke("delete", ["job", job_name])
    except oc.OpenShiftPythonException as e:
        print(f"Error occurred while deleting job: {e}")
