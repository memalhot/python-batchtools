from typing_extensions import override

import argparse
import sys
import openshift_client as oc

from .helpers import is_kueue_managed_job
from .basecommand import Command


class ListJobsCommand(Command):
    """
    batchtools bj

    Display the status of your jobs. This includes all jobs that have not been deleted.

    Note:
    Jobs must be explicitly deleted after they have completed.
    'brun' deletes jobs by default. However, if you specified WAIT=0 to 'brun',
    then it will not delete the job.

    """

    name: str = "bj"
    help: str = "Display the status of GPU jobs"

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        """
        Display the status of GPU jobs using 'oc get jobs'.
        """
        try:
            jobs = oc.selector("jobs").objects()
            if not jobs:
                print("No jobs found.")
                return

            # filter only Kueue-managed jobs
            managed = [job for job in jobs if is_kueue_managed_job(job)]

            print(f"Found {len(managed)} job(s):\n")

            for job in managed:
                print(f"- {job.model.metadata.name}")

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while retrieving jobs: {e}")
