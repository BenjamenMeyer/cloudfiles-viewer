#!/bin/bash
RCBU_PYLINTRC='conf/pylintrc'

# Run pylint on the API
pylint rcbu --rcfile=${RCBU_PYLINTRC}
# Run pylint on the viewer
pylint src --rcfile=${RCBU_PYLINTRC}

