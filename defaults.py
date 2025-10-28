import os

gpu = "v100"
image = "image-registry.openshift-image-registry.svc:5000/redhat-ods-applications/csw-run-f25:latest"
context = True
name = "job"
job_id = os.getpid()
job_delete = True
wait = True
timeout = 60 * 15 * 4
max_sec = 60 * 15
gpu_numreq = 1
gpu_numlim = 1
verbose = 0
