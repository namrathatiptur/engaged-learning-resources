from django import template

register = template.Library()

# Subtle, professional-style icons for activity rows (by category keywords)
_CATEGORY_EMOJI = (
    ("icebreaker", "🧊"),
    ("project", "📁"),
    ("discussion", "💬"),
    ("workshop", "🛠️"),
    ("presentation", "📊"),
    ("game", "🎯"),
    ("team", "🤝"),
    ("research", "🔍"),
    ("lab", "🧪"),
    ("reading", "📖"),
)


@register.filter
def activity_emoji(activity):
    if activity.category:
        name = activity.category.name.lower()
        for keyword, emoji in _CATEGORY_EMOJI:
            if keyword in name:
                return emoji
    return "📚"


MATERIAL_TYPE_EMOJI = {
    "worksheet": "📄",
    "instructions": "📋",
    "example": "💡",
    "video": "🎬",
}


@register.filter
def material_type_emoji(material_type_key):
    return MATERIAL_TYPE_EMOJI.get(material_type_key, "📎")


@register.filter
def get_item(mapping, key):
    """Lookup for dict-like objects in templates: {{ tag_apply_queries|get_item:tag.name }}"""
    if mapping is None:
        return ""
    try:
        return mapping.get(str(key), "")
    except AttributeError:
        return ""


@register.filter
def in_set(value, collection):
    """True if value is in collection (e.g. tag name in the set of selected tags)."""
    try:
        return value in collection
    except TypeError:
        return False
