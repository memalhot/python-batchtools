import pytest
import argparse
import os


@pytest.fixture(autouse=True)
def null_kubeconfig():
    # Ensure that we do not accidentally interact with a real cluster
    os.environ["KUBECONFIG"] = "/dev/null"


@pytest.fixture
def args() -> argparse.Namespace:
    return argparse.Namespace()


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    return p


@pytest.fixture
def subparsers(parser):
    return parser.add_subparsers(dest="cmd")
