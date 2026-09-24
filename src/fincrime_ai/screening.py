"""Candidate matching against a synthetic list, never a sanctions determination."""

import re
import unicodedata

from rapidfuzz.fuzz import ratio


def normalize(name):
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", name.lower())).strip()


class EntityMatcher:
    def __init__(self, watchlist, threshold=88):
        if not 0 <= threshold <= 100:
            raise ValueError("Threshold must be 0..100")
        self.threshold = threshold
        self.candidates = []
        for w in watchlist.to_dict("records"):
            if not w["active"]:
                continue
            for name, alias in [(w["canonical_name"], False)] + [
                (s.strip(), True) for s in w["aliases"].split("|") if s.strip()
            ]:
                self.candidates.append((normalize(name), alias, w))

    def screen(self, name, country, entity_type="BUSINESS"):
        normal = normalize(name)
        if not normal or not self.candidates:
            raise ValueError("Name and active reference candidates are required")
        results = []
        for candidate, alias, w in self.candidates:
            similarity = ratio(normal, candidate)
            country_match = country == w["country"]
            context = entity_type == w["entity_type"]
            score = 0.9 * similarity + 5 * country_match + 5 * context
            results.append((score, similarity, alias, country_match, w))
        score, similarity, alias, country_match, w = max(
            results, key=lambda row: row[0]
        )
        reasons = [
            (
                "ALIAS_MATCH"
                if alias
                else "EXACT_NAME" if similarity == 100 else "FUZZY_NAME"
            )
        ]
        if not country_match:
            reasons.append("COUNTRY_MISMATCH")
        return {
            "counterparty": name,
            "matched_entity": w["canonical_name"],
            "matched_entity_id": int(w["entity_id"]),
            "name_similarity_score": round(similarity, 3),
            "alias_match": bool(alias),
            "country_match": bool(country_match),
            "screening_score": round(score, 3),
            "screening_threshold": self.threshold,
            "recommendation": "REVIEW" if score >= self.threshold else "CLEAR",
            "reason_codes": reasons,
        }
