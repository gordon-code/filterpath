import contextlib
from collections.abc import Hashable
from typing import Any

from loguru import logger

from ._exceptions import NoPathExistsError, NotPathLikeError
from ._types import ObjTypes, PathTypes


def get(  # noqa: C901, PLR0915
    obj: ObjTypes,
    path: PathTypes,
    default: Any = None,
    path_separator: str = ".",
    raise_if_unfound: bool = False,
) -> Any | list[Any]:
    """Deeply traverse list/tuple/dict-like objects using a delimited string or list/tuple to .

    :param obj:
    :type obj: Sequence | Mapping
    :param path:
    :type path: str | list | tuple
    :param default:
    :type default: Any
    :param path_separator:
    :type path_separator: str
    :param raise_if_unfound:
    :type raise_if_unfound: bool
    :return:
    :rtype: Any | list[Any]
    """
    escapable_sequences: frozenset[str] = frozenset({path_separator, "\\", "[", ":"})
    sentinel: object = object()

    def _deep_get(_obj: ObjTypes, _path: PathTypes, container: list) -> Any | list[Any]:  # noqa: C901
        if _obj is sentinel:
            # STOP: Run out of objects to traverse
            logger.trace("out of objects: raising NoPathExistsError")
            raise NoPathExistsError(obj, path)

        if len(_path) == 0:
            # STOP: Run out of path variables
            logger.trace(f"out of paths: return {_obj}")
            return _obj

        if not hasattr(_obj, "__getitem__") or isinstance(_obj, str):
            # STOP: There are more path variables, but don't try traversing non-iterable or string
            logger.trace("out of iterables: raising NoPathExistsError")
            raise NoPathExistsError(obj, path)

        key, _path, has_container = _parse_path(_path)
        logger.trace(f"current key '{key}' and remaining path '{_path}'")

        if has_container:
            logger.trace("encountering container")
            # Strip brackets for any filtering key or function
            filter_key: str = key[1:-1]

            logger.trace(f"filtering container on '{key}'")
            try:
                filtered_obj: Any | list[Any] = _deep_get(_obj, filter_key, container)
            except KeyError:
                logger.trace(f"unable to filter '{_obj}' on '{filter_key}', return empty list")
                return container

            if isinstance(filtered_obj, dict):
                filtered_obj = filtered_obj.values()

            logger.trace(f"iterating {filtered_obj}")
            try:
                filtered_obj = iter(filtered_obj)
            except TypeError:
                logger.trace(f"{filtered_obj} not iterable, returning {filtered_obj}")
                container.append(filtered_obj)
                return container

            for item in filtered_obj:
                logger.trace(f"getting path '{_path}' of '{item}'")
                try:
                    deep_obj: Any | list[Any] = _deep_get(item, _path, container)
                    if deep_obj is not container:
                        container.append(deep_obj)
                except KeyError:
                    pass

            return container

        logger.trace(f"access '{key}' in {_obj}")
        return _deep_get(_get_any(_obj, key), _path, container)

    def _parse_path(_path: PathTypes) -> tuple[Any, PathTypes, bool]:
        if isinstance(_path, str):
            is_escaped: bool = False
            has_container: bool = _path.startswith("[")
            slice_operator_count: int = 0
            escape_indexes: list = []
            for idx, char in enumerate(_path):
                if not is_escaped:
                    if char == path_separator:
                        # Non-escaped path separator
                        break

                    if char == ":":
                        slice_operator_count += 1

                elif char in escapable_sequences:
                    # Escaped value, store index of escape character (previous index)
                    escape_indexes.append(idx - 1)

                is_escaped = not is_escaped and char == "\\"
            else:
                # No path separators; increment the index in order to encapsulate the entire string
                idx += 1

            parsed_path: str = _remove_char_at_index(_path[:idx], escape_indexes)
            if slice_operator_count in {1, 2}:
                with contextlib.suppress(ValueError):
                    sliced_path: slice = slice(*(int(part) if part else None for part in parsed_path.split(":")))
                    return sliced_path, _path[idx + 1 :], False

            return parsed_path, _path[idx + 1 :], has_container and parsed_path.endswith("]")

        # Get next from _path, operating on a list/tuple
        curr_path: Any = _path[0]
        if isinstance(curr_path, str) and path_separator in curr_path:
            # Parse the returned key for any unescaped subpaths
            curr_path, remaining_path, has_container = _parse_path(curr_path)
            if remaining_path:
                # Prepend the remaining subpath
                remaining_path = [remaining_path, *_path[1:]]
            return curr_path, remaining_path, has_container
        return curr_path, _path[1:], False

    def _remove_char_at_index(string: str, index: int | list[int]) -> str:
        if isinstance(index, int):
            index = [index]

        for idx_remove in sorted(index, reverse=True):
            if idx_remove >= len(string):
                break
            string = string[:idx_remove] + string[idx_remove + 1 :]
        return string

    def _get_any(_obj: ObjTypes, key: Any) -> Any:
        value: Any = sentinel
        # Try as a dict, must use `.get()` to prevent defaultdict from being autofilled
        if isinstance(_obj, dict) and isinstance(key, Hashable):
            value = _obj.get(key, sentinel)

        else:
            try:
                value = _obj[key]
            except (IndexError, TypeError, KeyError):
                # Namedtuples
                if hasattr(_obj, "_fields") and key in _obj._fields:
                    value = getattr(_obj, key)

        if value is sentinel and not isinstance(key, int):
            with contextlib.suppress(ValueError, TypeError):
                # If the value still hasn't been found yet, try again with an integer key
                value = _get_any(_obj, int(key))

        return value

    if isinstance(path, PathTypes):
        try:
            return _deep_get(obj, path, [])
        except NoPathExistsError:
            if raise_if_unfound:
                logger.trace("raise KeyError instead of returning default")
                raise
            logger.trace(f"return default value: {default}")
            return default
    else:
        raise NotPathLikeError(path)
