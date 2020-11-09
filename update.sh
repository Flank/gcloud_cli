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
SDK=google-cloud-sdk-$VERSION-linux-x86_64.tar.gz

SDK_TESTS_GS_PATH=gs://cloud-sdk-release/for_packagers/linux/$SDK_TESTS
STATUS=$(gsutil -q stat $SDK_TESTS_GS_PATH || echo 1)

if [[ $STATUS == 0 ]]; then
  if [ ! -f "$SDK_TESTS" ]; then
    gsutil cp $SDK_TESTS_GS_PATH .
  else
    echo "$SDK_TESTS exists"
  fi
else
  echo "File does not exist"
fi

if [ ! -f "$SDK" ]; then
    curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/$SDK --output $SDK
else
    echo "$SDK exists"
fi


echo "Updating google-cloud-sdk"
rm -rf google-cloud-sdk

if test -f "$SDK_TESTS"; then
    tar -xzf google-cloud-sdk-tests_$VERSION.orig.tar.gz
fi

tar -xzf google-cloud-sdk_$VERSION.orig.tar.gz

# Over GitHub 100MB file limit
rm google-cloud-sdk/bin/anthoscli

gsutil ls -l gs://cloud-sdk-release/for_packagers/linux > list.txt
