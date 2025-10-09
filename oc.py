import sys
import subprocess
import json
import openshift_client as oc


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

    # Validate arguments
    valid = {"-h", "--help", "-w", "--watch"}
    help_string(args, help_bj, valid)

    watch_flag = any(a in ("-w", "--watch") for a in args)

    # Open a project context
    with oc.api_client.ApiClient() as api:
        batch = oc.client.BatchV1Api(api)

        if watch_flag:
            print("Getting jobs with -w flag set (Ctrl+C to stop)...")
            stream = oc.watch.Watch().stream(batch.list_job_for_all_namespaces)
            for event in stream:
                obj = event["object"]
                etype = event["type"]
                ns = obj.metadata.namespace
                name = obj.metadata.name
                status = obj.status
                print(f"{etype}: {ns}/{name} | active={status.active or 0} | succeeded={status.succeeded or 0}")
        else:
            print("Getting jobs...")
            jobs = batch.list_job_for_all_namespaces()
            for job in jobs.items:
                ns = job.metadata.namespace
                name = job.metadata.name
                status = job.status
                print(f"{ns}/{name} | active={status.active or 0} | succeeded={status.succeeded or 0}")
