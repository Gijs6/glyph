import re
import secrets
import string
from datetime import datetime, timedelta, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

ID_LENGTH = 8

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def generate_id():
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(ID_LENGTH))


def generate_token():
    return secrets.token_urlsafe(24)


def now():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)

    email = db.Column(db.String(255), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=True)
    password_revoked_at = db.Column(db.DateTime, nullable=True)

    role = db.Column(db.String(50), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=now, nullable=False)

    @validates("email")
    def validate_email(self, key, value):
        value = (value or "").strip().lower()
        if not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address.")
        return value

    @property
    def is_admin(self):
        return self.role == "admin"

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Your password must be at least 8 characters.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class PasswordResetToken(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)
    token = db.Column(
        db.String(64), unique=True, nullable=False, default=generate_token
    )

    user_id = db.Column(db.String(ID_LENGTH), db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("reset_tokens", lazy=True))

    created_at = db.Column(db.DateTime, default=now, nullable=False)
    expires_at = db.Column(
        db.DateTime, default=lambda: now() + timedelta(hours=1), nullable=False
    )
    used = db.Column(db.Boolean, default=False, nullable=False)

    def is_valid(self):
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return not self.used and now() < expires

    def mark_used(self):
        self.used = True


class Page(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)

    author_id = db.Column(
        db.String(ID_LENGTH), db.ForeignKey("user.id"), nullable=False
    )
    author = db.relationship("User", backref=db.backref("pages", lazy="dynamic"))

    parent_id = db.Column(db.String(ID_LENGTH), db.ForeignKey("page.id"), nullable=True)
    parent = db.relationship(
        "Page", remote_side=[id], backref=db.backref("children", lazy="dynamic")
    )

    slug = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    meta_description = db.Column(db.String(300), nullable=True)
    is_homepage = db.Column(db.Boolean, default=False, nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=now, nullable=False)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now, nullable=False)

    @validates("slug")
    def validate_slug(self, key, value):
        value = (value or "").strip().lower()
        if not SLUG_RE.match(value):
            raise ValueError(
                "A slug can only contain lowercase letters, digits and hyphens."
            )
        return value

    @validates("parent_id")
    def validate_parent_id(self, key, value):
        if value and self.id and value == self.id:
            raise ValueError("A page can't be its own parent.")
        return value

    @property
    def edited(self):
        return (self.updated_at - self.created_at) > timedelta(seconds=1)

    @property
    def status_label(self):
        if self.is_archived:
            return "archived"
        if not self.is_active:
            return "inactive"
        return "live"

    @property
    def ancestors(self):
        chain = []
        seen = {self.id}
        page = self.parent
        while page is not None and page.id not in seen:
            chain.insert(0, page)
            seen.add(page.id)
            page = page.parent
        return chain

    @property
    def path(self):
        return "/".join([page.slug for page in self.ancestors] + [self.slug])

    @property
    def href(self):
        return f"/{self.path}.html"

    @property
    def is_live(self):
        return self.status_label == "live"


class Block(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)

    page_id = db.Column(db.String(ID_LENGTH), db.ForeignKey("page.id"), nullable=False)
    page = db.relationship(
        "Page",
        backref=db.backref(
            "blocks",
            lazy="dynamic",
            order_by="Block.position",
            cascade="all, delete-orphan",
        ),
    )

    type = db.Column(db.String(50), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    data = db.Column(db.JSON, nullable=False, default=dict)

    created_at = db.Column(db.DateTime, default=now, nullable=False)


class Menu(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)

    name = db.Column(db.String(100), nullable=False)

    created_at = db.Column(db.DateTime, default=now, nullable=False)


class MenuItem(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)

    menu_id = db.Column(db.String(ID_LENGTH), db.ForeignKey("menu.id"), nullable=False)
    menu = db.relationship(
        "Menu",
        backref=db.backref(
            "items",
            lazy="dynamic",
            order_by="MenuItem.position",
            cascade="all, delete-orphan",
        ),
    )

    label = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)

    page_id = db.Column(db.String(ID_LENGTH), db.ForeignKey("page.id"), nullable=True)
    page = db.relationship("Page")
    url = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=now, nullable=False)

    @property
    def href(self):
        return self.url if self.url else self.page.href

    @property
    def is_exported(self):
        return bool(self.url) or self.page.is_live


class Setting(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
