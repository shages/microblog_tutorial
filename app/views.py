"""Views for Flask microblog app."""

from flask import render_template, flash, redirect, \
    session, url_for, request, g
import flask_login
import datetime
from app import app, db, lm, oid
from .forms import LoginForm
from .models import User


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
        # Create new user
        user = User(nickname=nn, email=resp.email)
        db.session.add(user)
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
