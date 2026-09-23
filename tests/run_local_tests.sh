#!/bin/bash

# run local tests on a Pi or Multicam box

# Copyright (c) Mark McIntyre

here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

source ~/vRMS/bin/activate
[ "$(which pytest)" == "" ] && pip install pytest pytest-cov
SRCDIR=$here/..
export PYTHONPATH=$SRCDIR:$PYTHONPATH
pytest
