"""Database models."""

import hashlib
from app import db


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('user.id')))


class User(db.Model):
    """User object."""

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140), unique=False)
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    def follow(self, other_user):
        """Follow another user."""
        if not self.is_following(other_user):
            self.followed.append(other_user)
            return self

    def unfollow(self, other_user):
        """Unfollow another user."""
        if self.is_following(other_user):
            self.followed.remove(other_user)
            return self

    def is_following(self, other_user):
        """Check if I am following the specified user."""
        return self.followed.filter(followers.c.followed_id ==
                                    other_user.id).count() > 0

    def followed_posts(self):
        """Return posts of followed users, sorted by date."""
        return Post.query.join(followers,
                               (followers.c.followed_id == Post.user_id)) \
            .filter(followers.c.follower_id == self.id) \
            .order_by(Post.timestamp.desc())

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
            new_nickname = '{nn}{ver}'.format(nn=nickname, ver=version)
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
