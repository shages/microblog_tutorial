from flask import render_template, flash, redirect
from app import app
from .forms import LoginForm

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for OpenID="{oid}", remember_me={rem}'.format(
              oid=form.openid.data,
              rem=str(form.remember_me.data)
        ))
        return redirect('/index')
    return render_template('login.html',
                           title='Log in silly!',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])

@app.route('/')
@app.route('/index')
def hello():
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
