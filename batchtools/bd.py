import sys
import argparse
from typing import cast

import openshift_client as oc

from .basecommand import Command, override
from .basecommand import SubParserFactory
from .helpers import oc_delete


class DeleteJobsCommand(Command):
    """
    batchtools bd [job-name [job-name ...]]

    Delete specified Jobs, or all Jobs if none are specified.
    """

    name: str = "bd"
    help: str = "Delete specified Jobs, or all if none are specified"

    @classmethod
    @override
    def build_parser(cls, subparsers: SubParserFactory):
        p = super().build_parser(subparsers)
        p.add_argument(
            "job_names",
            nargs="*",
            help="Optional list of job names to delete",
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

            if args.job_names:
                # delete only specified jobs
                existing = {job.model.metadata.name for job in jobs}
                for name in args.job_names:
                    if name not in existing:
                        print(f"{name} does not exist; skipping.")
                        continue
                    oc_delete("job", name)
                    print(f"Deleted job: {name}")
            else:
                # delete all jobs
                print("No job names provided -> deleting ALL jobs:\n")
                for job in jobs:
                    name = job.model.metadata.name
                    oc_delete("job", name)
                    print(f"Deleted job: {name}")

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while deleting jobs: {e}")
