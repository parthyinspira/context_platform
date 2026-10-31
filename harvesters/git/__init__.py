"""Git source harvest step (KAN-80).

Only `harvest()` for Git exists so far: `connect`/`discover`/`profile`/`plan`
and registration under `get_harvester("git")` are separate, not-yet-started
stories (see `spec/changes/kan-80-git-harvest-sparse-fetch/proposal.md`).
"""
from harvesters.git.sparse_fetch import GitHarvestResult, harvest_git

__all__ = ["GitHarvestResult", "harvest_git"]
