from functools import cache
import importlib.resources as res
import importlib.metadata as meta


@cache
def get_package(name: str):
    return res.files(name)


@cache
def get_entry_points(group: str):
    return meta.entry_points(group=group)


def get_package_file(package_name: str, filename: str):
    return get_package(package_name).joinpath(filename)


def get_package_file_bytes(package_name: str, filename: str):
    file = get_package_file(package_name, filename)
    return file.read_bytes()
