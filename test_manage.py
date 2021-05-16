import manage
import pytest
import sh
from pathlib import Path
import hashlib

# Helpers
@pytest.fixture
def tmp_path_sh(tmp_path):
    newsh = sh(_cwd=tmp_path)
    return newsh


@pytest.fixture
def git_wrapper(tmp_path):
    return manage.GitWrapper(tmp_path)

def create_file_with_content(file_path: Path, content: str) -> None:
    """Create file and write content to it"""
    with file_path.open('w') as file:
        file.write(content)

def get_file_md5sum(file_path: Path) -> str:
    with file_path.open('rb') as file:
        return hashlib.md5(file.read()).hexdigest()

# Tests
def test_is_in_git_work_tree(git_wrapper):
    """Tests GitWrapper ability to check if it's in work tree or not"""
    git = git_wrapper
    gitcli = git._git
    assert not git.is_in_git_work_tree()
    gitcli.init()
    assert git.is_in_git_work_tree()

def test_dirty_workspace_detection(git_wrapper, tmp_path):
    git = git_wrapper
    test_file = tmp_path / 'test_file'
    gitcli = git._git
    gitcli.init()
    test_file.touch()
    gitcli.add(test_file)
    gitcli.commit(message='Test Commit')
    assert git.is_worktree_clean()
    with test_file.open('w') as f:
        f.write('Test Content')
    assert not git.is_worktree_clean()
    gitcli.add(test_file)
    assert not git.is_worktree_clean()


def test_tracked_files_finding(git_wrapper, tmp_path):
    """Check GitWrapper ability to find tracked files, without finding untracked ones"""
    git = git_wrapper
    gitcli = git._git
    gitcli.init()
    gitcli.commit(allow_empty=True, message='Initial commit')
    assert len(git.all_config_tracked_files()) == 0
    file_names = ('one', 'two', 'three' )
    file_paths = tuple(tmp_path / name for name in file_names)
    for file in file_paths:
        assert not file.exists()
        file.touch()
    assert len(git.all_config_tracked_files()) == 0
    gitcli.add(*file_paths)
    gitcli.commit(message='Test commit')
    assert len(git.all_config_tracked_files()) == len(file_paths)
    assert git.is_worktree_clean()


def test_outside_work_tree_exception(git_wrapper):
    git = git_wrapper
    with pytest.raises(manage.OutsideWorkTreeException):
        git.get_commit_subject()


def test_no_unneeded_substitution(tmp_path):
    empty_file = tmp_path / 'empty_file'
    file_without_placeholders = tmp_path / 'placeholderless_file'
    substitutions = {'TESTKEY': 'TESTVALUE'}
    empty_file.touch()
    create_file_with_content(file_without_placeholders, "This is just a random string")
    for file in (empty_file, file_without_placeholders):
        file_md5 = get_file_md5sum(file)
        manage.substitute_placeholders([file], substitutions={})
        assert get_file_md5sum(file) == file_md5
        manage.substitute_placeholders([file], substitutions=substitutions)
        assert get_file_md5sum(file) == file_md5

def test_basic_placeholder_substitution(tmp_path):
    file = tmp_path / 'placeholdered_file'
    substitutions = {'TESTKEY': 'TESTVALUE'}
    create_file_with_content(file, "PASSWORD: {{ TESTKEY }}")
    manage.substitute_placeholders([file], substitutions=substitutions)
    with file.open('r') as f:
        assert f.read() == "PASSWORD: TESTVALUE"

def test_basic_substitution_and_commit(git_wrapper, tmp_path):
    test_file = tmp_path / 'test_file'
    git = git_wrapper
    gitcli = git._git
    substitutions = {'TESTKEY': 'TESTVALUE'}
    create_file_with_content(test_file, "PASSWORD: {{ TESTKEY }}")
    initial_md5 = get_file_md5sum(test_file)
    # No worktree yet - throws error
    with pytest.raises(manage.OutsideWorkTreeException):
        manage.substitute_tracked_and_commit(git_wrapper, substitutions=substitutions)
    assert get_file_md5sum(test_file) == initial_md5
    # Create worktree, but the file is not tracked
    gitcli.init()
    gitcli.commit(allow_empty=True, message='Initial commit')
    manage.substitute_tracked_and_commit(git_wrapper, substitutions=substitutions)
    assert get_file_md5sum(test_file) == initial_md5
    # Track file and substitute it for real now
    gitcli.add(test_file)
    commit_message = 'Add test file'
    gitcli.commit(message=commit_message)
    manage.substitute_tracked_and_commit(git_wrapper, substitutions=substitutions)
    with test_file.open('r') as f:
        assert f.read() == "PASSWORD: TESTVALUE"
    print(gitcli.log(n=1))
    print(gitcli.status())
    assert git.is_worktree_clean()
    assert git.get_commit_subject() != commit_message



