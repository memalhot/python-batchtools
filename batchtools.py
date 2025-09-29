import sys
import subprocess


def run(command):
    return subprocess.run(command, check=False, text=True, capture_output=True)

def bd():
    """delete workloads, if none passed, delete every GPU job"""
    workloads=sys.argv[2:]

    if workloads == "-h":
        print("bdel [jobname [jobname...]] \n"
        "Delete the specified jobs, if none are specified then all current jobs are deleted ;-) \n"
        "See repository README.md for more documentation and examples.")
        return 0

    if not workloads:
        res = run(["oc", "get", "workloads", "-o", "name"])
        if res.returncode != 0:
            sys.stderr.write("Failed to list workloads via oc.\n")
            sys.exit(res.returncode)
        workloads = [w for w in workloads if w.startswith("job-job") or w.startswith("workloads/job-job")]

    if not workloads:
        print ("No GPU worloads found to delete")
        return  

    exit_code = 0
    for w in workloads:
        name = w if "/" in w else f"workloads/{w}"
        res = run(["oc", "delete", name])
        if res.stdout:
            sys.stdout.write(res.stdout)
        if res.stderr:
            sys.stderr.write(res.stderr)
        if res.returncode != 0:
            exit_code = res.returncode

    sys.exit(exit_code)

def bj():
    WATCH=sys.argv[2:]

    if WATCH == "-h":
        print("bjobs \n Display the status of your jobs. \n"
        "This include all jobs that have not been deleted. Note: jobs must be explicitly deleted after they have completed.  'brun' deletes by default.  However, if you specified WAIT=0 to 'brun' then it will not delete the job.Set WATCH=1 to have bjobs stay running and display changes in your jobs. See 'brun -h' and repository README.md for more documentation and examples.")
        return 0

    if WATCH:
        run(["oc", "get", "-w", "workloads"])
    else:
        run(["oc", "get", "workloads"])

def bl():
    print("bl called")

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

    # Skip the first arg (program name)
    args = sys.argv[1]

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
