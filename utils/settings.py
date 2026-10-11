from models import Setting, db

SITE_TITLE_KEY = "site_title"
HEADER_MENU_KEY = "header_menu_id"
SITE_LANGUAGE_KEY = "site_language"

SITE_LANGUAGES = [
    ("en", "English"),
    ("nl", "Dutch"),
]


def get_setting(key, default=None):
    setting = db.session.get(Setting, key)
    return setting.value if setting else default


def set_setting(key, value):
    setting = db.session.get(Setting, key)
    if setting is None:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    else:
        setting.value = value
    db.session.commit()
