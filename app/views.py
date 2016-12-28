"""Views for Flask microblog app."""

from flask import render_template, flash, redirect, \
    session, url_for, request, g
import flask_login
import datetime
from app import app, db, lm, oid
from .forms import LoginForm, EditForm
from .models import User

#                                                     _
#   _   ,_   ,_   _,_ ,_      /_  __,   ,__,   __/   //  _   ,_   ,
# _(/__/ (__/ (__(_/_/ (_   _/ (_(_/(__/ / (__(_/(__(/__(/__/ (__/_)_


@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 page."""
    db.session.rollback()
    return render_template('500.html'), 500


#    _
#   //  _,_ __   .  ,__,
# _(/__(_/_(_/__/__/ / (_
#          _/_
#         (/

@app.before_request
def before_request():
    """Keep the current user up-to-date by using flask_login."""
    g.user = flask_login.current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@lm.user_loader
def load_user(id):
    """Return the user object."""
    return User.query.get(int(id))


@oid.after_login
def after_login(resp):
    """Handle login after OpenID is authorized.

    Perform sanity check on email. If user already exists, log them in,
    otherwise create a new user in the database and log them in.

    Lastly, redirect the user to their next page or back to the index.
    """
    if resp.email is None or resp.email == '':
        flash('Invalid login. Try again, sucker!')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nn = resp.nickname
        if nn is None or nn == '':
            nn = resp.email.split('@')[0]
        # Uniquify
        nn = User.make_unique_nickname(nn)
        # Create new user
        user = User(nickname=nn, email=resp.email)
        db.session.add(user)
        db.session.commit()
        db.session.add(user.follow(user))  # make the user follow him/herself
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    flask_login.login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    """Log the user out, then redirect back to the homepage."""
    flask_login.logout_user()
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """Login view."""
    if g.user is not None and g.user.is_authenticated:
        redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=["nickname", "email"])
    return render_template('login.html',
                           title='Log in silly!',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


#                          _
#   ,_    ,_   _,_ /)  .  //  _
#  _/_)__/ (__(_/_//__/__(/__(/_
#  /            _/
# /             /)
#               `

@app.route('/u/<name>')
@flask_login.login_required
def user(name):
    """Profile page."""
    user = User.query.filter_by(nickname=name).first()
    if user is None:
        flash('User {0} not found'.format(name))
        return redirect(url_for('index'))
    posts = [
        {'author': user, 'body': 'Test post 1'},
        {'author': user, 'body': 'Test post 2'}
    ]
    return render_template('user.html',
                           user=user,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@flask_login.login_required
def edit():
    """Edit Profile page."""
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html',
                           form=form)


@app.route('/follow/<nickname>')
def follow(nickname):
    """Follow a user with the specified nickname."""
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User {0} wasn\'t found'.format(nickname))
        return redirect(url_for('index'))
    if g.user.is_following(user):
        # already following
        flash('User {0} is already being followed'.format(nickname))
        return redirect(url_for('index'))
    # follow the user
    u = g.user.follow(user)
    if u is None:
        flash('Can\'t follow user {0}'.format(nickname))
        return redirect(url_for('index'))
    db.session.add(u)
    db.session.commit()
    flash('You are now following user {0}'.format(nickname))
    return redirect(url_for('user', name=nickname))


@app.route('/unfollow/<nickname>')
def unfollow(nickname):
    """Unfollow a user with the specified nickname."""
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User {0} not found.'.format(nickname))
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow {0}'.format(nickname))
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following {0}'.format(nickname))
    return redirect(url_for('user', name=nickname))


#                      _  ,_
#   .  ,__,   __/   __/ )/
# _/__/ / (__(_/(__(/__/(_


@app.route('/')
@app.route('/index')
@flask_login.login_required
def index():
    """Site index."""
    user = flask_login.current_user
    posts = [  # fake array of posts
        {
            'author': {'nickname': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'nickname': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', user=user, title="Yo yo yo",
                           posts=posts)
