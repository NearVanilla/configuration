#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


class PluginException(Exception):
    pass


class NotAPluginException(PluginException):
    pass


class NotAPaperPluginException(NotAPluginException):
    pass


class NotAVelocityPluginException(NotAPluginException):
    pass


class FileNotExistentException(PluginException):
    def __init__(self, file: Path):
        super().__init__(f"File {file} does not exist")
