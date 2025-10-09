import sys
import subprocess
import json
from kubernetes import config, watch as k8s_watch
from openshift.dynamic import DynamicClient

#https://github.com/openshift/openshift-client-python

def help_string(args, help_string, valid):
    """ function to print help strings when needed """
    # add something to check that supplied flags are not incorrect
    if "-h" in sys.argv[2:] or "--help" in sys.argv[2:]:
        print(help_string)
        sys.exit(0)

def bj(args):
    help_bj = """\
            bj
                Usage:
                    bj [-h | --help] [-w | --watch]

                    Display the status of your jobs. This includes all jobs that have not been deleted.

                    Note:
                    Jobs must be explicitly deleted after they have completed.
                    'brun' deletes jobs by default. However, if you specified WAIT=0 to 'brun',
                    then it will not delete the job.

                    Tip:
                    Set -w or --watch to have bj stay running and display changes in your jobs.

                    See also:
                    'brun -h' and the repository README.md for more documentation and examples.
            """

    k8s_client = config.new_client_from_config()  # or config.load_incluster_config() in cluster
    dyn = DynamicClient(k8s_client)
    jobs_res = dyn.resources.get(api_version="batch/v1", kind="Job")

    if watch_flag:
        print("Getting jobs with -w flag set (Ctrl+C to stop)...")
        w = k8s_watch.Watch()
        for evt in w.stream(jobs_res.list_for_all_namespaces):
            obj = evt["object"]
            ns = obj.metadata.namespace
            name = obj.metadata.name
            st = getattr(obj, "status", {}) or {}
            active = getattr(st, "active", 0) or 0
            succeeded = getattr(st, "succeeded", 0) or 0
            failed = getattr(st, "failed", 0) or 0
            print(f"{evt['type']}: {ns}/{name}\tactive={active}\tsucceeded={succeeded}\tfailed={failed}")
    else:
        print("Getting jobs...")
        resp = jobs_res.list_for_all_namespaces()
        for job in resp.items:
            ns = job.metadata.namespace
            name = job.metadata.name
            st = getattr(job, "status", {}) or {}
            active = getattr(st, "active", 0) or 0
            succeeded = getattr(st, "succeeded", 0) or 0
            failed = getattr(st, "failed", 0) or 0
            print(f"{ns}/{name}\tactive={active}\tsucceeded={succeeded}\tfailed={failed}")

def main():
    commands = {
        "bj": bj,
        "bjobs": bj,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python3 batchtools.py <command> [options]")
        sys.exit(1)

    cmd = sys.argv[1]
    func = commands[cmd]

    func(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())