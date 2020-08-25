#!/bin/bash

set -euxo pipefail

# get latest version number from https://cloud.google.com/sdk/docs/downloads-versioned-archives
# or view version number on the website: https://cloud.google.com/sdk/docs/quickstart-linux
#
# https://storage.cloud.google.com/cloud-sdk-release
#
# gsutil ls -l gs://cloud-sdk-release/for_packagers/linux > list.txt

VERSION=$1
SDK_TESTS=google-cloud-sdk-tests_$VERSION.orig.tar.gz
SDK=google-cloud-sdk_$VERSION.orig.tar.gz

if [ ! -f "$SDK_TESTS" ]; then
  gsutil cp gs://cloud-sdk-release/for_packagers/linux/$SDK_TESTS .
else
  echo "$SDK_TESTS exists"
fi

if [ ! -f "$SDK" ]; then
  gsutil cp gs://cloud-sdk-release/for_packagers/linux/$SDK .
else
    echo "$SDK exists"
fi

echo "Updating google-cloud-sdk"
rm -rf google-cloud-sdk

tar -xzf google-cloud-sdk_$VERSION.orig.tar.gz
tar -xzf google-cloud-sdk-tests_$VERSION.orig.tar.gz

# Over GitHub 100MB file limit
rm google-cloud-sdk/bin/anthoscli

gsutil ls -l gs://cloud-sdk-release/for_packagers/linux > list.txt
