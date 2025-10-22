from helpers import *
from imports import *
from build_yaml import build_job_body

def get_pod_status(pod_name: str, namespace: str | None = None) -> str:
    """
    Return the current status.phase of a pod (e.g. Pending, Running, Succeeded, Failed).
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
                print(f"Pod {pod_name} finished with phase={phase}")
                break
            if timeout and (time.monotonic() - start) > timeout:
                print(f"Timeout waiting for pod {pod_name} to complete")
                return
            time.sleep(5)

    print(pretty_print(pod_name))

def prepare_context_and_getlist(context: int, context_dir: str, jobs_dir: str, output_dir: str, getlist_path: str) -> None:    
    if not context:
        return
        
    ctx = Path(context_dir).resolve()
    out = Path(output_dir).resolve()
    gl  = Path(getlist_path).resolve()
    jobs = Path(jobs_dir).resolve()

    if not ctx.is_dir():
        print(f"ERROR: CONTEXT_DIR: {ctx} is not a directory")
        sys.exit(-1)

    if out.exists():
        print(f"ERROR: {out} directory already exists")
        sys.exit(-1)
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("ERROR: Failed to make output dir (already exists)")
        sys.exit(-1)
    except Exception as e:
        print(f"ERROR: Failed to make output dir: {e}")
        sys.exit(-1)

    jdir_rel: str | None = None
    # Is jobs_dir directly under context_dir?
    if jobs.parent.resolve() == ctx:
        jdir_rel = f"./{jobs.name}"
    else:
        jdir_rel = None

    entries: list[str] = []
    for name in sorted(p.name for p in ctx.iterdir()):
        # immediate children only (like -mindepth 1 -maxdepth 1)
        # "find" would include both files and directories; do the same here
        rel = f"./{name}"
        if jdir_rel and rel == jdir_rel:
            continue
        entries.append(rel)

    # Write GETLIST
    try:
        gl.parent.mkdir(parents=True, exist_ok=True)
        gl.write_text("\n".join(entries) + ("\n" if entries else ""))
    except Exception as e:
        print(f"ERROR: Failed to write getlist at {gl}: {e}")
        sys.exit(-1)


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


    prepare_context_and_getlist(
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

        print(f"Creating job {job_name} in queue {queue_name}...")
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

    if delete:
        oc_delete(job_name)

    return 0