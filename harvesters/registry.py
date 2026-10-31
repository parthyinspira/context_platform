"""Plugin registry selecting a `Harvester` implementation by `source.type`.

Registration is explicit (a decorator applied to the harvester class), not
filesystem or entry-point based: each harvester package imports and registers
itself, and `harvesters/__init__.py` imports every known package so
registration happens once, on first import of `harvesters`.
"""
from __future__ import annotations

from typing import Type

from harvesters.base import Harvester

_REGISTRY: dict[str, Type[Harvester]] = {}


class UnknownSourceTypeError(LookupError):
    """Raised when no harvester is registered for a given `source.type`."""

    def __init__(self, source_type: str):
        super().__init__(
            f"no harvester registered for source type '{source_type}'; "
            f"known types: {sorted(_REGISTRY)}"
        )
        self.source_type = source_type


def register_harvester(source_type: str):
    """Class decorator registering a `Harvester` subclass for `source_type`."""

    def decorator(cls: Type[Harvester]) -> Type[Harvester]:
        if not (isinstance(cls, type) and issubclass(cls, Harvester)):
            raise TypeError(f"{cls!r} must be a subclass of Harvester")
        existing = _REGISTRY.get(source_type)
        if existing is not None and existing is not cls:
            raise ValueError(
                f"source type '{source_type}' is already registered to "
                f"{existing.__module__}.{existing.__qualname__}"
            )
        _REGISTRY[source_type] = cls
        return cls

    return decorator


def get_harvester(source_type: str) -> Harvester:
    """Return a new instance of the `Harvester` registered for `source_type`."""
    cls = _REGISTRY.get(source_type)
    if cls is None:
        raise UnknownSourceTypeError(source_type)
    return cls()


def registered_types() -> list[str]:
    """Known source types, for diagnostics and admin tooling."""
    return sorted(_REGISTRY)
