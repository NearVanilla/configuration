from __future__ import annotations  # Postponed evaluation PEP-563

import os
from pathlib import Path
from typing import Iterable, Optional, Union
import string

import jinja2

from server_manager.config.exceptions import *
from server_manager.config.gitwrapper import GitWrapper, require_clean_workspace
from server_manager.config.utils import current_date

Substitutions = Union[dict, None]

COMMIT_SUBSTITUTED = "[SUBST]"
COMMIT_CHANGED = "[CHNG]"
JINJA_ENVIRONMENT = {
    "block_start_string": "<<<%",
    "block_end_string": "%>>>",
    "comment_start_string": "<<<#",
    "comment_end_string": "#>>>",
    "undefined": jinja2.StrictUndefined,  # Throw error on missing values
}


def _get_trailing_whitespace(content: str) -> str:
    """Get all trailing whitespace characters from given content

    >>> _get_trailing_whitespace("")
    ''
    >>> _get_trailing_whitespace("abc\ndef\nghi")
    ''
    >>> _get_trailing_whitespace("abc\ndef\nghi\n")
    '\n'
    >>> _get_trailing_whitespace("abc\ndef\nghi\n\n\n")
    '\n\n\n'
    """
    ws = set(string.whitespace)
    result = []
    for char in reversed(content):
        if char in ws:
            result.append(char)
        else:
            break
    return "".join(reversed(result))


def substitute_placeholders(
    files: Iterable[Path],
    substitutions: Substitutions = None,
    environment: Optional[dict] = None,
) -> None:
    if substitutions is None:
        substitutions = dict(os.environ)
    if environment is None:
        environment = dict()
    for k, v in JINJA_ENVIRONMENT.items():
        if k not in environment:
            environment[k] = v
    for file in files:
        try:
            with file.open("r+") as f:
                original = f.read()
                template = jinja2.Template(original, **environment)
                rendered = template.render(**substitutions)
                # Jinja seems to eat trailing whitespace (most importantly newlines)
                # And plugins often restore them later
                # To avoid issues, we restore trailing whitespace from original file
                orig_ws = _get_trailing_whitespace(original)
                rend_ws = _get_trailing_whitespace(rendered)
                # If it's 0, it'd destroy whole file...
                rendered = rendered[: -len(rend_ws) or None] + orig_ws
                if rendered != original:
                    f.seek(0)
                    f.truncate()
                    f.write(rendered)
        except Exception as e:
            raise SubstituteException(file) from e


@require_clean_workspace
def substitute_tracked_placeholders(
    git: GitWrapper, substitutions: Substitutions = None
) -> None:
    if is_substituted(git):
        raise WorkTreeAlreadySubstitutedException()
    try:
        substitute_placeholders(git.all_config_tracked_files(), substitutions)
    except:
        git.repo.head.reset(working_tree=True)
        raise


def substitute_tracked_and_commit(
    git: GitWrapper, substitutions: Substitutions = None
) -> None:
    substitute_tracked_placeholders(git, substitutions)
    if not git.is_worktree_clean():
        git.stage_all_tracked()
        git.commit(message=f"{COMMIT_SUBSTITUTED} {current_date()}")


def commit_and_unsubstitute(git: GitWrapper, msg: str) -> None:
    if not is_substituted(git):
        raise WorkTreeNotSubstitutedException()
    if git.repo.head.is_detached:
        raise DetachedHeadException()
    presub_commit = git.repo.commit("HEAD^")
    sub_commit = git.repo.commit("HEAD")
    if git.is_worktree_clean():
        # Reset our change commit
        git.repo.active_branch.commit = presub_commit
        git.repo.head.reset(index=True, working_tree=True)
    else:
        git.stage_all_tracked()
        git.commit(COMMIT_CHANGED)
        git.repo.git.revert(sub_commit.hexsha, no_edit=True)
        # Squash
        git.repo.active_branch.commit = presub_commit
        git.repo.head.reset(index=False, working_tree=False)
        # This might have changed for some reason
        # Make sure we aren't making useless, empty commit
        if not git.is_worktree_clean():
            git.commit(msg)


def is_substituted(git: GitWrapper):
    return git.get_commit_subject("HEAD").startswith(COMMIT_SUBSTITUTED)
