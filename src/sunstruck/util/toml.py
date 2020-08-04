import os
from typing import Dict, Optional

import tomlkit


def _get_project_meta(pyproj_path: str = "./pyproject.toml") -> Dict[str, str]:
    if os.path.exists(pyproj_path):
        with open(pyproj_path, "r") as pyproject:
            file_contents = pyproject.read()
        return tomlkit.parse(file_contents)["tool"]["poetry"]
    else:
        return {}


pkg_meta: Dict[str, str] = _get_project_meta()
project: Optional[str] = pkg_meta.get("name")
version: Optional[str] = pkg_meta.get("version")
