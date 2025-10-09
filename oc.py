import sys
import subprocess
import json
import openshift_client as oc

#https://github.com/openshift/openshift-client-python

def help_string(args, help_string, valid):
    """ function to print help strings when needed """
    # add something to check that supplied flags are not incorrect
    if "-h" in sys.argv[2:] or "--help" in sys.argv[2:]:
        print(help_string)
        sys.exit(0)

#!/usr/bin/env python3
import sys
import openshift_client as oc

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

    valid = {"-h", "--help", "-w", "--watch"}
    help_string(args, help_bj, valid)

    watch_flag = any(a in ("-w", "--watch") for a in args)

    # Open a client context; this automatically loads your current kubeconfig
    with oc.client() as client:
        if watch_flag:
            print("Getting jobs with -w flag set (Ctrl+C to stop)...")
            for event in client.watch("jobs"):
                etype = event["type"]
                obj = event["object"]
                name = obj.metadata.name
                ns = obj.metadata.namespace
                status = obj.status
                print(f"{etype}: {ns}/{name} | active={status.get('active', 0)} | succeeded={status.get('succeeded', 0)}")
        else:
            print("Getting jobs...")
            jobs = client.get("jobs")
            for job in jobs.items:
                name = job.metadata.name
                ns = job.metadata.namespace
                status = job.status
                active = getattr(status, "active", 0) or 0
                succeeded = getattr(status, "succeeded", 0) or 0
                failed = getattr(status, "failed", 0) or 0
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