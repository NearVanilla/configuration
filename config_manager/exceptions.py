from pathlib import Path


class ManageException(Exception):
    pass


class DirtyWorkTreeException(ManageException):
    """WorkTree is dirty, but it's required to be empty"""

    def __init__(self):
        super().__init__("Worktree is modified")


class WorkTreeAlreadySubstitutedException(ManageException):
    """Worktree has already been substituted"""

    def __init__(self):
        super().__init__("Worktree already substituted")


class WorkTreeNotSubstitutedException(ManageException):
    """Worktree has not been substituted"""

    def __init__(self):
        super().__init__("Worktree not substituted")


class RefNotExistsError(ValueError):
    def __init__(self, ref):
        super().__init__(f"Reference named '{ref}' does not exist")


class SubstituteException(ManageException):
    def __init__(self, path: Path):
        super().__init__(f"Error substituting file {path}")


class DetachedHeadException(ManageException):
    def __init__(self):
        super().__init__(
            "Head is detached from any branch, where it's required not to be so"
        )
