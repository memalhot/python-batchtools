from imports import *

def is_logged_in() -> bool:
    try:
        oc.invoke("whoami")
        return True
    except oc.OpenShiftPythonException:
        print("You are not logged in to the oc cli. Retrieve the token using 'oc login --web' or retrieving the login token from the openshift UI.")
        return False

def get_cmd(command:str) -> str:
    """
    Helper function to print the hostname using subprocess.
    """
    try:
        result = subprocess.run(
            [command],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        return output

    except subprocess.CalledProcessError as e:
        print(f"Error: command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"stderr: {e.stderr.strip()}")
        sys.exit(-1)


def pretty_print(pod_name:str) -> Optional[str]:
    try:
        logs = oc.selector(f"pod/{pod_name}").logs()
        # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚
        logs = str(logs).replace("\\n", "\n")
        return logs
    except OpenShiftPythonException as e:
        print("Error occurred while retrieving logs:")
        print(e)

def oc_delete(job_name:str) -> None:
    try:
        print(f"Deleting {job_name}")
        oc.invoke("delete", ["job", job_name])
    except OpenShiftPythonException as e:
        print("Error occurred while retrieving logs:")
        print(e)
