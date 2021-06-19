#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
import enum
from pathlib import Path
from zipfile import ZipFile

import yaml

from server_manager.plugins.exceptions import *


@enum.unique
class PluginPlatform(enum.Enum):
    PAPER = enum.auto()
    VELOCITY = enum.auto()


@dataclasses.dataclass(frozen=True)
class PluginInfo:
    name: str
    version: str
    platform: PluginPlatform
    raw: dict

    @classmethod
    def from_data(cls, data: dict, platform: PluginPlatform) -> PluginInfo:
        return cls(
            name=data["name"], version=data["version"], platform=platform, raw=data
        )


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
        return PluginInfo.from_data(data=data, platform=PluginPlatform.PAPER)


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
            data = yaml.safe_load(plug)
        return PluginInfo.from_data(data=data, platform=PluginPlatform.VELOCITY)


def get_plugin_info(file: Path) -> PluginInfo:
    if not file.exists():
        raise FileNotExistentException(file)

    try:
        return get_paper_plugin_info(file)
    except NotAPaperPluginException:
        return get_velocity_plugin_info(file)
