import argparse
import sys
import subprocess
import json


def bj(args):
    """ display the status of jobs """
    if args == "bj -w" or args == "bj --watch":
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])

def bd(args): 
    print("bd called", args)

    # CHECK IF ARGS PROVIDES A WORKLOAD TO DELETE

    # ELSE
    # add error catching
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

    # ELSE
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

    # ELSE
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
    """ Gets status of the queue and tallies the admitted, pending, reserved, and total GPUS for user visibility """
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
import argparse
import sys
import subprocess
import json


def bj(args):
    """ display the status of jobs """
    if args == "-w" or args == " --watch ":
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])

def bd(args): 
    print("bd called", args)

    # CHECK IF ARGS PROVIDES A WORKLOAD TO DELETE

    # ELSE
    # add error catching
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

    # ELSE
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

    # ELSE
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
    """ Gets status of the queue and tallies the admitted, pending, reserved, and total GPUS for user visibility """
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
    print("br called", args)
    

def main():
    valid_args = {"bd", "bj", "bl", "bp", "bs", "bq", "bw", "br", "bwk"}

    parser = argparse.ArgumentParser(description="Command-line tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    for cmd in valid_args:
        sub = subparsers.add_parser(cmd, help=f"Run {cmd}")
    if cmd == "bj":
            sub.add_argument(
                "-w", "--watch",
                action="store_true",
                help="bjobs \n Display the status of your jobs.  This include all jobs that have not been deleted. Note: jobs must be explicitly deleted after they have completed.  'brun' deletes by default.  However, if you specified WAIT=0 to 'brun' then it will not delete the job. Set WATCH=1 to have bjobs stay running and display changes in your jobs. See 'brun -h' and repository README.md for more documentation and examples."
            )
            sub.set_defaults(func=bj)
    else:
            sub.set_defaults(func=globals().get(cmd))

    args = parser.parse_args()

    # Lookup the function by name and call it
    func = globals().get(args.command)
    if func:
        sys.exit(func(args))
    else:
        print(f"Unknown command {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()

def br(args): 
    print("br called", args)
    

def main():
    valid_args = {"bd", "bj", "bl", "bp", "bs", "bq", "bw", "br", "bwk", "-w", "--watch"}

    parser = argparse.ArgumentParser(description="Command-line tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    for cmd in valid_args:
        sub = subparsers.add_parser(cmd, help=f"Run {cmd}")
    if cmd == "bj":
            sub.add_argument(
                "-w", "--watch",
                action="store_true",
                help="bjobs \n Display the status of your jobs.  This include all jobs that have not been deleted. Note: jobs must be explicitly deleted after they have completed.  'brun' deletes by default.  However, if you specified WAIT=0 to 'brun' then it will not delete the job. Set WATCH=1 to have bjobs stay running and display changes in your jobs. See 'brun -h' and repository README.md for more documentation and examples."
            )
            sub.set_defaults(func=bj)
    else:
            sub.set_defaults(func=globals().get(cmd))

    args = parser.parse_args()

    # Lookup the function by name and call it
    func = globals().get(args.command)
    if func:
        sys.exit(func(args))
    else:
        print(f"Unknown command {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
