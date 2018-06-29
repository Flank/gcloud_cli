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
"""Tests for the container images add-tag command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from containerregistry.client.v2 import docker_http as v2_docker_http
from containerregistry.client.v2 import docker_image as v2_image
from containerregistry.client.v2 import docker_session as v2_session
from containerregistry.client.v2_2 import docker_http as v2_2_docker_http
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_image_list
from containerregistry.client.v2_2 import docker_session as v2_2_session
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.core import exceptions
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import httplib2
import mock
import six.moves.http_client

_IMAGE = 'gcr.io/foobar/baz'
_TAGS1 = ['tag1']
_TAGS2 = ['tag2']


class AddTagTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def _StoreAddedTags(self, name, creds, transport, command):
    self._added_tags.add(str(name))

  def SetUp(self):
    self._added_tags = set()
    self._manifests = {}
    self._manifest = {}
    self.registry_mock = mock.MagicMock()
    self.registry_mock.manifests = lambda: self._manifests
    self.registry_mock.manifest = lambda: self._manifest

    self.push_mock = mock.MagicMock()

    mock1_init = self.StartObjectPatch(v2_docker_http, 'Transport')
    mock1_init.side_effect = self._StoreAddedTags

    mock2_init = self.StartObjectPatch(v2_2_docker_http, 'Transport')
    mock2_init.side_effect = self._StoreAddedTags

    ctx_manager = self.StartObjectPatch(v2_image.FromRegistry, '__enter__')
    ctx_manager.return_value = self.registry_mock

    ctx_manager_2 = self.StartObjectPatch(v2_session.Push, '__enter__')
    ctx_manager_2.return_value = self.push_mock

    ctx_manager_3 = self.StartObjectPatch(v2_2_image.FromRegistry, '__enter__')
    ctx_manager_3.return_value = self.registry_mock

    ctx_manager_4 = self.StartObjectPatch(v2_2_session.Push, '__enter__')
    ctx_manager_4.return_value = self.push_mock

    ctx_manager_5 = self.StartObjectPatch(docker_image_list.FromRegistry,
                                          '__enter__')
    ctx_manager_5.return_value = self.registry_mock

  def InitManifest(self, version):
    self._manifests = {_MakeSha('a'*64): {'tag': _TAGS1, 'timestamp': ''},
                       _MakeSha('b'*64): {'tag': _TAGS2, 'timestamp': ''}}

    self._manifest = {'schemaVersion': version}

  def InitManifestList(self):
    self._manifests = {_MakeSha('a'*64): {'tag': _TAGS1, 'timestamp': ''},
                       _MakeSha('b'*64): {'tag': _TAGS2, 'timestamp': ''}}

    self._manifest = {'schemaVersion': 2,
                      'manifests': []}

  def AddTag(self, src_image, *dest_images):
    cmd = (['container', 'images', 'add-tag', src_image] + list(dest_images) +
           ['-q'])
    self.Run(cmd)

  def testManifestSchema1AddTagToTag(self):
    self.InitManifest(1)
    self.AddTag(_GetImageName('tag1'), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))

  def testManifestSchema1AddMultipleTagsToTag(self):
    self.InitManifest(1)
    self.AddTag(
        _GetImageName('tag1'), _GetImageName('tag3'), _GetImageName('tag5'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.assertIn(_GetImageName('tag5'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains(_GetImageName('tag5'))

  def testManifestSchema1AddTagToDigest(self):
    self.InitManifest(1)
    self.AddTag(_GetDigestName('a' * 64), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))

  def testManifestSchema1AddTagToDigestByPrefix(self):
    self.InitManifest(1)
    self.AddTag(_GetDigestName('aaa'), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains(_GetDigestName('a' * 64))

  def testManifestSchema1AddTagToLatest(self):
    self.InitManifest(1)
    self.AddTag(_IMAGE, _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains('latest')

  def testManifestSchema2AddTagToTag(self):
    self.InitManifest(2)
    self.AddTag(_GetImageName('tag1'), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))

  def testManifestSchema2AddMultipleTagsToTag(self):
    self.InitManifest(2)
    self.AddTag(
        _GetImageName('tag1'), _GetImageName('tag3'), _GetImageName('tag5'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.assertIn(_GetImageName('tag5'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains(_GetImageName('tag5'))

  def testManifestSchema2AddTagToDigest(self):
    self.InitManifest(2)
    self.AddTag(_GetDigestName('a'*64), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))

  def testManifestSchema2AddTagToDigestByPrefix(self):
    self.InitManifest(2)
    self.AddTag(_GetDigestName('aaa'), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains(_GetDigestName('a'*64))

  def testManifestSchema2AddTagToLatest(self):
    self.InitManifest(2)
    self.AddTag(_IMAGE, _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains('latest')

  def testManifestListAddTagToTag(self):
    self.InitManifestList()
    self.AddTag(_GetImageName('tag1'), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))

  def testManifestListAddMultipleTagsToTag(self):
    self.InitManifestList()
    self.AddTag(
        _GetImageName('tag1'), _GetImageName('tag3'), _GetImageName('tag5'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.assertIn(_GetImageName('tag5'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains(_GetImageName('tag5'))

  def testManifestListAddTagToDigest(self):
    self.InitManifestList()
    self.AddTag(_GetDigestName('a'*64), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))

  def testManifestListAddTagToDigestByPrefix(self):
    self.InitManifestList()
    self.AddTag(_GetDigestName('aaa'), _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains(_GetDigestName('a'*64))

  def testManifestListAddTagToLatest(self):
    self.InitManifestList()
    self.AddTag(_IMAGE, _GetImageName('tag3'))
    self.assertIn(_GetImageName('tag3'), self._added_tags)
    self.AssertErrContains(_GetImageName('tag3'))
    self.AssertErrContains('latest')

  def testNotFound(self):
    image_name = 'gcr.io/coolcompany/notfound'
    self.registry_mock.exists = lambda: False

    # Simulate a 404 error the dockerless client.
    err = v2_docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.NOT_FOUND
        }), '')

    self.push_mock.upload.side_effect = err

    # NOT_FOUND is a user-recoverable error, gcloud should terminate elegantly
    with self.assertRaises(util.UserRecoverableV2Error):
      self.AddTag(image_name, _GetImageName('tag3'))

  def testForbidden(self):
    image_name = 'gcr.io/coolercompany/forbidden'
    self.registry_mock.exists = lambda: True

    # Simulate a 403 error the dockerless client.
    err = v2_docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.FORBIDDEN
        }), '')

    self.push_mock.upload.side_effect = err

    # FORBIDDEN is a user-recoverable error, gcloud should terminate elegantly
    with self.assertRaises(util.UserRecoverableV2Error):
      self.AddTag(image_name, _GetImageName('tag3'))

  def testTokenRefreshError(self):
    image_name = 'gcr.io/coolcompany/notfound'
    self.registry_mock.exists = lambda: False

    expected_message = 'Bad status during token exchange: 403'
    exception = v2_docker_http.TokenRefreshException(expected_message)

    self.push_mock.upload.side_effect = exception

    # Auth failures are user-recoverable, gcloud should terminate elegantly
    try:
      with self.assertRaises(util.TokenRefreshError):
        self.AddTag(image_name, _GetImageName('tag3'))
    except Exception as e:
      print('Exeptions type: ', type(e))
      raise Exception(e)

  def testProjectRootDestionationImage(self):
    image_name = _GetImageName('latest')
    with self.assertRaises(exceptions.Error):
      self.AddTag(image_name, 'gcr.io/project-id:tag')

  def testInvalidSourceName(self):
    image_name = 'badi$mage'
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(image_name, _GetImageName('tag3'))

  def testInvalidDestName(self):
    image_name = 'badi$mage'
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(_GetImageName('tag1'), image_name)

  def testNonExistentSourceDigest(self):
    digest = _GetDigestName('bad')
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(digest, _GetImageName('tag3'))

  def testInvalidSourceRepo(self):
    image_name = 'myrepository.com/blah:'
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(image_name, _GetImageName('tag3'))

  def testInvalidDestRepo(self):
    image_name = 'myrepository.com/blah:'
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(_GetImageName('tag1'), image_name)

  def testManifestSchema1NonUniqueDigest(self):
    self.InitManifest(1)
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(_GetDigestName(''), _GetImageName('tag3'))

  def testManifestSchema2NonUniqueDigest(self):
    self.InitManifest(2)
    with self.assertRaises(util.InvalidImageNameError):
      self.AddTag(_GetDigestName(''), _GetImageName('tag3'))


def _MakeSha(sha):
  return 'sha256:{0}'.format(sha)


def _StripSha(sha):
  return sha.replace('sha256:', '')


def _GetImageName(tag_name, image=_IMAGE):
  return image + ':' + tag_name


def _GetDigestName(digest, image=_IMAGE):
  return image + '@' + _MakeSha(digest)


if __name__ == '__main__':
  test_case.main()
