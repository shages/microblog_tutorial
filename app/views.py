"""Views for Flask microblog app."""

from flask import render_template, flash, redirect, \
    session, url_for, request, g
import flask_login
import flask_babel
import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, LANGUAGES
from app import app, db, lm, oid, babel
from .forms import LoginForm, EditForm, PostForm, SearchForm
from .models import User, Post
from .emails import follower_notification


#                     _
#   /_ __,   /_  _   //
# _/_)(_/(__/_)_(/__(/_


@babel.localeselector
def get_locale():
    """Return the locale for Babel to use."""
    return request.accept_languages.best_match(LANGUAGES.keys())


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
        g.search_form = SearchForm()
    g.locale = get_locale()


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
        flash(flask_babel.gettext('Invalid login. Try again, sucker!'))
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nn = resp.nickname
        if nn is None or nn == '':
            nn = resp.email.split('@')[0]
        # Uniquify
        nn = User.make_valid_nickname(nn)
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


#   ,    _  __,   ,_   __   /_
# _/_)__(/_(_/(__/ (__(_,__/ (_


@app.route('/search', methods=['POST'])
@flask_login.login_required
def search():
    """Submit a search query to the search_results view."""
    if g.search_form.validate_on_submit():
        return redirect(url_for('search_results',
                                query=g.search_form.search.data))
    return redirect(url_for('index'))


@app.route('/search/<query>')
@flask_login.login_required
def search_results(query):
    """Perform a search using the Whoosh search engine."""
    results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html',
                           query=query,
                           results=results)


#                          _
#   ,_    ,_   _,_ /)  .  //  _
#  _/_)__/ (__(_/_//__/__(/__(/_
#  /            _/
# /             /)
#               `

@app.route('/u/<name>')
@app.route('/u/<name>/<int:page>')
@flask_login.login_required
def user(name, page=1):
    """Profile page."""
    user = User.query.filter_by(nickname=name).first()
    if user is None:
        flash('User {0} not found'.format(name))
        return redirect(url_for('index'))
    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
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
@flask_login.login_required
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
    follower_notification(user, g.user)
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


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@flask_login.login_required
def index(page=1):
    """Site index."""
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data,
                    timestamp=datetime.datetime.utcnow(),
                    author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live')
        return redirect(url_for('index'))
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html',
                           title="Yo yo yo",
                           form=form,
                           posts=posts)
