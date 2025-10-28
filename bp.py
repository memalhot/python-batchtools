from imports import *

def print_pods_for(job_name: str):
    pods = oc.selector("pods", labels={"job-name": job_name}).objects()
    if not pods:
        print(f"No pods found for job {job_name}.")
        return
    print(f"\nPods for {job_name}:\n{'-' * 40}")
    for pod in pods:
        print(f"- {pod.model.metadata.name}")


def bp(job_names: list[str] | None = None) -> int:
    try:
        jobs = oc.selector("jobs").objects()
        if not jobs:
            print("No jobs found.")
            return 0

        job_dict = {job.model.metadata.name: job for job in jobs}

        if job_names:
            for name in job_names:
                if name not in job_dict:
                    print(f"{name} does not exist; cannot fetch pod name.")
                    continue
                print_pods_for(name)
        else:
            print("Displaying pods for all current batch jobs:\n")
            for name in job_dict.keys():
                print_pods_for(name)

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving pods:")
        print(e)
        traceback.print_exc()
        return 1

    return 0