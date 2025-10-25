# pyright: reportExplicitAny=false, reportAny=false

import abc
from typing import Protocol
from typing import Any

import argparse


class SubParserFactory(Protocol):
    """
    This is here to make type checkers happy. Since argparse._SubParsersAction
    is a private class, we can't use it as a type hint, so we use this instead.
    """

    def add_parser(
        self,
        name: str,
        *,
        deprecated: bool = False,
        **kwargs: Any,
    ) -> argparse.ArgumentParser: ...


class Command(abc.ABC):
    """
    Base class for all command implementations.
    """

    name: str
    help: str
    description: str | None = None

    @classmethod
    def build_parser(cls, subparsers: SubParserFactory) -> argparse.ArgumentParser:
        p = subparsers.add_parser(
            cls.name,
            help=cls.help,
            description=cls.__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        return p

    @staticmethod
    @abc.abstractmethod
    def run(args: argparse.Namespace) -> None:
        raise NotImplementedError()
