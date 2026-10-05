"""
Cover images for activity list cards.

Default: a stable image per activity from a small set of education-themed Unsplash URLs
(images.unsplash.com), via ``activity.id % len(urls)``.

Themed override: when title, description, slug, category, or tags suggest a scavenger hunt,
outdoor group activity, puzzle-solving activity, or a civics lesson that mentions both
religion and government, use a matching Unsplash image from the same source (Unsplash License).
"""

from __future__ import annotations

from typing import List, Optional

_URL_Q = "?auto=format&fit=crop&w=800&h=600&q=80"

# Person holding a map: scavenger / treasure hunt / clues (Natalie, Unsplash)
_IMAGE_SCAVENGER_MAP = (
    f"https://images.unsplash.com/photo-1470506926202-05d3fca84c9a{_URL_Q}"
)
# Jigsaw puzzle: collaborative problem-solving (Fabian Kühne, Unsplash)
_IMAGE_PUZZLE = f"https://images.unsplash.com/photo-1601063987324-7b482964872b{_URL_Q}"
# Group outdoors / trail: hiking & team activities (Unsplash)
_IMAGE_OUTDOOR_GROUP = (
    f"https://images.unsplash.com/photo-1529333166437-7750a6dd5a70{_URL_Q}"
)
# Seminar / group discussion — civics & social-systems lessons (college-age context)
_IMAGE_CIVICS_SEMINAR = (
    f"https://images.unsplash.com/photo-1531482615713-2afd69097998{_URL_Q}"
)

_EDUCATION_IMAGES: List[str] = [
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1529390079861-591de354faf5?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1543269865-cbf427effbad?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=800&h=600&q=80",
    "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?auto=format&fit=crop&w=800&h=600&q=80",
]


def _haystack_lower(activity) -> str:
    parts: List[str] = []
    if getattr(activity, "title", None):
        parts.append(activity.title)
    if getattr(activity, "description", None):
        parts.append(activity.description)
    if getattr(activity, "slug", None):
        parts.append(activity.slug.replace("-", " "))
    cat = getattr(activity, "category", None)
    if cat is not None and getattr(cat, "name", None):
        parts.append(cat.name)
    # List view prefetches tags; detail/other callers may still work with one query.
    for t in activity.tags.all():
        parts.append(t.name)
    return " ".join(parts).lower()


def _themed_tile_url(hay: str) -> Optional[str]:
    """Return a themed tile URL or None to use the default pool."""
    # Civics / comparative systems (religion + government in one lesson, incl. “governance”)
    if "religion" in hay and ("government" in hay or "governance" in hay):
        return _IMAGE_CIVICS_SEMINAR
    # HR / admissions-style copy often mentions "orientation" or "team"; keep the
    # stable id-based pool image (what showed before themed overrides).
    if any(
        needle in hay
        for needle in (
            "recruitment",
            "recruiting",
            "recruit ",
        )
    ):
        return None
    # Scavenger / treasure / clues: map photo (avoid bare "hunt", too broad)
    if any(
        needle in hay
        for needle in (
            "scavenger",
            "treasure hunt",
            "treasure-hunt",
            "clue",
            "clues",
        )
    ):
        return _IMAGE_SCAVENGER_MAP
    # Puzzle / collaborative problem-solving
    if any(
        needle in hay
        for needle in (
            "puzzle",
            "jigsaw",
            "riddle",
            "brain teaser",
            "brain-teaser",
        )
    ):
        return _IMAGE_PUZZLE
    # Outdoor group / trail activities
    outdoor_signals = (
        "hiking",
        "group hike",
        "hike,",
        "hike.",
        "hike ",
        " hiker",
        "forest path",
        "trail ",
        " team building",
        "field trip",
        "outdoor orientation",
        "field orientation",
        "outdoor group",
        "outdoor team",
        "outdoor activity",
        "outdoor class",
        "outside classroom",
        "campus walk",
        "nature walk",
    )
    if any(s in hay for s in outdoor_signals):
        return _IMAGE_OUTDOOR_GROUP
    if "outdoor" in hay and any(
        w in hay for w in ("group", "team", "class", "campus", "walk", "activity")
    ):
        return _IMAGE_OUTDOOR_GROUP
    return None


def tile_image_url(activity) -> str:
    hay = _haystack_lower(activity)
    themed = _themed_tile_url(hay)
    if themed is not None:
        return themed
    pool = _EDUCATION_IMAGES
    idx = activity.id % len(pool)
    return pool[idx]
