BLOCK_TYPES = {
    "text": {
        "label": "Text",
        "icon": "note",
        "fields": ["content"],
        "defaults": {"content": ""},
    },
    "button": {
        "label": "Button",
        "icon": "link",
        "fields": ["label", "url", "style"],
        "defaults": {"label": "", "url": "", "style": "primary"},
    },
    "image": {
        "label": "Image",
        "icon": "image",
        "fields": ["url", "alt", "caption"],
        "defaults": {"url": "", "alt": "", "caption": ""},
    },
}


def default_data(block_type):
    return dict(BLOCK_TYPES[block_type]["defaults"])


def extract_data(block_type, form):
    config = BLOCK_TYPES.get(block_type)
    if not config:
        return {}
    return {field: (form.get(field) or "").strip() for field in config["fields"]}


def block_preview(block):
    data = block.data or {}
    if block.type == "text":
        return (
            (data.get("content") or "").splitlines()[0][:80]
            if data.get("content")
            else ""
        )
    if block.type == "button":
        return data.get("label") or data.get("url") or ""
    if block.type == "image":
        return data.get("alt") or data.get("url") or ""
    return ""
