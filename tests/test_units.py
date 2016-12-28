"""Microblog unit tests."""

import pytest
import decorator
import os
import unittest
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from config import basedir
from app import app, db
from app.models import User


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
