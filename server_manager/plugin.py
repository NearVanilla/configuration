#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
import enum
import json
from pathlib import Path
from zipfile import ZipFile
from typing import Union

import yaml

from server_manager.hash_utils import sha1
from server_manager.plugin_exceptions import *


@enum.unique
class PluginPlatform(enum.Flag):
    PAPER = enum.auto()
    VELOCITY = enum.auto()


@enum.unique
class PluginComparison(enum.Enum):
    OUTDATED = enum.auto()
    UP_TO_DATE = enum.auto()
    NEWER = enum.auto()
    CHANGED = enum.auto()


@dataclasses.dataclass(frozen=True)
class PluginInfo:
    name: str
    version: str
    platform: PluginPlatform
    checksum: str
    raw: dict

    @classmethod
    def from_data(
        cls, data: dict, platform: PluginPlatform, checksum: str
    ) -> PluginInfo:
        version = data["version"]
        # Handle dumb plugins specifying version as array
        if isinstance(version, list) and len(version) == 1:
            version = version[0]
        return cls(
            name=data["name"],
            version=version,
            platform=platform,
            checksum=checksum,
            raw=data,
        )

    def compare_to(self, other: PluginInfo) -> PluginComparison:
        """
        Returns whether this plugin is older, newer or up to date to the other one

        >>> local_plugin = PluginInfo.from_data(data={"name": "test", "version": "1.2.0"}, platform=PluginPlatform.PAPER, checksum="")
        >>> local_plugin.compare_to(PluginInfo.from_data(data={"name": "test", "version": "1.3.0"}, platform=PluginPlatform.PAPER, checksum=""))
        <PluginComparison.OUTDATED: 1>
        >>> local_plugin.compare_to(PluginInfo.from_data(data={"name": "test", "version": "1.1.0"}, platform=PluginPlatform.PAPER, checksum=""))
        <PluginComparison.NEWER: 3>
        >>> local_plugin.compare_to(PluginInfo.from_data(data={"name": "test", "version": "1.2.0"}, platform=PluginPlatform.PAPER, checksum=""))
        <PluginComparison.UP_TO_DATE: 2>
        >>> local_plugin.compare_to(PluginInfo.from_data(data={"name": "test", "version": "1.2.1"}, platform=PluginPlatform.PAPER, checksum=""))
        <PluginComparison.OUTDATED: 1>
        >>> local_plugin.compare_to(PluginInfo.from_data(data={"name": "test", "version": "0.2.1"}, platform=PluginPlatform.PAPER, checksum=""))
        <PluginComparison.NEWER: 3>
        """
        if self.name != other.name:
            raise ValueError(
                f"Can't compare two different plugins - {self.name} and {other.name}"
            )
        myversion = self._versiontuple(self.version)
        otherversion = self._versiontuple(other.version)
        if myversion == otherversion:
            if self.checksum != other.checksum:
                # Main versions match, but additional stuff not
                return PluginComparison.CHANGED
            return PluginComparison.UP_TO_DATE
        elif myversion < otherversion:
            return PluginComparison.OUTDATED
        elif myversion > otherversion:
            return PluginComparison.NEWER
        else:
            raise RuntimeError(
                f"Unable to compare versions `{self.version}` and `{other.version}`"
            )

    @staticmethod
    def _versiontuple(version: str) -> tuple[Union[int, str], ...]:
        version = str(version)
        # Get rid of additional crap
        for separator in ("+", "-", " "):
            version = version.split(separator)[0]
        return tuple(int(i) if i.isdigit() else i for i in version.split("."))


def get_paper_plugin_info(file: Path) -> PluginInfo:
    datafile = "plugin.yml"
    if not file.exists():
        raise FileNotExistentException(file)
    with ZipFile(file) as zipfile:
        try:
            zipfile.getinfo(datafile)
        except KeyError as e:
            raise NotAPaperPluginException(
                f"{file} does not contain {datafile}!"
            ) from e
        with zipfile.open(datafile) as plug:
            data = yaml.safe_load(plug)
    checksum = sha1(file)
    return PluginInfo.from_data(
        data=data, platform=PluginPlatform.PAPER, checksum=checksum
    )


def get_velocity_plugin_info(file: Path) -> PluginInfo:
    datafile = "velocity-plugin.json"
    if not file.exists():
        raise FileNotExistentException(file)
    with ZipFile(file) as zipfile:
        try:
            zipfile.getinfo(datafile)
        except KeyError as e:
            raise NotAVelocityPluginException(
                f"{file} does not contain {datafile}!"
            ) from e
        with zipfile.open(datafile) as plug:
            data = json.load(plug)
    checksum = sha1(file)
    return PluginInfo.from_data(
        data=data, platform=PluginPlatform.VELOCITY, checksum=checksum
    )


def get_plugin_info(file: Path) -> PluginInfo:
    if not file.exists():
        raise FileNotExistentException(file)
    plugin = None
    for info_getter in (get_paper_plugin_info, get_velocity_plugin_info):
        try:
            new_plugin = info_getter(file)
            if plugin is None:
                plugin = new_plugin
            else:
                plugin = dataclasses.replace(
                    plugin, platform=plugin.platform | new_plugin.platform
                )
        except NotAPluginException:
            pass
    if plugin is None:
        raise NotAPluginException(f"{file} is not known plugin type jar")
    return plugin
