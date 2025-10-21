from imports import *
from helpers import oc_delete

# MCHECK: NEEDS PERMISSIONS TO BE TESTED
def bd(job_names: list[str] | None = None) -> int:
    try:
        jobs = oc.selector("workloads").objects()
        if not jobs:
            print("No jobs found.")
            return 0

        # only get gpu jobs (ASK ABOUT THIS)
        gpu_jobs = [
            job for job in jobs if job.model.metadata.name.startswith("job-job") 
            or job.model.metadata.name.startswith("workloads/job-job")
        ]

        if not gpu_jobs:
            print("No GPU workloads to delete.")
            return 0

        # case where user provides jobs to delete
        if job_names:
            found = [job.model.metadata.name for job in gpu_jobs]
            for name in job_names:
                if name not in found:
                    print(f"{name} is not a GPU job and cannot be deleted.")
                    continue
                oc_delete(name)
        else:
            # case where user does not provide jobs to delete, delete all
            print("No job names provided -> deleting all GPU workloads:\n")
            for job in gpu_jobs:
                name = job.model.metadata.name
                oc_delete(name)

    except OpenShiftPythonException as e:
        print("Error occurred while deleting jobs:")
        print(e)
        traceback.print_exc()
        return 1

    return 0