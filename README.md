# Microblog tutorial
[![Build Status](https://travis-ci.org/shages/microblog_tutorial.svg?branch=master)](https://travis-ci.org/shages/microblog_tutorial)
[![codecov.io](https://codecov.io/gh/shages/microblog_tutorial/coverage.svg?branch=master)](https://codecov.io/gh/shages/microblog_tutorial?branch=master)

Following the [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)


## Initialization
Initialize the database
```sh
./db_util/db_create.py
./db_util/db_migrate.py
```

Start the server
```sh
./run.py
```


## Tests
Lint checks
```sh
./tests/flake.sh
```

Unit tests
```sh
pytest
```
