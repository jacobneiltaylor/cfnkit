from functools import cache
from cfnkit.resources import get_entry_points
from cfnkit.datastructures import BuilderEntryPoint


@cache
def get_builder_entry_points():
    entry_points = get_entry_points("cfnkit.builder")

    return [
        BuilderEntryPoint.from_entry_point(entry_point) for entry_point in entry_points
    ]


def get_builder_entry_point(name: str):
    entry_points = get_builder_entry_points()

    for entry_point in entry_points:
        if name == entry_point.name:
            return entry_point

    raise KeyError(f"{name} not found in entry points")
