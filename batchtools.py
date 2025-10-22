from imports import *
from helpers import is_logged_in
from bj import bj
from bl import bl
from bd import bd
from bq import bq
from bps import bps
from bp import bp
from br import br

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", description="OpenShift CLI helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # B JOBS
    p_bj = sub.add_parser("bj", help="""\
            bj
                Usage:
                    bj [-h | --help]

                    Display the status of your jobs. This includes all jobs that have not been deleted.

                    Note:
                    Jobs must be explicitly deleted after they have completed.
                    'brun' deletes jobs by default. However, if you specified WAIT=0 to 'brun',
                    then it will not delete the job.

                    Tip:
                    Set -w or --watch to have bj stay running and display changes in your jobs.

                    See also:
                    'brun -h' and the repository README.md for more documentation and examples.
        """)

    # B LOGS
    p_bl = sub.add_parser("bl", help=""""\
        bl
            Usage:
                bl [-h | --help] [pod-name [pod-name ...]]

                    Display logs of specified pods. If none are specified then logs for all
                    pods of all current batch jobs will be display.

                    See also:
                    See repository README.md for more documentation and examples.
    """)

    p_bl.add_argument("pod_names", nargs="*", help="Optional pod names to display logs for")


    # B DEL
    p_bd = sub.add_parser("bd", help=""""\
        bd
            Delete specified GPU jobs, or all GPU jobs if none are specified.

            Usage:
                bd [-h | --help] [jobname [jobname...]]

            Description:
                Delete the specified jobs. If no jobs are specified, all current
                GPU-related jobs will be deleted.

            See also:
                See the repository README.md for documentation and examples.
        """)

    p_bd.add_argument("pod_names", nargs="*", help="Optional job names to delete jobs")

    # B PODS
    p_bp = sub.add_parser("bp", help="""\
            bp
            Usage:
                bp [-h | --help] [job-name [job-name ...]]

                Display the pod names of the specified batch jobs. If no jobs are
                specified then the pods of all current batch jobs will
                be displayed.

                See also:
                See repository README.md for more documentation and examples.
        """)

    p_bp.add_argument("job_names", nargs="*", help="Optional jobs to fetch the job name of")

    p_bq = sub.add_parser("bq", help="""\
        bq
            Usage:
                bq [-h | --help]

            Display the status of the GPU queues for the cluster.

            This command shows the number of admitted (active), pending, and reserved jobs 
            on each queue. It also displays how many GPUs service each queue and the 
            queuing strategy being used.

            See also:
            See the repository README.md for more documentation and examples.
    """)

    p_br = sub.add_parser("br", help="""\
            brun [-h] [--gpu GPU] [--image IMAGE] [--name NAME] [--job-id JOB_ID]
            [--job-delete {0,1}] [--wait {0,1}] [--timeout SECONDS]
            [--max-sec SECONDS] [--gpu-numreq NUM] [--gpu-numlim NUM] [-v]
            <command line>

                brun creates and submits a batch job to a GPU batch queue using the OpenShift Python client.
                The arguments are treated as a command line that will execute as the batch job within a container.
                The behaviour of the job submission can be controlled via several environment variables or CLI flags.

                By default, the job runs in an isolated container environment scheduled onto a GPU node using
                the Kueue queue system. GPU type, image, resource limits, and runtime behavior (e.g., waiting or
                automatic deletion) can be customized at submission time.

                Example usages:

                1. Run a simple command on the default GPU type (v100)
                $ brun ./hello
                Hello from CPU
                Hello from GPU
                ...
                RUNDIR: jobs/job-v100-9215

                2. Specify GPU type and image for a training job
                $ br --gpu a100 --image quay.io/user/train:latest python train.py --epochs 5

                3. Submit without waiting for completion
                $ br --wait 0 ./long_running_task.sh

                By default, br waits for the job to complete, streams its logs,
                and then displays the directory where the job outputs were copied.

                Options:
                --gpu              Select GPU type (maps to queue label; default: v100)
                --image            Specify container image to use for the job
                --context          Specify whether script will copy working directory or not (1/0; default: 1)
                --name             Base name for the job (default: job)
                --job-id           Job ID suffix (default: current process ID)
                --job-delete       Delete the job on completion (1/0; default: 1)
                --wait             Wait for job completion (1/0; default: 1)
                --timeout          Maximum time to wait for completion (seconds)
                --max-sec          Maximum execution time allowed inside container
                --gpu-numreq       Number of GPUs requested
                --gpu-numlim       Number of GPUs limited
                -v, --verbose      Increase verbosity of output

                See the repository README.md for more examples and advanced usage.
                """
        )

    DEFAULTS = {
        "gpu": "v100",
        "image": "image-registry.openshift-image-registry.svc:5000/redhat-ods-applications/csw-run-f25:latest",
        "context": 1,
        "name": "job",
        "job_id": os.getpid(),
        "job_delete": 1,
        "wait": 1,
        "timeout": 60 * 15 * 4,
        "max_sec": 60 * 15,
        "gpu_numreq": 1,
        "gpu_numlim": 1,
        "verbose": 0,
        }

    p_br.add_argument("--gpu", default=DEFAULTS["gpu"],
                      choices=["v100", "a100", "h100", "none"],
                      help=f"GPU type (maps to queue label; default: {DEFAULTS['gpu']})")

    p_br.add_argument("--image", default=DEFAULTS["image"],
                      help=f"Container image (default: {DEFAULTS['image']})")
    
    p_br.add_argument("--context", default=DEFAULTS["context"],
                      help=f"Specify whether script will copy working directory or not (default: {DEFAULTS['context']})")

    p_br.add_argument("--name", default=DEFAULTS["name"],
                      help=f"Base job name (default: {DEFAULTS['name']})")

    p_br.add_argument("--job-id", default=DEFAULTS["job_id"],
                      help="Job ID suffix (default: current process ID)")

    p_br.add_argument("--job-delete", type=int, default=DEFAULTS["job_delete"],
                      choices=[0, 1], help="Delete job on finish (1/0; default: 1)")

    p_br.add_argument("--wait", type=int, default=DEFAULTS["wait"],
                      choices=[0, 1], help="Wait for completion (1/0; default: 1)")

    p_br.add_argument("--timeout", type=int, default=DEFAULTS["timeout"],
                      help=f"Wait timeout in seconds (default: {DEFAULTS['timeout']})")

    p_br.add_argument("--max-sec", type=int, default=DEFAULTS["max_sec"],
                      help=f"Maximum execution time (default: {DEFAULTS['max_sec']})")

    p_br.add_argument("--gpu-numreq", type=int, default=DEFAULTS["gpu_numreq"],
                      help=f"Number of GPUs requested (default: {DEFAULTS['gpu_numreq']})")

    p_br.add_argument("--gpu-numlim", type=int, default=DEFAULTS["gpu_numlim"],
                      help=f"Number of GPUs limited (default: {DEFAULTS['gpu_numlim']})")

    p_br.add_argument("-v", "--verbose", action="count", default=DEFAULTS["verbose"],
                      help="Increase verbosity (-v, -vv, etc.)")

    p_br.add_argument("command", nargs=argparse.REMAINDER,
                      help="Command to run inside the container.")


    #BPS
    p_bps = sub.add_parser("bps", help="""\
                bps
                    Usage:
                        bps [-h | --help] [-v | --verbose] [node-name [node-name ...]]

                    List active GPU pods per node. By default prints only BUSY nodes.
                    With -v/--verbose, prints FREE for nodes seen with Running pods but 0 GPUs.
            """)
    p_bps.add_argument("-v", "--verbose", action="store_true", help="Show FREE nodes too")
    p_bps.add_argument("nodes", nargs="*", help="Optional node name(s) to filter")

    return parser

def main(argv=None) -> int:

    if not is_logged_in():
        sys.exit(1)
    
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "bj":
        return bj(args.watch)

    elif args.cmd == "bd":
        return bd(args.pod_names)

    elif args.cmd == "bl":
        return bl(args.pod_names)

    elif args.cmd == "bp":
        return bp(args.job_names)

    elif args.cmd == "bq":
        return bq(args)
    
    elif args.cmd == "br":
        return br(args)
    
    elif args.cmd == "bps":
        # so nodes is iterable in bps
        return bps(getattr(args, "nodes", None), getattr(args, "verbose", False))

    # should never return here
    return 2

if __name__ == "__main__":
    sys.exit(main())