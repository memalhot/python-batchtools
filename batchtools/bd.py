import sys
import argparse
from typing import cast
import openshift_client as oc
from .basecommand import Command, override
from .basecommand import SubParserFactory
from .helpers import oc_delete, is_kueue_managed_job


class DeleteJobsCommand(Command):
    """
    batchtools bd [job-name [job-name ...]]

    Delete specified Kueue-managed GPU jobs, or all such jobs if none are specified.

    Description:
        Deletes only those Jobs that are both:
          - named like your GPU jobs (name starts with 'job-'), and
          - detected as Kueue-managed (via labels/Workload linkage).
    """

    name: str = "bd"
    help: str = "Delete specified Kueue-managed GPU jobs, or all if none are specified"

    @classmethod
    @override
    def build_parser(cls, subparsers: SubParserFactory):
        p = super().build_parser(subparsers)
        p.add_argument(
            "job_names",
            nargs="*",
            help="Optional list of job names to delete (must be Kueue-managed)",
        )
        return p

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        args = cast(DeleteJobsCommand, args)
        try:
            jobs = oc.selector("jobs").objects()
            if not jobs:
                print("No jobs found.")
                return

            gpu_jobs = [job for job in jobs]

            # only want to delete kueue jobs so filter for kueue jobs
            kueue_gpu_jobs = [job for job in gpu_jobs if is_kueue_managed_job(job)]

            if not kueue_gpu_jobs:
                print("No Kueue-managed GPU jobs to delete.")
                return

            if args.job_names:
                # if jobs are specified, only delete specified jobs
                allowed = {job.model.metadata.name for job in kueue_gpu_jobs}
                for name in args.job_names:
                    if name not in allowed:
                        print(f"{name} is not a Kueue-managed GPU job; skipping.")
                        continue
                    oc_delete("job", name)
                    print(f"Deleted job: {name}")
            else:
                print("No job names provided -> deleting all Kueue-managed GPU jobs:\n")
                for job in kueue_gpu_jobs:
                    name = job.model.metadata.name
                    oc_delete("job", name)
                    print(f"Deleted job: {name}")

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while deleting jobs: {e}")
