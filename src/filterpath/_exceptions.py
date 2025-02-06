from ._types import ObjTypes, PathTypes


class NoPathExistsError(KeyError):
    def __init__(self, obj: ObjTypes, path: PathTypes) -> None:
        super().__init__(f"{obj!r} does not contain path '{path}'")


class NotPathLikeError(TypeError):
    def __init__(self, path: PathTypes) -> None:
        super().__init__(
            f"path argument must be one of '{PathTypes}', not '{type(path).__name__}'",
        )
