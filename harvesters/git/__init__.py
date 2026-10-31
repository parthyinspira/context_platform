"""Git harvester package.

`GitHarvester` (KAN-78) registers for source type `"git"` and implements
`connect`/`discover`/`profile`/`plan` plus `harvest()`, which delegates to
`harvest_git()` (KAN-80) for the actual sparse fetch. `normalize()` and
`validate()` remain not-yet-started follow-up work.
"""
from __future__ import annotations

from harvesters.git.harvester import GitHarvester
from harvesters.git.sparse_fetch import GitHarvestResult, harvest_git

__all__ = ["GitHarvester", "GitHarvestResult", "harvest_git"]
