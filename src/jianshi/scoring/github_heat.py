from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class GithubHeatInput:
    stars: int
    forks: int
    age_days: float
    push_age_days: float
    recent_stars_per_day: float | None = None

def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))

def score_github_heat(x: GithubHeatInput) -> dict[str, float]:
    stars=max(0,x.stars)
    forks=max(0,x.forks)
    age=max(1.0,x.age_days)
    popularity=_clamp(100*math.log(stars+1)/math.log(100000+1))
    lifetime=_clamp(100*math.log(stars/max(age,7.0)+1)/math.log(1000+1))
    freshness=_clamp(100-max(0.0,x.push_age_days)*5)
    recency=_clamp(100-age/1.8)
    fork_score=_clamp((forks/stars)*500 if stars else 0)
    static=(popularity*.25+lifetime*.35+freshness*.20+recency*.10+fork_score*.10)
    recent=0.0
    if x.recent_stars_per_day is not None:
        recent=_clamp(100*math.log(max(0.0,x.recent_stars_per_day)+1)/math.log(1000+1))
        heat=static*.55+recent*.45
    else:
        heat=static
    return {
        "popularity":round(popularity,2),
        "lifetime_velocity":round(lifetime,2),
        "freshness":round(freshness,2),
        "recency":round(recency,2),
        "fork_score":round(fork_score,2),
        "static_heat":round(static,2),
        "recent_velocity":round(recent,2),
        "heat":round(heat,2),
    }
