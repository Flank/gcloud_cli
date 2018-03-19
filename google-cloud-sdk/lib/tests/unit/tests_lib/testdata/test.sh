#!/bin/sh

read input
echo "$input"
echo "test output"
echo "test error" 1>&2
exit 1

