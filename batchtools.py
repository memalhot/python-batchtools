import sys
import subprocess
import json


### error catching needed for functions~~
### ADD PYTHON START TO USAGE

def help_string(args, help_string, valid):
    """ function to print help strings when needed """
    # add something to check that supplied flags are not incorrect

    if "-h" in sys.argv[2:] or "--help" in sys.argv[2:]:
        print(help_string)
        sys.exit(0)


def bj(args):
    help_bjobs = """\
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

    # check for invalid args
    valid = {"-h", "--help", "-w", "--watch"}
    help_string(args, help_bjobs, valid)

    # MAYBE NEEDS MORE INFO FOR USER !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if "-w" in sys.argv[2:] or "--watch" in sys.argv[2:]:
        print("Getting jobs with -w flag set")
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])

def bwk(args): 
    """ gets specified gpu jobs or gets all gpu jobs """


# oc get workloads -o name
# Error from server (Forbidden): workloads.kueue.x-k8s.io is forbidden: User "system:serviceaccount:bu-cs599-pmpp-cuda-51774f:csw-dev" cannot list resource "workloads" in API group "kueue.x-k8s.io" in the namespace "bu-cs599-pmpp-cuda-51774f"

# do we expect user to delete workloads or jobs?

def bd(args): 

    help_bd="""\
        bd
        Usage:
            bd [-h | --help] [jobname [jobname...]]

                Delete the specified jobs. If none are specified, then all current jobs
                are deleted ;-).

                See also:
                See repository README.md for more documentation and examples.
    """
    
    # check for invalid arguments
    valid = {"-h", "--help"}
    help_string(args, help_bd, valid)

    wk = subprocess.run(["oc", "get", "workloads", "-o", "name"], capture_output=True, text=True, check=True)

    workloads = wk.stdout.strip().splitlines()

    # only get workloads pertaining to gpu jobs
    workloads = [w for w in workloads if w.startswith("job-job") or w.startswith("workloads/job-job")]

    if not workloads:
        print ("No GPU worloads found to delete")
        return 

    # if there are workloads provided, delete those
    # if not, delete every workload
    if args:
        for i in range(2, len(sys.argv)):
            if sys.argv[i] not in workloads:
                print(sys.arv[i], "is not a job and cannot be deleted")
            else:
                subprocess.run(["oc", "delete", sys.argv[i]])
    else:
        for w in workloads:
            print(w)
            name = w if "/" in w else f"workloads/{w}"
            subprocess.run(["oc", "delete", name])


def bl(args):
    help_bl="""\
        bl
        Usage:
            bl [-h | --help] [pod-name [pod-name ...]]

                Display logs of specified pods. If none are specified then logs for all
                pods of all current batch jobs will be display.

                See also:
                See repository README.md for more documentation and examples.
    """

    valid = {"-h", "--help"}
    help_string(args, help_bl, valid)

    ret = subprocess.run(['oc', 'get', 'pods', '-o', 'name'], capture_output=True, text=True, check=True)

    # stdout returns string, save as array
    pods=ret.stdout.strip().splitlines()

    if not pods:
        print("No pods to retrieve logs from")
        return

    # if there are pods provided by the user to get logs of, print logs
    # if not, print logs for every pod
    if args:
        for i in range(2, len(sys.argv)):
            if sys.argv[i] not in pods:
                print(sys.argv[i], "is not a pod, logs cannot be retrieved")
            else:
                result = subprocess.run(["oc", "logs", sys.argv[i]], capture_output=True, text=True, check=True)
                print(f"Logs for {sys.argv[i]}:\n{result.stdout}")
    else:
        for p in pods:
            result = subprocess.run(["oc", "logs", p], capture_output=True, text=True, check=True)
            print(f"Logs for {p}:\n{result.stdout}")


def bp(args):
    help_bp="""\
        bp
        Usage:
            bp [-h | --help] [job-name [job-name ...]]

            Display the pod names of the specified batch jobs. If no jobs are
            specified then the pods of all current batch jobs will
            be displayed.

            See also:
            See repository README.md for more documentation and examples.
        """

    valid = {"-h", "--help"}
    help_string(args, help_bp, valid)

    ret = subprocess.run(["oc", "get", "jobs", "-o", "name"], capture_output=True, text=True, check=True)
    jobs = ret.stdout.strip().split
    print(jobs)

    if not jobs:
        print("No jobs to display pod names of.")

    if args:
        for i in range(2, len(sys.argv[i])):
            if argv[i] not in jobs:
                print(sys.argv[i], "does not exist, cannot fetch pod name")
            else:
                subprocess.run(["oc", "get", "jobs", "-l", sys.argv[i], "-o", "name"])
    else:
        for j in jobs:
            subprocess.run(["oc", "get", "jobs", "-l", j, "-o", "name"])


def bq(args):
    help_bq="""\
            Usage:
                bq [-h | --help ]

                Display the status of the GPU queues for the cluster.

                This command shows the number of admitted (active), pending, and reserved jobs 
                on each queue. It also displays how many GPUs service each queue and the 
                queuing strategy being used.

                See also:
                See the repository README.md for more documentation and examples.
        """

    # check for invalid arguments
    valid = {"-h", "--help"}
    help_string(args, help_bq, valid)

    try:
        result = subprocess.run(["oc", "get", "clusterqueue", "-o", "json"], check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running oc: {e.stderr or e}\n")
        sys.exit(e.returncode)
    except json.JSONDecodeError:
        sys.stderr.write("Failed to parse oc output as JSON.\n")
        sys.exit(1)

    # iterate through clusterqueues and compute totals
    for item in data.get("items", []):
        meta = item.get("metadata", {})
        spec = item.get("spec", {})
        status = item.get("status", {})

        # add up to get total GPU quota across all resourceGroups
        total_gpu = 0
        for rg in spec.get("resourceGroups", []):
            for flav in rg.get("flavors", []):
                for res in flav.get("resources", []):
                    if res.get("name") == "nvidia.com/gpu":
                        try:
                            total_gpu += int(res.get("nominalQuota", 0))
                        except (TypeError, ValueError):
                            continue

        # print zero if none
        admitted = status.get("admittedWorkloads", 0)
        pending = status.get("pendingWorkloads", 0)
        reserving = status.get("reservingWorkloads", 0)
        queueing = spec.get("queueingStrategy", "")

        print(
            f"{meta.get('name','')} \t"
            f"admitted: {admitted} "
            f"pending: {pending} "
            f"reserved: {reserving} "
            f"GPUS:{total_gpu} "
            f"{queueing}"
        )

def bps(args):
    print("bps called", args)

def bw(args): 
    print("bw called", args)

def br(args):
    print("br called")


# CLEANUP
def main():
    commands = {
        "bj": bj,
        "bjobs": bj,
        "bd": bd,
        "bdel": bd,
        "bl": bl,
        "blogs": bl,
        "bp": bp,
        "bpods": bp,
        "bs": bps,
        "bps": bps,
        "bq": bq,
        "bqstat":bq,
        "bw": bw,
        "bwait":bw,
        "br": br,
        "brun":br,
        "bwk": bwk,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python3 batchtools.py <command> [options]")
        sys.exit(1)

    cmd = sys.argv[1]
    func = commands[cmd]

    func(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())