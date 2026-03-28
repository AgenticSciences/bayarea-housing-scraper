"""SF neighborhood safety scoring.

Safety ratings are based on publicly available crime statistics
and community knowledge. These are approximate guides, not
definitive safety guarantees. Always visit in person before
signing a lease.

Scale: 1-5 (5 = safest)
"""

from __future__ import annotations

# Neighborhood → (safety_score, aliases)
# Aliases are used for fuzzy matching against listing text
NEIGHBORHOODS: dict[str, tuple[int, list[str]]] = {
    # ⭐⭐⭐⭐⭐ (5/5) — Safest
    "Sunset": (5, ["sunset", "outer sunset", "inner sunset", "日落", "parkside"]),
    "Noe Valley": (5, ["noe valley", "noe"]),
    "Bernal Heights": (5, ["bernal heights", "bernal"]),
    "Marina": (5, ["marina", "cow hollow"]),
    "Pacific Heights": (5, ["pacific heights", "pac heights"]),
    "Presidio": (5, ["presidio", "baker beach"]),
    "West Portal": (5, ["west portal"]),
    "Forest Hill": (5, ["forest hill"]),
    "Glen Park": (5, ["glen park"]),
    "Diamond Heights": (5, ["diamond heights"]),
    "Twin Peaks": (5, ["twin peaks"]),
    "Laurel Heights": (5, ["laurel heights"]),
    "Sea Cliff": (5, ["sea cliff", "seacliff"]),
    "Lake Merced": (5, ["lake merced"]),
    "Stonestown": (5, ["stonestown"]),
    "Miraloma Park": (5, ["miraloma"]),
    "St. Francis Wood": (5, ["st. francis wood", "saint francis"]),

    # ⭐⭐⭐⭐ (4/5) — Safe
    "Richmond": (4, ["richmond", "inner richmond", "outer richmond"]),
    "Upper Haight": (4, ["upper haight", "haight ashbury", "haight"]),
    "Alamo Square": (4, ["alamo square", "nopa"]),
    "Daly City": (4, ["daly city"]),
    "Castro": (4, ["castro", "upper market"]),
    "Nob Hill": (4, ["nob hill"]),
    "Russian Hill": (4, ["russian hill"]),
    "Ingleside": (4, ["ingleside"]),
    "Visitacion Valley": (4, ["visitacion valley", "visitacion"]),
    "South San Francisco": (4, ["south san francisco", "south sf", "ssf"]),
    "Cole Valley": (4, ["cole valley"]),
    "Hayes Valley": (4, ["hayes valley"]),
    "Duboce Triangle": (4, ["duboce"]),
    "Potrero Hill": (4, ["potrero hill", "potrero"]),

    # ⭐⭐⭐ (3/5) — Moderate
    "SOMA": (3, ["soma", "south beach", "south of market", "mission bay"]),
    "Mission (Valencia)": (3, ["mission", "valencia", "dolores"]),
    "North Beach": (3, ["north beach", "telegraph hill"]),
    "Portola": (3, ["portola"]),
    "Excelsior": (3, ["excelsior"]),
    "Financial District": (3, ["financial district", "fidi"]),
    "Chinatown": (3, ["chinatown"]),
    "Lower Haight": (3, ["lower haight"]),
    "Dogpatch": (3, ["dogpatch"]),
    "Bayview": (3, ["bayview", "hunters point"]),
    "Outer Mission": (3, ["outer mission"]),

    # ⭐⭐ (2/5) — Caution
    "Tenderloin Adjacent": (2, ["lower nob hill", "civic center", "un plaza"]),
    "Mid-Market": (2, ["mid-market", "mid market"]),
    "Western Addition (South)": (2, ["western addition"]),

    # ⭐ (1/5) — Avoid
    "Tenderloin": (1, ["tenderloin"]),
    "6th Street Corridor": (1, ["6th street", "sixth street"]),
}


class SafetyScorer:
    """Score neighborhoods based on safety data."""

    def __init__(self, neighborhoods: dict | None = None):
        self.neighborhoods = neighborhoods or NEIGHBORHOODS

    def score(self, *texts: str) -> int:
        """
        Score safety from listing text(s). Returns 0 if no neighborhood matched.

        Args:
            *texts: Title, location, URL, etc. to search for neighborhood names.

        Returns:
            Safety score 0-5 (0 = unknown).
        """
        score, _ = self.score_with_name(*texts)
        return score

    def score_with_name(self, *texts: str) -> tuple[int, str | None]:
        """
        Score safety and return matched neighborhood name.

        Returns:
            Tuple of (score, neighborhood_name). (0, None) if no match.
        """
        combined = " ".join(texts).lower()

        # Check each neighborhood's aliases
        best_score = 0
        best_name = None
        for name, (score, aliases) in self.neighborhoods.items():
            for alias in aliases:
                if alias in combined:
                    # Return the most specific match (longest alias)
                    if best_name is None or len(alias) > len(best_name):
                        best_score = score
                        best_name = name
                    elif score < best_score:
                        # If we find a less safe area, use that (conservative)
                        best_score = score
                        best_name = name

        return best_score, best_name

    def get_all_ratings(self) -> dict[str, int]:
        """Return all neighborhoods with their safety scores."""
        return {name: score for name, (score, _) in self.neighborhoods.items()}

    def get_safest(self, min_score: int = 4) -> list[str]:
        """Return neighborhood names with safety >= min_score."""
        return [
            name for name, (score, _) in self.neighborhoods.items()
            if score >= min_score
        ]
