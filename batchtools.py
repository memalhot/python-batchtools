import sys
import subprocess
import json


### error catching needed for functions~~

def bj(args):
    help_bjobs = """\
            bjobs
                Usage:
                    bjobs [-h] [-w | --watch]

                    Display the status of your jobs. This includes all jobs that have not been deleted.

                    Note:
                    Jobs must be explicitly deleted after they have completed.
                    'brun' deletes jobs by default. However, if you specified WAIT=0 to 'brun',
                    then it will not delete the job.

                    Tip:
                    Set -w or --watch to have bjobs stay running and display changes in your jobs.

                    See also:
                    'brun -h' and the repository README.md for more documentation and examples.
            """

    valid = {"-h", "-w", "--watch"}

    # check for invalid arguments
    if any(arg not in valid for arg in args):
        print(help_bjobs)
        sys.exit(1)

    if "-h" in sys.argv[2:] or "--help" in sys.argv[2:]:
        print(help_bjobs)
    
    # MAYBE NEEDS MORE INFO FOR USER !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    elif "-w" in sys.argv[2:] or "--watch" in sys.argv[2:]:
        print("Getting jobs with -w flag set")
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])

def bd(args): 

    # CHECK IF ARGS PROVIDES A WORKLOAD TO DELETE

    # ELSE
    result = subprocess.run(["oc", "get", "workloads", "-o", "name"], capture_output=True, text=True, check=True)
    workloads = result.stdout.strip().splitlines()

    workloads = [w for w in workloads if w.startswith("job-job") or w.startswith("workloads/job-job")]

    if not workloads:
        print ("No GPU worloads found to delete")
        return 
 
    for w in workloads:
        print(w)
        name = w if "/" in w else f"workloads/{w}"
        subprocess.run(["oc", "delete", name])


def bl(args):
    # CHECK IF ARGS PROVIDES PODS
    ret = subprocess.run(["oc", "get", "pods"], capture_output=True, text=True, check=True)
    pods = ret.stdout.strip().split
    print(pods)

    if pods:
        for p in pods:
            result = subprocess.run(["oc", "logs", p], capture_output=True, text=True, check=True)
            print(f"Logs for {p}:\n{result.stdout}")
    else:
        print("No pods to retrieve logs from")



def bp(args):
    # CHECK IF ARGS PROVIDES PODS
    if not pods:
        ret = subprocess.run(["oc", "get", "jobs", "-o", "name"], capture_output=True, text=True, check=True)

        jobs = ret.stdout.strip().split
        print(jobs)
        if jobs:
            job_name="job=name"
            for j in jobs:
                # FIX THIS
                result = subprocess.run(["oc", "get", "pods", "-l", job-name==j, "o", "name"])
        else:
            print("No pods")

def bs(args): 
    bps(args)

def bq(args):
    help_bq="""\
            Usage:
                bq [-h]

                Display the status of the GPU queues for the cluster.

                This command shows the number of admitted (active), pending, and reserved jobs 
                on each queue. It also displays how many GPUs service each queue and the 
                queuing strategy being used.

                See also:
                See the repository README.md for more documentation and examples.
        """

    valid = {"-h"}

    # check for invalid arguments
    if any(arg not in valid for arg in args):
        print(help_bq)
        sys.exit(1)

    if "-h" in sys.argv[2:]:
        print(help_bq)
    else:
        try:
            result = subprocess.run(
                ["oc", "get", "clusterqueue", "-o", "json"],
                check=True,
                capture_output=True,
                text=True,
            )
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


def bwk(args): 
    """ gets specified gpu jobs or gets all gpu jobs """

def bw(args): 
    print("bw called", args)

def br(args):
    print("br called")

def main():
    commands = {
        "bj": bj,
        "bd": bd,
        "bl": bl,
        "bp": bp,
        "bs": bs,
        "bq": bq,
        "bw": bw,
        "br": br,
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