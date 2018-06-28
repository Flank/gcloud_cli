# get latest version number from https://cloud.google.com/sdk/downloads
#
# https://storage.cloud.google.com/cloud-sdk-release
#
# gsutil ls -l gs://cloud-sdk-release/for_packagers/linux > list.txt

VERSION=201.0.0
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
