import dataclasses
from pathlib import Path

from requests import Response, Session

from server_manager.hash_utils import sha1
from server_manager.plugin import PluginInfo
from server_manager.utils import plugin_to_b2_name

BASE_URL = "https://files.nearvanilla.com/plugins"
SESSION = Session()
SESSION.headers["User-Agent"] = "ServerJarManager"


@dataclasses.dataclass(frozen=True)
class RemotePluginInfo:
    size: int
    sha1: str
    filename: str
    upload_timestamp: int


def response_to_file(response: Response, file: Path) -> None:
    """Writes requests.Response content to file."""
    with file.open("wb") as f:
        for chunk in response.iter_content():
            f.write(chunk)


def download_plugin(plugin: PluginInfo, destination: Path) -> None:
    """Download plugin and put it in destination"""
    url = f"{BASE_URL}/{plugin_to_b2_name(plugin)}"
    response = SESSION.get(url)
    response.raise_for_status()
    response_to_file(response, destination)
    # TODO: Throw a proper exception
    assert sha1(destination) == get_remote_plugin_info_from_response(response).sha1


def get_remote_plugin_info_from_response(response: Response) -> RemotePluginInfo:
    """Get plugin info from response"""
    headers = response.headers
    return RemotePluginInfo(
        size=int(headers["Content-Length"]),
        sha1=headers["x-bz-content-sha1"],
        filename=headers["x-bz-file-name"],
        upload_timestamp=int(headers["X-Bz-Upload-Timestamp"]),
    )


def get_remote_plugin_info(plugin: PluginInfo) -> RemotePluginInfo:
    """Get plugin info from remote"""
    url = f"{BASE_URL}/{plugin_to_b2_name(plugin)}"
    response = SESSION.head(url)
    response.raise_for_status()
    return get_remote_plugin_info_from_response(response)
