"""Microblog unit tests."""

import pytest
import decorator
import os
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from datetime import datetime, timedelta
from config import basedir
from app import app, db
from app.models import User, Post


#           _  ,_
#    /)  ._/ )/ -/-      ,_   _   ,
#  _//__/_ _/(__/__(_/__/ (__(/__/_)_
# _/
# /)
# `


@pytest.fixture
def setup():
    """Setup test fixture.

    Sets Flask application config options, and creates a database.
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(
        os.path.join(basedir, 'test.db'))
    myapp = app.test_client()
    db.create_all()
    return myapp


def td(func):
    """Teardown decorator for test functions.

    Removes database session.
    """
    def myfunc(func, *args, **kwargs):
        try:
            r = func(*args, **kwargs)
        finally:
            db.session.remove()
            db.drop_all()
        return r
    return decorator.decorator(myfunc, func)


#  -/- _   ,   -/- ,
# _/__(/__/_)__/__/_)_


def test_avatar():
    """Test avatar function in User model class."""
    u = User(nickname='john', email='john@example.com')
    avatar = u.avatar(128)
    expected = ('http://www.gravatar.com/avatar/'
                'd4c74594d841139328695756648b6bd6')
    assert avatar[0:len(expected)] == expected


@td
def test_make_unique_nickname(setup):
    """Test unique user nickname creation."""
    # Create single user
    u = User(nickname='john', email='john@example.com')
    db.session.add(u)
    db.session.commit()

    # Test make_unique_nickname() func
    nickname = User.make_unique_nickname('john')
    assert nickname != 'john'

    # Create a second user with the new nickname
    u = User(nickname=nickname, email='susan@example.com')
    db.session.add(u)
    db.session.commit()

    # Create a second john user
    nickname2 = User.make_unique_nickname('john')

    # Shouldn't equal the original, nor the second user
    assert nickname2 != 'john'
    assert nickname2 != nickname

    # Create fresh nickname and assure there's no issue
    assert User.make_unique_nickname('terry') == 'terry'


@td
def test_follow(setup):
    """Test the following feature db model."""
    # Setup two users
    u1 = User(nickname='john', email='john@example.com')
    u2 = User(nickname='susan', email='susan@example.com')
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()
    # they shouldn't be following anyone
    assert u1.is_following(u2) == 0
    assert u2.is_following(u1) == 0
    # unfollowing should return None
    assert u1.unfollow(u2) is None
    assert u2.unfollow(u1) is None

    # Follow a user
    u = u1.follow(u2)
    db.session.add(u)
    db.session.commit()
    assert u1.follow(u2) is None     # try following again
    assert u1.is_following(u2) == 1  # now following u2
    assert u2.is_following(u1) == 0  # not the other way around
    assert u1.followed.count() == 1
    assert u1.followed.first().nickname == 'susan'
    assert u2.followers.count() == 1
    assert u2.followers.first().nickname == 'john'

    # Unfollow a user
    u = u1.unfollow(u2)
    assert u is not None
    db.session.add(u)
    db.session.commit()
    assert not u1.is_following(u2)
    assert u1.followed.count() == 0
    assert u2.followers.count() == 0
    assert u1.unfollow(u2) is None


@td
def test_follow_posts(setup):
    """Get posts of followed users, sorted by date."""
    # make four users
    u1 = User(nickname='john', email='john@example.com')
    u2 = User(nickname='susan', email='susan@example.com')
    u3 = User(nickname='mary', email='mary@example.com')
    u4 = User(nickname='david', email='david@example.com')
    db.session.add(u1)
    db.session.add(u2)
    db.session.add(u3)
    db.session.add(u4)
    # make four posts
    utcnow = datetime.utcnow()
    p1 = Post(body="post from john", author=u1,
              timestamp=utcnow + timedelta(seconds=1))
    p2 = Post(body="post from susan", author=u2,
              timestamp=utcnow + timedelta(seconds=2))
    p3 = Post(body="post from mary", author=u3,
              timestamp=utcnow + timedelta(seconds=3))
    p4 = Post(body="post from david", author=u4,
              timestamp=utcnow + timedelta(seconds=4))
    db.session.add(p1)
    db.session.add(p2)
    db.session.add(p3)
    db.session.add(p4)
    db.session.commit()
    # setup the followers
    u1.follow(u1)  # john follows himself
    u1.follow(u2)  # john follows susan
    u1.follow(u4)  # john follows david
    u2.follow(u2)  # susan follows herself
    u2.follow(u3)  # susan follows mary
    u3.follow(u3)  # mary follows herself
    u3.follow(u4)  # mary follows david
    u4.follow(u4)  # david follows himself
    db.session.add(u1)
    db.session.add(u2)
    db.session.add(u3)
    db.session.add(u4)
    db.session.commit()
    # check the followed posts of each user
    f1 = u1.followed_posts().all()
    f2 = u2.followed_posts().all()
    f3 = u3.followed_posts().all()
    f4 = u4.followed_posts().all()
    assert len(f1) == 3
    assert len(f2) == 2
    assert len(f3) == 2
    assert len(f4) == 1
    assert f1 == [p4, p2, p1]
    assert f2 == [p3, p2]
    assert f3 == [p4, p3]
    assert f4 == [p4]
