from typing import Any, Optional
from abc import ABC, abstractmethod

from troposphere import Template

from cfnkit.types import Parameters, Resources, Outputs, ParameterMap, ResourceMap


class Builder(ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_parameters(self) -> Parameters:
        return
        yield  # noqa

    @abstractmethod
    def get_resources(self, parameters: ParameterMap) -> Resources:
        raise NotImplementedError()

    def get_outputs(self, resources: ResourceMap) -> Outputs:
        return
        yield  # noqa

    @staticmethod
    def _get_template_kwargs(desc, meta):
        kwargs = {}

        if desc is not None:
            kwargs["description"] = desc

        if meta is not None:
            kwargs["metadata"] = meta

        return kwargs

    def build_template(
        self,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        parameters: ParameterMap = {}
        resources: ResourceMap = {}

        kwargs = self._get_template_kwargs(description, metadata)
        template = Template(**kwargs)

        for parameter in self.get_parameters():
            template.add_parameter(parameter)
            parameters[parameter.title] = parameter

        for resource in self.get_resources(parameters):
            template.add_resource(resource)
            resources[resource.title] = resource

        for output in self.get_outputs(resources):
            template.add_output(output)

        return template
