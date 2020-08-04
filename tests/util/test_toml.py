import pytest  # noqa

import util.toml as toml


class TestToml:
    def test_get_project_meta(self):
        assert toml._get_project_meta(pyproj_path="/bad/path/pyproject.toml") == {}
