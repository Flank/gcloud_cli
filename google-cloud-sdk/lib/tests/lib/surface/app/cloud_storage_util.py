# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper class for commands which upload files to Google Cloud Storage."""

import hashlib

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base

storage_v1 = core_apis.GetMessagesModule('storage', 'v1')


def GetSha(content):
  """A helper function to return the SHA of a string.

  Args:
    content: A string to get the SHA of.
  Returns:
    A string containing the hex digest of the SHA1 checksum of the content.
  """
  return files.Checksum(algorithm=hashlib.sha1).AddContents(content).HexDigest()


class WithGCSCalls(sdk_test_base.SdkBase):
  """A helper class used to test code that calls GCS."""

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    old_get_client_instance = core_apis.GetClientInstance
    def _MockGetClientInstance(api, version, no_http=False):
      if api == 'storage' and version == 'v1':
        return self.apitools_client
      return old_get_client_instance(api, version, no_http)
    self.StartObjectPatch(core_apis, 'GetClientInstance',
                          _MockGetClientInstance)

  def ExpectUploads(self, file_list):
    """Mocks out the upload calls for a list of files.

    This function takes care of deduplicating the files to ensure that each
    upload only happens once.

    Args:
      file_list: A list of 2-tuples containing the filename and the content of
      the file.
    """
    sha_to_size = {}
    for _, content in file_list:
      sha_to_size[GetSha(content)] = len(content)

    for sha, size in sorted(sha_to_size.iteritems()):
      self.apitools_client.objects.Insert.Expect(
          storage_v1.StorageObjectsInsertRequest(
              bucket=self._BUCKET_NAME,
              name=sha,
              object=storage_v1.Object(size=size)
          ),
          storage_v1.Object(size=size)
      )

  def ExpectList(self, file_list):
    """Mocks out the List call and sets the return value correctly.

    Args:
      file_list: A list of 2-tuples containing the filename and the content of
      the file.
    """
    objects = storage_v1.Objects(
        items=[storage_v1.Object(name=GetSha(c)) for _, c in file_list])

    self.apitools_client.objects.List.Expect(
        storage_v1.StorageObjectsListRequest(bucket=self._BUCKET_NAME),
        response=objects
    )

  def ExpectListMulti(self, file_list_list):
    """Mocks out the List call and sets the return value correctly.

    This sets up the list calls with a paginated response.

    Args:
      file_list_list: A list of lists of 2-tuples containing the filename and
      the content of the file.
    """
    page_tokens = map(str, range(len(file_list_list) - 1))
    for idx, file_list in enumerate(file_list_list):
      next_page_token = None
      if idx < len(file_list_list) - 1:
        next_page_token = page_tokens[idx]
      objects = storage_v1.Objects(
          items=[storage_v1.Object(name=GetSha(c)) for _, c in file_list],
          nextPageToken=next_page_token)

      curr_page_token = None
      if idx > 0:
        curr_page_token = page_tokens[idx-1]
      self.apitools_client.objects.List.Expect(
          storage_v1.StorageObjectsListRequest(bucket=self._BUCKET_NAME,
                                               pageToken=curr_page_token),
          response=objects
      )

  def ExpectListException(self, exception):
    """Mocks out the List call and raises the supplied exception.

    Args:
      exception: An exception to raise in the API call.
    """
    self.apitools_client.objects.List.Expect(
        storage_v1.StorageObjectsListRequest(bucket=self._BUCKET_NAME),
        response=None,
        exception=exception
    )
