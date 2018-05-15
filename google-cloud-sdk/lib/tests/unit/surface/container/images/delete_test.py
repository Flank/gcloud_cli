# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for container images delete commands."""

from __future__ import absolute_import
from __future__ import unicode_literals

from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from containerregistry.client.v2_2 import docker_session
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2
import mock
import six.moves.http_client

_REPOSITORY = 'gcr.io/project/repository'
_DIGEST_SUFFIX1 = 'sha256:' + 'a'*64
_DIGEST1 = _REPOSITORY+'@'+_DIGEST_SUFFIX1
_DIGEST_SUFFIX2 = 'sha256:' + 'b'*64
_DIGEST2 = _REPOSITORY+'@'+_DIGEST_SUFFIX2
_TAGS1 = ['v1', 'prod', 'frontend', 'latest']
_TAGS2 = ['v2', 'dev', 'backend']
_TAG_V1 = _REPOSITORY + ':v1'


class DeleteTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def _StoreDeletedTagsAndDigests(self, name, creds, transport):
    if isinstance(name, docker_name.Tag):
      self._deleted_tags.add(str(name))
    if isinstance(name, docker_name.Digest):
      self._deleted_digests.add(str(name))

  def _GetDigestForTag(self, tag_str):
    image = docker_name.Tag(tag_str)
    for digest_suffix in self._manifests:
      if image.tag in self._manifests[digest_suffix]['tag']:
        return docker_name.Digest(_REPOSITORY + '@' + digest_suffix)

  def SetUp(self):
    self._deleted_tags = set()
    self._deleted_digests = set()
    self._manifests = {}
    self._parent_digest_for_tag = {}
    registry_mock = mock.Mock()
    registry_mock.manifests = lambda: self._manifests

    self.digest_from_name_mock = self.StartObjectPatch(util,
                                                       'GetDigestFromName')
    self.digest_from_name_mock.side_effect = self._GetDigestForTag

    ctx_manager = self.StartObjectPatch(
        docker_image.FromRegistry, '__enter__')
    ctx_manager.return_value = registry_mock

    self.mock_delete = self.StartObjectPatch(
        docker_session, 'Delete')
    self.mock_delete.side_effect = self._StoreDeletedTagsAndDigests

  def Delete(self, image_names):
    return self.Run([
        'container',
        'images',
        'delete',
        '--format=disable',
        '--force-delete-tags',
    ] + image_names)

  def DeleteNoForce(self, image_names):
    return self.Run([
        'container',
        'images',
        'delete',
        '--format=disable',
    ] + image_names)

  def testDeleteDigest(self):
    self._manifests = {
        _DIGEST_SUFFIX1:
        {'tag': _TAGS1, 'timestamp': ''},
        _DIGEST_SUFFIX2:
        {'tag': _TAGS2, 'timestamp': ''}
    }
    result = resource_projector.MakeSerializable(self.Delete([_DIGEST1]))
    result_names = [i['name'] for i in result]
    self.assertEqual(len(_TAGS1) + 1, len(result))  # tags + digest
    self.assertEqual(len(_TAGS1), len(self._deleted_tags))
    for tag in _TAGS1:
      self.assertTrue(_REPOSITORY+':'+tag in result_names)
      self.AssertErrContains(tag)
      self.assertTrue(_REPOSITORY+':'+tag in self._deleted_tags)
    self.AssertErrContains(_DIGEST1)
    self.assertEqual(len(self._deleted_digests), 1)
    self.assertIn(_DIGEST1, result_names)
    self.assertIn(_DIGEST1, self._deleted_digests)

  def testDeleteDigest_Registry403(self):
    self._manifests = {_DIGEST_SUFFIX1: {'tag': _TAGS1, 'timestamp': ''}}

    self.digest_from_name_mock.side_effect = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.UNAUTHORIZED
        }), '')

    with self.assertRaises(util.UserRecoverableV2Error):
      self.Delete([_TAG_V1])

  def testDeleteDigest_Registry404(self):
    self._manifests = {_DIGEST_SUFFIX1: {'tag': _TAGS1, 'timestamp': ''}}

    self.digest_from_name_mock.side_effect = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.NOT_FOUND
        }), '')

    with self.assertRaises(util.UserRecoverableV2Error):
      self.Delete([_TAG_V1])

  def testDeleteDigest_TokenRefreshError(self):
    self._manifests = {_DIGEST_SUFFIX1: {'tag': _TAGS1, 'timestamp': ''}}

    expected_message = 'Bad status during token exchange: 403'
    exception = docker_http.TokenRefreshException(expected_message)

    self.digest_from_name_mock.side_effect = exception

    with self.assertRaises(util.TokenRefreshError):
      self.Delete([_TAG_V1])

  def testDeleteDigestByPrefix(self):
    self._manifests = {
        _DIGEST_SUFFIX1:
        {'tag': _TAGS1, 'timestamp': ''},
        _DIGEST_SUFFIX2:
        {'tag': _TAGS2, 'timestamp': ''}
    }
    digest = _REPOSITORY + '@sha256:aaa'
    result = resource_projector.MakeSerializable(self.Delete([digest]))
    result_names = [i['name'] for i in result]
    self.assertEqual(len(_TAGS1) + 1, len(result))  # tags + digest
    self.assertEqual(len(_TAGS1), len(self._deleted_tags))
    for tag in _TAGS1:
      self.assertTrue(_REPOSITORY+':'+tag in result_names)
      self.AssertErrContains(tag)
      self.assertTrue(_REPOSITORY+':'+tag in self._deleted_tags)
    self.AssertErrContains(_DIGEST1)
    self.assertEqual(len(self._deleted_digests), 1)
    self.assertIn(_DIGEST1, result_names)
    self.assertIn(_DIGEST1, self._deleted_digests)

  def testDeleteByTag(self):
    self._manifests = {
        _DIGEST_SUFFIX1:
        {'tag': _TAGS1, 'timestamp': ''},
        _DIGEST_SUFFIX2:
        {'tag': _TAGS2, 'timestamp': ''}
    }
    # Delete by tag for image w/ digest1
    result = resource_projector.MakeSerializable(self.Delete([_TAG_V1]))
    result_names = [i['name'] for i in result]
    self.assertIn(_DIGEST1, result_names)
    self.assertIn(_DIGEST1, self._deleted_digests)
    self.AssertErrContains(_DIGEST1)
    for expected_tag in _TAGS1:
      self.assertIn(_REPOSITORY + ':' + expected_tag, result_names)
      self.AssertErrContains(expected_tag)
      self.assertTrue(_REPOSITORY + ':' + expected_tag in self._deleted_tags)

  def testDeleteByTag_ImplicitLatest(self):
    self._manifests = {
        _DIGEST_SUFFIX1:
        {'tag': _TAGS1, 'timestamp': ''},
        _DIGEST_SUFFIX2:
        {'tag': _TAGS2, 'timestamp': ''}
    }
    # Delete by implicit ':latest' tag for image w/ digest1
    result = resource_projector.MakeSerializable(self.Delete([_REPOSITORY]))
    self.AssertErrContains('Implicit ":latest" tag specified: ' + _REPOSITORY)

    result_names = [i['name'] for i in result]
    self.assertIn(_DIGEST1, result_names)
    self.assertIn(_DIGEST1, self._deleted_digests)
    self.AssertErrContains(_DIGEST1)
    for expected_tag in _TAGS1:
      self.assertIn(_REPOSITORY + ':' + expected_tag, result_names)
      self.AssertErrContains(expected_tag)
      self.assertTrue(_REPOSITORY + ':' + expected_tag in self._deleted_tags)

  def testDeleteByTagNoForce(self):
    self._manifests = {
        _DIGEST_SUFFIX1: {
            'tag': _TAGS1,
            'timestamp': ''
        },
        _DIGEST_SUFFIX2: {
            'tag': _TAGS2,
            'timestamp': ''
        }
    }
    with self.assertRaises(exceptions.Error):
      self.DeleteNoForce([_TAG_V1])

  def testRepeatDeleteDigestAndTag(self):
    self._manifests = {
        _DIGEST_SUFFIX1:
        {'tag': _TAGS1, 'timestamp': ''},
        _DIGEST_SUFFIX2:
        {'tag': _TAGS2, 'timestamp': ''}
    }
    result = resource_projector.MakeSerializable(self.Delete([_DIGEST1,
                                                              _TAG_V1]))
    result_names = [i['name'] for i in result]
    self.assertEqual(len(_TAGS1) + 1, len(result))  # tags + digest
    self.assertEqual(len(_TAGS1), len(self._deleted_tags))
    for tag in _TAGS1:
      self.assertTrue(_REPOSITORY+':'+tag in result_names)
      self.AssertErrContains(tag)
      self.assertTrue(_REPOSITORY+':'+tag in self._deleted_tags)
    self.AssertErrContains(_DIGEST1)
    self.assertEqual(len(self._deleted_digests), 1)
    self.assertIn(_DIGEST1, result_names)
    self.assertIn(_DIGEST1, self._deleted_digests)

  def testDeleteBadInput(self):
    image_name = 'badi$mage'
    with self.assertRaises(docker_name.BadNameException):
      self.Delete([image_name])

  def testIncompleteImageName(self):
    image_name = 'gcr.io/badimage@' + _DIGEST_SUFFIX1
    with self.assertRaisesRegex(util.InvalidImageNameError,
                                'Image name should start with'):
      self.Delete([image_name])

  def testDeleteUnsupportedInputTag(self):
    image_name = 'myregistry.io/badimage:'
    with self.assertRaises(docker_name.BadNameException):
      self.Delete([image_name])

  def testDeleteUnsupportedInputDigest(self):
    image_name = 'myregistry.io/badimage@'
    with self.assertRaises(util.InvalidImageNameError):
      self.Delete([image_name])

  def testNonUniqueDigest(self):
    self._manifests = {
        _DIGEST_SUFFIX1:
        {'tag': _TAGS1, 'timestamp': ''},
        _DIGEST_SUFFIX2:
        {'tag': _TAGS2, 'timestamp': ''}
    }
    with self.assertRaises(util.InvalidImageNameError):
      self.Delete([_REPOSITORY + '@' + 'sha256:'])

if __name__ == '__main__':
  test_case.main()
