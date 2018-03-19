#!/bin/sh

echo "out"
YAML_FILE="$3/app.yaml"
echo "app.yaml contents" > "$YAML_FILE"
echo "service-yaml path: $1" 1>&2
echo "app-dir path: $2" 1>&2
exit 0
