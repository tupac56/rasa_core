#!/bin/bash

set -e

function print_help {
    echo "Available options:"
    echo " start - Start Rasa Core server"
}

case ${1} in
    start)
        exec python serve.py
        ;;
    *)
        print_help
        ;;
esac
