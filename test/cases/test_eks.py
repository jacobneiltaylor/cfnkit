from cfnkit.builders.discovery import get_builder_entry_point
from support.helpers import (
    load_test_eks_template,
    matrix_parametrize,
    assert_equivalent,
)


def _mkargs(name: str, karpenter: bool, boundaries: bool) -> dict[str, dict]:
    return {
        "kwargs": {"enable_karpenter": karpenter, "provide_boundaries": boundaries},
        "expect": load_test_eks_template(name),
    }


TEST_MATRIX = {
    name: _mkargs(name, bool(idx & 1), bool(idx & 2))
    for idx, name in enumerate(
        (
            "default",
            "karpenter",
            "boundaries",
            "all",
        )
    )
}


@matrix_parametrize(TEST_MATRIX)
def test_eks_template_builder(kwargs: dict, expect: dict):
    builder_entry_point = get_builder_entry_point("eks")
    builder = builder_entry_point.construct(**kwargs)
    assert getattr(builder, "enable_karpenter") == kwargs["enable_karpenter"]
    assert getattr(builder, "provide_boundaries") == kwargs["provide_boundaries"]
    template = builder.build_template()
    assert_equivalent(template.to_dict(), expect)
