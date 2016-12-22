from flask import render_template, flash, redirect
from app import app
from .forms import LoginForm

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html',
    title="Log in silly!",
    form=LoginForm())

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
