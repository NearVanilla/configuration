from __future__ import annotations
import dataclasses
from pathlib import Path

from requests import Response, Session

from server_manager.hash_utils import sha256
from typing import Iterable, List, Dict, Any, Optional

from .utils import response_to_file

BASE_URL = "https://api.papermc.io/v2"
SESSION = Session()
SESSION.headers["User-Agent"] = "ServerJarManager"
SESSION.headers["Accept"] = "application/json"


@dataclasses.dataclass(frozen=True)
class Base:
    project_id: str
    project_name: str

    def get_project(self) -> Project:
        return Project.get_project_from_id(self.project_id)

    @staticmethod
    def get_project_request_url(project_id: str) -> str:
        return f"{BASE_URL}/projects/{project_id}"

    @property
    def project_base_url(self) -> str:
        return self.get_project_request_url(self.project_id)


@dataclasses.dataclass(frozen=True)
class Project(Base):
    version_groups: List[str]
    versions: List[str]

    @classmethod
    def get_project_from_id(cls, project_id: str) -> Project:
        response = SESSION.get(cls.get_project_request_url(project_id))
        response.raise_for_status()
        return cls(**response.json())


@dataclasses.dataclass(frozen=True)
class VersionBase(Base):
    version: str

    def get_version(self) -> Version:
        return Version.get_version_from(self.project_id, self.version)

    @classmethod
    def get_version_request_url(cls, project_id: str, version: str) -> str:
        return f"{cls.get_project_request_url(project_id)}/versions/{version}"

    @property
    def version_base_url(self) -> str:
        return self.get_version_request_url(self.project_id, self.version)


@dataclasses.dataclass(frozen=True)
class Version(VersionBase):
    builds: List[int]

    @classmethod
    def get_version_from(cls, project_id: str, version: str) -> Version:
        response = SESSION.get(cls.get_version_request_url(project_id, version))
        response.raise_for_status()
        return cls(**response.json())

    def get_latest_build(self) -> int:
        return max(self.builds)


@dataclasses.dataclass(frozen=True)
class BuildBase(VersionBase):
    build: int

    def get_build(self) -> Build:
        return Build.get_build_from(self.project_id, self.version, self.build)

    @classmethod
    def get_build_request_url(cls, project_id: str, version: str, build: int) -> str:
        return f"{cls.get_version_request_url(project_id, version)}/builds/{build}"

    @property
    def build_base_url(self) -> str:
        return self.get_build_request_url(self.project_id, self.version, self.build)


@dataclasses.dataclass(frozen=True)
class Build(BuildBase):
    time: str
    channel: str
    promoted: bool
    changes: List[Dict[str, str]]
    downloads: Dict[str, Dict[str, str]]

    @classmethod
    def get_build_from(cls, project_id: str, version: str, build: int) -> Build:
        response = SESSION.get(cls.get_build_request_url(project_id, version, build))
        response.raise_for_status()
        return cls(**response.json())

    def get_download_url(self, file_name: str) -> str:
        return f"{self.build_base_url}/downloads/{file_name}"

    def download(self, name: str, destination: Optional[Path] = None) -> None:
        """Download given prop to destination, or prop name if not given"""
        if destination is None:
            destination = Path(".")
        prop = self.downloads.get(name)
        if prop is None:
            raise ValueError(f"Non-existent prop name: {name}")
        prop_name = prop["name"]
        if destination.is_dir():
            destination = destination / prop_name
        response = SESSION.get(self.get_download_url(prop_name))
        response.raise_for_status()
        response_to_file(response, destination)
        assert destination.exists()
        # TODO: Throw propper exception
        assert sha256(destination) == prop["sha256"]
