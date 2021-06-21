from pathlib import Path

from requests import Response, Session

from server_manager.plugin import PluginInfo

BASE_URL = "https://files.nearvanilla.com/plugins"
SESSION = Session()
SESSION.headers["User-Agent"] = "ServerJarManager"


def response_to_file(response: Response, file: Path) -> None:
    """Writes requests.Response content to file."""
    with file.open("wb") as f:
        for chunk in response.iter_content():
            f.write(chunk)


def download_plugin(plugin: PluginInfo, destination: Path) -> None:
    """Download plugin and put it in destination"""
    url = f"{BASE_URL}/{plugin.name}/{plugin.version}.jar"
    response = SESSION.get(url)
    response.raise_for_status()
    response_to_file(response, destination)
