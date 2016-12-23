#!/bin/bash
find ./app -name "*.py" -exec flake8 --ignore=E402,F401 {} +
