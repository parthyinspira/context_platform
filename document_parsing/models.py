from dataclasses import dataclass


@dataclass(frozen=True)
class Section:
    """One structural section of a parsed document.

    `heading` and `level` are `None` for the fallback section emitted when a
    document has no detected heading structure.
    """

    heading: str | None
    level: int | None
    text: str
    order: int
