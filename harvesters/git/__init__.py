"""Git harvester package (KAN-78): registers `GitHarvester` for source type `"git"`."""
from __future__ import annotations

from harvesters.git.harvester import GitHarvester

__all__ = ["GitHarvester"]
