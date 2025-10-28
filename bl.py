from imports import *
from helpers import pretty_print

def bl(pod_names: list[str] | None = None) -> int:
    try:
        pods = oc.selector("pods").objects()

        if not pods:
            print("No pods to retrieve logs from.")
            return 0

        # dict of pod name and pod object
        pod_dict = {pod.model.metadata.name: pod for pod in pods}

        # case where user provides pods
        if pod_names:
            for name in pod_names:
                if name not in pod_dict:
                    print(f"{name} is not a valid pod. Logs cannot be retrieved.")
                    continue
                print(f"\nLogs for {name}:\n{'-' * 40}")
                print(pretty_print(name))
 
        else:
            # case where user provides no args, print logs for all pods
            for name, pod in pod_dict.items():
                print(f"\nLogs for {name}:\n{'-' * 40}")
                pretty_print(name)

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving logs:")
        print(e)
        traceback.print_exc()
        return 1

    return 0
