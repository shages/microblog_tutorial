"""Database models."""

import hashlib
from app import db


class User(db.Model):
    """User object."""

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140), unique=False)
    last_seen = db.Column(db.DateTime)

    @staticmethod
    def make_unique_nickname(nickname):
        """Convert requested nickname into a uniquified one.

        Uses version counter to uniquify. For example:

        make_unique_nickname('Charles') -> 'Charles'
        make_unique_nickname('Charles') -> 'Charles2'
        make_unique_nickname('Charles') -> 'Charles3'
        """
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = '{nn}.{ver}'.format(nn=nickname, ver=version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    def avatar(self, size):
        """Get avatar from Gravatar service."""
        return 'http://www.gravatar.com/avatar/{md5}?d=mm&s={size}'.format(
            size=size,
            md5=hashlib.md5(self.email.encode('utf-8')).hexdigest()
        )

    @property
    def is_authenticated(self):
        """User is authenticated."""
        return True

    @property
    def is_active(self):
        """User is still active."""
        return True

    @property
    def is_anonymous(self):
        """User is anonymous."""
        return False

    def get_id(self):
        """Return db id of the user."""
        try:
            return unicode(self.id)  # python2
        except NameError:
            return str(self.id)  # python3

    def __repr__(self):
        """Representation of user."""
        return '<User {0!r}>'.format(self.nickname)


class Post(db.Model):
    """User post object."""

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        """Representation of post."""
        return '<Post {0!r}>'.format(self.body)
