from typing import Any
from typing import Callable
from unittest import mock


def DictToObject(
    spec: dict[str, Any], obj: mock.Mock | None = None, name: str = None
) -> mock.Mock:
    """Transform a nested dictionary into an object hiearchy. We use this to create fake
    openshift_client response objects."""

    if obj is None:
        obj = mock.Mock(spec=list(spec.keys()), name=name)

    for key, val in spec.items():
        if isinstance(val, dict):
            setattr(obj, key, DictToObject(val, getattr(obj, key)))
        elif isinstance(val, list):
            setattr(
                obj,
                key,
                list(
                    [
                        DictToObject(item) if isinstance(item, dict) else item
                        for item in val
                    ]
                ),
            )
        elif isinstance(val, tuple) and len(val) > 0 and isinstance(val[0], Callable):
            if len(val) > 1:
                for k, v in val[1].items():
                    setattr(getattr(obj, key), k, v)
        else:  # this is the only addition
            setattr(obj, key, val)

    return obj
