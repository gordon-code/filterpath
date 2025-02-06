from collections.abc import Mapping, Sequence
from typing import NamedTuple, Union

ObjTypes = Union[Sequence, Mapping, NamedTuple]  # noqa: UP007
PathTypes = str | list | tuple
