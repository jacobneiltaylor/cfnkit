from inspect import signature
from importlib.metadata import EntryPoint
from dataclasses import dataclass
from typing import Type

from cfnkit.builders.builder import Builder


@dataclass
class BuilderEntryPoint:
    name: str
    module: str
    attr: str
    klass: Type[Builder]

    @property
    def init_signature(self):
        return signature(self.klass.__init__)

    def construct(self, *args, **kwargs) -> Builder:
        return self.klass(*args, **kwargs)

    @classmethod
    def from_entry_point(cls, entry_point: EntryPoint):
        return cls(
            entry_point.name,
            entry_point.module,
            entry_point.attr,
            entry_point.load(),
        )
