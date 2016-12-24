"""Views for Flask microblog app."""

from flask import render_template, flash, redirect, \
    session, url_for, request, g
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, lm, oid
from .forms import LoginForm
from .models import User


@lm.user_loader
def load_user(id):
    """Return the user object."""
    return User.query.get(int(id))


@oid.after_login
def after_login(resp):
    """Handle login."""
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
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('hello'))


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """Login view."""
    if g.user is not None and g.user.is_authenticated:
        redirect(url_for('hello'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=["nickname", "email"])
    return render_template('login.html',
                           title='Log in silly!',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


@app.route('/')
@app.route('/index')
def hello():
    """Site index."""
    user = {'nickname': 'Charlie'}
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
