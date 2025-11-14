import subprocess
import tomllib
import pathlib

file_path = pathlib.Path.home() / ".config" / "uv" / "uv.toml"
pip_index_url = subprocess.run(
    ["pip", "config", "get", "global.index-url"],
    capture_output=True,
    text=True,
).stdout.strip()

if not file_path.exists():
    file_path.touch()

with open(file_path, "rb") as file:
    config = tomllib.load(file)

config["index"] = [{'name': 'pypi', 'url': 'https://pypi.org/simple/'}, {'name': 'wikr', 'url': pip_index_url}]

with open(file_path, "wb") as file:
    tomllib.dump(config, file)
