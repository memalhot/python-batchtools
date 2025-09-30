import sys
import subprocess

def bd():
    """delete workloads, if none passed, delete every GPU job"""
    workloads=sys.argv[2:]

    if workloads == "-h":
        print("bdel [jobname [jobname...]] \n"
        "Delete the specified jobs, if none are specified then all current jobs are deleted ;-) \n"
        "See repository README.md for more documentation and examples.")
        return 0

    if not workloads:
        ret = subprocess.run(["oc", "get", "workloads", "-o", "name"])
        if ret.returncode != 0:
            sys.stderr.write(ret.stderr)
            sys.exit(ret.returncode)
        workloads = [w for w in workloads if w.startswith("job-job") or w.startswith("workloads/job-job")]
        print(workloads)

    if not workloads:
        print ("No GPU worloads found to delete")
        return  

    exit_code = 0
    for w in workloads:
        print(w)
        name = w if "/" in w else f"workloads/{w}"
        ret = run(["oc", "delete", name])
        if ret.stderr:
            sys.stderr.write(ret.stderr)
        if ret.returncode != 0:
            exit_code = ret.returncode

    sys.exit(exit_code)

def bj():
    WATCH=sys.argv[3:]

    if WATCH == "-h":
        print("bjobs \n Display the status of your jobs. \n"
        "This include all jobs that have not been deleted. Note: jobs must be explicitly deleted after they have completed.  'brun' deletes by default.  However, if you specified WAIT=0 to 'brun' then it will not delete the job.Set WATCH=1 to have bjobs stay running and display changes in your jobs. \n See 'brun -h' and repository README.md for more documentation and examples.")
        return 0

    if WATCH:
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])

def bl():
    pods = sys.argv[3:]
    if pods == "-h":
        print("blog [pod-name [pod-name ...]]\n Display logs of specified pods.\n If none specified then logs for all pods of all current batch jobs will be display. \n See repository README.md for more documentation and examples.")
        return 0

    # if no pods provided fetch pods
    if not pods:
        ret = subprocess.run(["oc", "get", "pods"])
        if ret.returncode != 0:
            sys.stderr.write(ret)
            sys.exit(ret.returncode)
        pods = ret.stdout.strip().split
        print(pods)

    if not pods:
        print("No pods found to display logs for.")
        return 0
    
    for p in pods:
        ret = subprocess.run(["oc", "logs", p])
        if ret.stdout:
            sys.stdout.write(ret.stdout)
        if ret.stderr:
            sys.stderr.write(ret.stderr)

def bp():
    print("bp called")

def bs():
    print("bs called")

def bq():
    print("bq called")

def bw():
    print("bw called")

def br():
    print("bw called")


def main():
    valid_args = {"bd", "bj", "bl", "bp", "bs", "bq", "bw, br"}

    # Skip the program name arg
    args = sys.argv[1:3]

    if not args:
        # CHANGE ME
        print("Usage: python script.py <bd|bj|bl|bp|bs|bq|bw>")
        sys.exit(1)

    for arg in args:
        if arg in valid_args:
                globals()[arg]() 
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
