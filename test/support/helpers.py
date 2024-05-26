import os
import json
from typing import Any

import json.scanner
from pytest import mark
from deepdiff import DeepDiff

from support import constants


def get_test_rootdir():
    return os.path.dirname(__file__)


def open_test_data_file(subdir, filename):
    return open(os.path.join(get_test_rootdir(), constants.FILE_DIR, subdir, filename))


def load_test_json_file(subdir, name):
    filename = f"{name}.json"
    with open_test_data_file(subdir, filename) as datafile:
        return json.load(datafile)


def load_test_eks_template(name: str) -> dict:
    return load_test_json_file(constants.EKS_TEMPLATE_DIR, name)


def load_test_vpc_template(name: str) -> dict:
    return load_test_json_file(constants.VPC_TEMPLATE_DIR, name)


def matrix_parametrize(matrix: dict[str, dict[str, Any]]):
    def decorator(func):
        expected_argnames = set(tuple(matrix.values())[0].keys())

        for key, value in matrix.items():
            current_argnames = set(value.keys())
            if current_argnames != expected_argnames:
                actual = ",".join(current_argnames)
                expected = ",".join(expected_argnames)
                raise ValueError(
                    f"matrix item {key} has args ({actual}) inconsistent with reference ({expected})"
                )

        test_ids = tuple(matrix.keys())
        argnames = tuple(expected_argnames)

        argvalues = tuple(
            [item[argname] for argname in argnames]
            for item in [matrix[test_id] for test_id in test_ids]
        )

        return mark.parametrize(
            argnames,
            argvalues,
            ids=test_ids,
        )(func)

    return decorator


def compare_objects(a, b):
    diff = DeepDiff(a, b, ignore_order=True)
    return len(dict(diff)) == 0, diff


def assert_equivalent(actual, expected):
    result, diff = compare_objects(actual, expected)
    assert result, f"difference detected: {json.dumps(diff)}"
