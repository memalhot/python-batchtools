from imports import *

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


def pretty_print(pod_name:str) -> str:
    try:
        logs = oc.selector(f"pod/{pod_name}").logs()
        # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚
        logs = str(logs).replace("\\n", "\n")
        return logs
    except OpenShiftPythonException as e:
        print("Error occurred while retrieving logs:")
        print(e)
        return 1
