from helpers import *
from imports import *
from build_yaml import build_job_body
from file_setup import prepare_context

# https://piazza.com/class/me4rjds6oce507/post/23

# change pid -> make temp

def get_pod_status(pod_name: str, namespace: str | None = None) -> str:
    """
    Return the current status.phase of a pod (Pending, Running, Succeeded, Failed).
    """
    pod = oc.selector(f"pod/{pod_name}").object()
    return pod.model.status.phase or "Unknown"

def log_job_output(job_name: str, *, wait: int, timeout: int | None) -> None:
    """
    Wait until the job's pod completes (Succeeded/Failed), then print its logs once.
    """
    pods = oc.selector("pod", labels={"job-name": job_name}).objects()
    if not pods:
        print(f"No pods found for job {job_name}")
        return

    pod = pods[0]
    pod_name = pod.model.metadata.name

    if wait:
        start = time.monotonic()
        while True:
            phase = get_pod_status(pod_name)
            if phase in ("Succeeded", "Failed"):
                print(f"Pod, {pod_name} finished with phase={phase}")
                break
            if timeout and (time.monotonic() - start) > timeout:
                print(f"Timeout waiting for pod {pod_name} to complete")
                return
    print(pretty_print(pod_name))



def br(args) -> int:
    DEFAULT_QUEUES = {
        "v100": "v100-localqueue",
        "a100": "a100-localqueue",
        "h100": "h100-localqueue",
        "none": "dummy-localqueue",
    }

    gpu = args.gpu
    name = args.name
    image = args.image
    job_id = int(args.job_id)
    context = int(args.context)
    max_sec = int(args.max_sec)
    gpu_req = int(args.gpu_numreq)
    gpu_lim = int(args.gpu_numlim)
    wait = int(args.wait)
    timeout = int(args.timeout)
    delete = int(args.job_delete)

    if gpu not in DEFAULT_QUEUES:
        print(f"ERROR: unsupported GPU {gpu} : no queue found")
        return 1
    queue_name = DEFAULT_QUEUES[gpu]


    job_name = f"{name}-{gpu}-{job_id}"
    container_name = f"{job_name}-container"
    file_to_execute = " ".join(args.command).strip()

    pwd = get_cmd("pwd")
    context_directory=f"{pwd}"
    jobs_directory=f"{pwd}/jobs"

    output_directory=f"{jobs_directory}/{job_name}"
    dev_pod_name = get_cmd("hostname")
    getlist=f"{output_directory}/getlist"

    pod = oc.selector(f"pod/{dev_pod_name}").object()
    container = getattr(pod.model.spec, "containers", []) or []
    dev_container_name = container[0].name

    prepare_context(
        context=context,
        context_dir=context_directory,
        jobs_dir=jobs_directory,
        output_dir=output_directory,
        getlist_path=getlist
    )

    try:
        # Create job body using the helper
        job_body = build_job_body(
            job_name=job_name,
            queue_name=queue_name,
            image=image,
            container_name=container_name,
            cmdline=file_to_execute,
            max_sec=max_sec,
            gpu=gpu,
            gpu_req=gpu_req,
            gpu_lim=gpu_lim,
            context=context,
            devpod_name=dev_pod_name,
            devcontainer=dev_container_name,
            context_dir=context_directory,
            jobs_dir=jobs_directory,
            job_workspace=output_directory,
            getlist_path=getlist,
        )

        print(f"Creating job {job_name} in {queue_name}...")
        job = oc.create(job_body)
        print(f"Job: {job_name} created successfully.")
        if wait:
            log_job_output(
                job_name=job_name,
                wait=wait,
                timeout=timeout
            )

    except OpenShiftPythonException as e:
        print("Error occurred while creating job:")
        print(e)
        traceback.print_exc()
        return 1

    #MCHECK: might get conflicting logic here
    # if a user waits to complete a job and sets delete (which is standard) the job will delete
    if delete and wait:
        oc_delete(job_name)
        print(f"RUNDIR: jobs/{job_name}")
    else:
        print(f"User specified not to wait, or not to delete, so {job_name} must be deleted by user.")
        print(f"You can do this by running:")
        print(f"bd {job_name} OR ")
        print(f"oc delete job {job_name}")
    return 0