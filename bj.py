from imports import *

def bj(watch: bool) -> int:
    """
    Display the status of GPU jobs using 'oc get jobs'.
    """
    try:
        jobs = oc.selector("jobs").objects()
        if not jobs:
            print("No jobs found.")
            return 0

        print(f"Found {len(jobs)} jobs:\n")
        for job in jobs:
            print(f"- {job.model.metadata.name}")

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving jobs:")
        print(e)
        return 1

    return 0