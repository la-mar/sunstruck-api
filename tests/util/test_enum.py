import itertools

import pytest

from util.enums import Enum, to_lower_enum


class Sparkling(str, Enum):
    TOPO = "topo chico"
    WATERLOO = "waterloo"
    LACROIX = "lacroix"


class TestEnum:
    def test_has_value_existing(self):
        assert Sparkling.has_value("topo chico") is True

    def test_has_value_missing(self):
        assert Sparkling.has_value("dr pepper") is False

    def test_has_member_existing_lower(self):
        assert Sparkling.has_member("topo") is True

    def test_has_member_existing_upper(self):
        assert Sparkling.has_member("TOPO") is True

    def test_has_member_missing(self):
        assert Sparkling.has_member("not_topo") is False

    def test_value_map(self):
        assert Sparkling.value_map() == {
            "topo chico": Sparkling.TOPO,
            "waterloo": Sparkling.WATERLOO,
            "lacroix": Sparkling.LACROIX,
        }

    def test_keys(self):
        assert Sparkling.keys() == ["TOPO", "WATERLOO", "LACROIX"]

    def test_values(self):
        assert Sparkling.values() == ["topo chico", "waterloo", "lacroix"]

    def test_members(self):
        assert Sparkling.members() == [
            Sparkling.TOPO,
            Sparkling.WATERLOO,
            Sparkling.LACROIX,
        ]

    def test_iter_class(self):
        assert list(Sparkling) == [
            Sparkling.TOPO,
            Sparkling.WATERLOO,
            Sparkling.LACROIX,
        ]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("topo chico", Sparkling.TOPO),
        ("WaterLOO", Sparkling.WATERLOO),
        ("LACROIX", Sparkling.LACROIX),
    ],
)
def test_to_lower_enum(value, expected):
    assert to_lower_enum(value, Sparkling) == expected


@pytest.mark.parametrize(
    "value,transform",
    list(
        itertools.product(
            Sparkling.values(), [str.upper, str.lower, str.capitalize, str.title]
        )
    ),
)
def test_case_sensitivity(value, transform):
    assert isinstance(Sparkling(transform(value)), Sparkling)


if __name__ == "__main__":
    pass
