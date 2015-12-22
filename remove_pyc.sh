#!/bin/sh
find . -type f -name '*.pyc' -not -path "./venv/*" -exec rm {} \; 
