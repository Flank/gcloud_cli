# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for container images untag commands."""

from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_session
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2
import mock

_REPOSITORY = 'gcr.io/project/repository'
_DIGEST_SUFFIX = 'sha256:' + 'a' * 64
_DIGEST = _REPOSITORY + '@' + _DIGEST_SUFFIX
_TAGS = ['v1', 'prod', 'frontend']
_TAG_V1 = _REPOSITORY + ':v1'
_TAG_PROD = _REPOSITORY + ':prod'


class UntagTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def _StoreRemovedTags(self, name, creds, transport):
    self._removed_tags.add(str(name))

  def SetUp(self):
    self._removed_tags = set()

    self.mock_digest_from_tag = self.StartObjectPatch(
        util, 'GetDigestFromName', return_value=_DIGEST)

    self.mock_delete = self.StartObjectPatch(docker_session, 'Delete')
    # This is an alternative to verify calls to delete. docker_name.Tags
    # are a bit of a pain to use with the mocking framework.
    self.mock_delete.side_effect = self._StoreRemovedTags

  def Untag(self, image_names):
    return self.Run([
        'container',
        'images',
        'untag',
        '--format=disable',
    ] + image_names)

  def _AssertNamesInResult(self, result, names):
    result_names = [i['name'] for i in result]
    self.assertItemsEqual(names, result_names)

  def testUntag_Digest(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.Untag([_DIGEST])

  def testUntag_DigestAndTag(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.Untag([_TAG_V1, _DIGEST])

  def testUntag_NotFullyQualified(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.Untag([_REPOSITORY])

  def testUntag_TagAndNotFullyQualified(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.Untag([_TAG_V1, _REPOSITORY])

  def testUntag_BadInput(self):
    image_name = 'badi$mage'
    with self.assertRaises(docker_name.BadNameException):
      self.Untag([image_name])

  def testUntag_UnsupportedInputTag(self):
    image_name = 'myregistry.io/badimage:'
    with self.assertRaises(docker_name.BadNameException):
      self.Untag([image_name])

  def testUntag_Registry403(self):
    response = httplib2.Response({'status': 403, 'body': 'some body'})
    exception = docker_http.V2DiagnosticException(response, 'some content')
    self.mock_delete.side_effect = exception
    with self.assertRaises(util.UserRecoverableV2Error) as cm:
      self.Untag([_TAG_V1])
    self.assertIn('Access denied:', str(cm.exception.message))

  def testUntag_Registry404(self):
    response = httplib2.Response({'status': 404, 'body': 'some body'})
    exception = docker_http.V2DiagnosticException(response, 'some content')
    self.mock_delete.side_effect = exception
    with self.assertRaises(util.UserRecoverableV2Error) as cm:
      self.Untag([_TAG_V1])
    self.assertIn('Not found:', str(cm.exception.message))

  def testUntag_TokenRefresh403(self):
    expected_message = 'Bad status during token exchange: 403'
    exception = docker_http.TokenRefreshException(expected_message)
    self.mock_delete.side_effect = exception
    with self.assertRaises(util.TokenRefreshError) as cm:
      self.Untag([_TAG_V1])
    self.assertIn(expected_message, str(cm.exception.message))

  def testUntag(self):
    result = resource_projector.MakeSerializable(self.Untag([_TAG_V1]))

    self._AssertNamesInResult(result, [_TAG_V1])

    # Assert that the digest was resolved from the tag.
    self.mock_digest_from_tag.assert_called_once_with(_TAG_V1)

    # Assert that tag to be deleted was printed.
    # The tagged digest should also be printed before deletion, for
    # reversibility. Beyond this, the exact format of this log line is
    # unimportant and can be modified as long as it adheres to gcloud's
    # formatting guidelines.
    self.AssertErrContains('Tag: [{0}]\n'
                           '- referencing digest: [{1}]'.format(
                               _TAG_V1, _DIGEST))

    # Assert that 'Delete' was called appropriately.
    self.assertTrue(_TAG_V1 in self._removed_tags)

  def testUntag_MultipleValid(self):
    result = resource_projector.MakeSerializable(
        self.Untag([_TAG_V1, _TAG_PROD]))

    self._AssertNamesInResult(result, [_TAG_V1, _TAG_PROD])

    # Assert that the digest was resolved from the tags.
    self.assertEqual(self.mock_digest_from_tag.call_count, 2)
    self.mock_digest_from_tag.assert_has_calls(
        [mock.call(_TAG_V1), mock.call(_TAG_PROD)], any_order=True)

    # Assert that tag to be deleted was printed.
    # The tagged digest should also be printed before deletion, for
    # reversibility. Beyond this, the exact format of this log line is
    # unimportant and can be modified as long as it adheres to gcloud's
    # formatting guidelines.
    for tag in [_TAG_V1, _TAG_PROD]:
      self.AssertErrContains('Tag: [{0}]\n'
                             '- referencing digest: [{1}]'.format(tag, _DIGEST))

    # Assert that 'Delete' was called appropriately.
    self.assertTrue(_TAG_V1 in self._removed_tags)
    self.assertTrue(_TAG_PROD in self._removed_tags)


if __name__ == '__main__':
  test_case.main()
