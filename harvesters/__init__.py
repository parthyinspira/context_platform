"""Harvester base class, value types and the source.type plugin registry.

Concrete harvester packages (one per source type, e.g. `harvesters/git/`)
register themselves by importing `harvesters.registry.register_harvester`
and applying it to their `Harvester` subclass. As each concrete package is
added (starting with the Git harvester in a later story), import it here so
registration happens on `import harvesters`.
"""
