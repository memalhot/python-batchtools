import argparse
import sys
import subprocess
import json
import getopt


def bj(args):
    """ display status of jobs """

    try:
        opts, _ = getopt.getopt(args, "w", ["watch"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    watch = False
    for opt, _ in opts:
        if opt in ("-w", "--watch"):
            watch = True

    if watch:
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