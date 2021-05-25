import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
import sh
from click.testing import CliRunner

import manage


# Helpers
@pytest.fixture
def tmp_path_sh(tmp_path):
    newsh = sh(_cwd=tmp_path)
    return newsh


@pytest.fixture
def tmp_path_git(tmp_path_sh):
    return tmp_path_sh.git


@pytest.fixture
def tmp_git_wrapper(tmp_path, tmp_path_git) -> manage.GitWrapper:
    gitcli = tmp_path_git
    gitcli.init()
    gitcli.commit(allow_empty=True, message="initial message")
    return manage.GitWrapper(tmp_path)


@contextmanager
def chdir(path):
    current_path = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current_path)


def create_file_with_content(file_path: Path, content: str) -> None:
    """Create file and write content to it"""
    with file_path.open("w") as file:
        file.write(content)


def get_file_md5sum(file_path: Path) -> str:
    with file_path.open("rb") as file:
        return hashlib.md5(file.read()).hexdigest()


# Tests
def test_is_empty_dir(tmp_path):
    assert manage.is_dir_empty(tmp_path)
    file = tmp_path / "testfile"
    file.touch()
    assert not manage.is_dir_empty(tmp_path)


def test_getting_correct_commit(tmp_path, tmp_path_git):
    gitcli = tmp_path_git
    commit_msg = "First commit"
    gitcli.init()
    gitcli.commit(message=commit_msg, allow_empty=True)
    git = manage.GitWrapper(tmp_path)
    assert git.get_commit_subject("HEAD") == commit_msg
    assert git.get_commit_subject("master") == commit_msg


def test_dirty_workspace_detection(tmp_path, tmp_path_git):
    test_file = tmp_path / "test_file"
    gitcli = tmp_path_git
    gitcli.init()
    git = manage.GitWrapper(tmp_path)
    test_file.touch()
    gitcli.add(test_file)
    gitcli.commit(message="Test Commit")
    assert git.is_worktree_clean()
    with test_file.open("w") as f:
        f.write("Test Content")
    assert not git.is_worktree_clean()
    gitcli.add(test_file)
    assert not git.is_worktree_clean()


def test_tracked_files_finding(tmp_path, tmp_path_git):
    """Check GitWrapper ability to find tracked files, without finding untracked ones"""
    gitcli = tmp_path_git
    gitcli.init()
    git = manage.GitWrapper(tmp_path)
    gitcli.commit(allow_empty=True, message="Initial commit")
    assert len(git.all_config_tracked_files()) == 0
    file_names = ("one", "two", "three")
    file_paths = tuple(tmp_path / name for name in file_names)
    for file in file_paths:
        assert not file.exists()
        file.touch()
    assert len(git.all_config_tracked_files()) == 0
    gitcli.add(*file_paths)
    gitcli.commit(message="Test commit")
    assert len(git.all_config_tracked_files()) == len(file_paths)
    assert git.is_worktree_clean()


def test_no_unneeded_substitution(tmp_path):
    empty_file = tmp_path / "empty_file"
    file_without_placeholders = tmp_path / "placeholderless_file"
    substitutions = {"TESTKEY": "TESTVALUE"}
    empty_file.touch()
    create_file_with_content(file_without_placeholders, "This is just a random string")
    for file in (empty_file, file_without_placeholders):
        file_md5 = get_file_md5sum(file)
        manage.substitute_placeholders([file], substitutions={})
        assert get_file_md5sum(file) == file_md5
        manage.substitute_placeholders([file], substitutions=substitutions)
        assert get_file_md5sum(file) == file_md5


def test_basic_placeholder_substitution(tmp_path):
    file = tmp_path / "placeholdered_file"
    substitutions = {"TESTKEY": "TESTVALUE"}
    create_file_with_content(file, "PASSWORD: {{ TESTKEY }}")
    manage.substitute_placeholders([file], substitutions=substitutions)
    with file.open("r") as f:
        assert f.read() == "PASSWORD: TESTVALUE"


def test_basic_substitution_and_commit(tmp_path, tmp_path_git):
    test_file = tmp_path / "test_file"
    gitcli = tmp_path_git
    substitutions = {"TESTKEY": "TESTVALUE"}
    create_file_with_content(test_file, "PASSWORD: {{ TESTKEY }}")
    initial_md5 = get_file_md5sum(test_file)
    # Create worktree, but the file is not tracked
    gitcli.init()
    git = git_wrapper = manage.GitWrapper(tmp_path)
    gitcli.commit(allow_empty=True, message="Initial commit")
    manage.substitute_tracked_and_commit(git_wrapper, substitutions=substitutions)
    assert get_file_md5sum(test_file) == initial_md5
    # Track file and substitute it for real now
    gitcli.add(test_file)
    commit_message = "Add test file"
    gitcli.commit(message=commit_message)
    assert git.get_commit_subject() == commit_message
    manage.substitute_tracked_and_commit(git_wrapper, substitutions=substitutions)
    with test_file.open("r") as f:
        assert f.read() == "PASSWORD: TESTVALUE"
    assert git.is_worktree_clean()
    assert git.get_commit_subject() != commit_message


def test_list_paths_simple(tmp_path, tmp_path_git):
    gitcli = tmp_path_git
    gitcli.init()
    gitcli.commit(message="First commit", allow_empty=True)
    git = manage.GitWrapper(tmp_path)
    assert set(git.list_tracked_files()) == set()
    empty_file = tmp_path / "empty_file"
    empty_file.touch()
    gitcli.add(empty_file)
    gitcli.commit(message="Second commit")
    tracked_files = set(git.list_tracked_files())
    assert tracked_files == {empty_file}
    nested_empty_file = tmp_path / "nested/empty/file"
    nested_empty_file.parent.mkdir(parents=True)
    nested_empty_file.touch()
    gitcli.add(nested_empty_file)
    gitcli.commit(message="Third commit")
    tracked_files = set(git.list_tracked_files())
    assert tracked_files == {empty_file, nested_empty_file}


def test_list_paths_with_submodules(tmp_path):
    main_repo_path = tmp_path / "main_repo"
    main_file = main_repo_path / "main_file"
    submodule_path = tmp_path / "submodule"
    submodule_file = submodule_path / "submodule_file"
    for repo_path in (main_repo_path, submodule_path):
        repo_path.mkdir()
        gitcli = sh.git.bake(_cwd=repo_path)
        gitcli.init()

    for file in (main_file, submodule_file):
        file.touch()

    maingit = sh.git.bake(_cwd=main_repo_path)
    subgit = sh.git.bake(_cwd=submodule_path)

    subgit.add(submodule_file)
    subgit.commit(message="Submodule Commit")

    maingit.add(main_file)
    maingit.submodule.add(submodule_path)
    maingit.commit(message="Main Commit")

    git = manage.GitWrapper(main_repo_path)
    assert set(git.list_tracked_files()) == {main_file, main_repo_path / ".gitmodules"}


def test_subworktree_basic(tmp_path):
    # Adding/listing
    maingit = sh.git.bake(_cwd=tmp_path)
    maingit.init()
    git = manage.GitWrapper(tmp_path)
    assert set(git.get_all_subworktrees()) == set()
    worktree = manage.WorkTree(path="my_path", revision="my_ref")
    with pytest.raises(manage.RefNotExistsError):
        git.add_subworktree(worktree)
    # Init
    worktreepath = tmp_path / worktree.path
    maingit.commit(allow_empty=True, message="Main message")
    maingit.checkout("--orphan", worktree.revision)
    worktree_subject = "Worktree message"
    maingit.commit(allow_empty=True, message=worktree_subject)
    worktree_hash = maingit("rev-list", "HEAD", n=1, format="%H").split("\n")[1].strip()
    maingit.checkout("master")

    git.add_subworktree(worktree)
    assert set(git.get_all_subworktrees()) == set((worktree,))

    assert not worktreepath.exists()
    workgit = worktree.init(git)
    assert worktreepath.exists()
    # GitRepo working :)
    assert workgit.is_worktree_clean()
    assert workgit.get_commit_subject() == worktree_subject
    assert workgit.get_commit_sha() == worktree_hash


def test_cli_new_subworktree(tmp_path, tmp_git_wrapper):
    git = tmp_git_wrapper
    assert set(git.get_all_subworktrees()) == set()

    worktree = manage.WorkTree(path="my_path", revision="my_ref")
    runner = CliRunner()
    with chdir(tmp_path):
        # First creation should be successful
        result = runner.invoke(
            manage.cli, ["new-subworktree", str(worktree.path), worktree.revision]
        )
        if result.exception:
            raise result.exception
        assert set(git.get_all_subworktrees()) == set((worktree,))

        # Second creation should fail, as it exists already
        result = runner.invoke(
            manage.cli, ["new-subworktree", str(worktree.path), worktree.revision]
        )
        assert isinstance(result.exception, SystemExit)


@pytest.fixture
def added_worktree(tmp_git_wrapper):
    git = tmp_git_wrapper
    assert set(git.get_all_subworktrees()) == set()
    worktree = manage.WorkTree(path="worktree_path", revision="worktree_revision")
    git.create_detached_empty_branch(worktree.revision, "Initial commit")
    git.add_subworktree(worktree)
    assert set(git.get_all_subworktrees()) == set((worktree,))
    return worktree


def test_cli_init_nonexistent_and_initialized(tmp_git_wrapper, added_worktree):
    git = tmp_git_wrapper
    runner = CliRunner()
    with chdir(git.path):
        result = runner.invoke(manage.cli, ["init"])
        if result.exception:
            raise result.exception
        assert "Initializing" in result.stdout
        result = runner.invoke(manage.cli, ["init"])
        if result.exception:
            raise result.exception
        assert "Skipping" in result.stdout


def test_cli_init_empty_dir(tmp_git_wrapper, added_worktree):
    git = tmp_git_wrapper
    worktree = added_worktree
    runner = CliRunner()
    with chdir(git.path):
        worktree.path.mkdir()
        result = runner.invoke(manage.cli, ["init"])
        if result.exception:
            raise result.exception
        assert "Initializing" in result.stdout


def test_cli_init_dirty_dir(tmp_git_wrapper, added_worktree):
    git = tmp_git_wrapper
    worktree = added_worktree
    runner = CliRunner()
    with chdir(git.path):
        worktree.path.mkdir()
        (worktree.path / "random_file").touch()
        result = runner.invoke(manage.cli, ["init"])
        with pytest.raises(SystemExit):
            if result.exception:
                raise result.exception
        assert "Unable to initialize" in result.stdout
