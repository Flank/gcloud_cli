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
"""Tests for container images list commands."""

from __future__ import absolute_import
from __future__ import unicode_literals

from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.core import properties
from googlecloudsdk.core.docker import docker
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2
import mock
import six.moves.http_client

_REPOSITORY = 'gcr.io/foobar'


class ListTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    properties.VALUES.core.project.Set('myproject')
    self._children = {}
    self.registry_mock = mock.Mock()
    self.registry_mock.children.side_effect = lambda: self._children

    ctx_manager = self.StartObjectPatch(docker_image.FromRegistry, '__enter__')
    ctx_manager.return_value = self.registry_mock

  def List(self, repository=None):
    args = ['container', 'images', 'list']
    if repository:
      args.append('--repository={0}'.format(repository))
    self.Run(args)

  def testListEmpty(self):
    self.List(_REPOSITORY)
    self.AssertErrContains('Listed 0 items.')

  def testListNoFlag(self):
    # We should default to the project if there is no argument.
    validate = self.StartObjectPatch(util, 'ValidateRepositoryPath')
    self.List()
    validate.assert_called_once_with('gcr.io/myproject')
    self.AssertErrContains('Listed 0 items.')

  def testListImages_DomainScopedProject(self):
    properties.VALUES.core.project.Set('google.com:my-project')
    validate = self.StartObjectPatch(util, 'ValidateRepositoryPath')
    self.List()
    validate.assert_called_once_with('gcr.io/google.com/my-project')
    self.AssertErrContains('Listed 0 items.')

  def testListImages(self):
    self._children = ['tag1', 'tag2']
    self.List(_REPOSITORY)
    for tag in self._children:
      self.AssertOutputContains('{0}/{1}'.format(_REPOSITORY, tag))

    self.List()
    for tag in self._children:
      self.AssertOutputContains('{0}/{1}'.format(_REPOSITORY, tag))
    self.AssertErrContains('Only listing images in gcr.io/')

  def testListImages_DomainScoped(self):
    self._children = ['tag1', 'tag2']
    self.List(_REPOSITORY)
    for tag in self._children:
      self.AssertOutputContains('{0}/{1}'.format(_REPOSITORY, tag))

    self.List()
    for tag in self._children:
      self.AssertOutputContains('{0}/{1}'.format(_REPOSITORY, tag))
    self.AssertErrContains('Only listing images in gcr.io/')

  def testListBadInput(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.List('badi$mage')
    self.AssertErrContains('A Docker registry domain must be specified.')

  def testListUnsupportedInput(self):
    with self.assertRaises(docker.UnsupportedRegistryError):
      self.List('myregistry.io/badimage')
    self.AssertErrContains(
        'myregistry.io/badimage is not in a supported registry.  '
        'Supported registries are')

  def testListUnauthorized(self):
    # Simulate a 401 error the dockerless client.
    err = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.UNAUTHORIZED
        }), '')
    self.registry_mock.children.side_effect = err

    with self.assertRaises(util.UserRecoverableV2Error):
      self.List()
    self.AssertErrContains('Access denied:')

  def testListForbidden(self):
    # Simulate a 403 error the dockerless client.
    err = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.FORBIDDEN
        }), '')

    self.registry_mock.children.side_effect = err

    with self.assertRaises(util.UserRecoverableV2Error):
      self.List()
    self.AssertErrContains('Access denied:')

  def testListNotFound(self):
    # Simulate a 404 error the dockerless client.
    err = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': six.moves.http_client.NOT_FOUND
        }), '')

    self.registry_mock.children.side_effect = err

    with self.assertRaises(util.UserRecoverableV2Error):
      self.List()
    self.AssertErrContains('Not found:')

  def testListTokenRefreshError(self):
    expected_message = 'Bad status during token exchange: 403'
    exception = docker_http.TokenRefreshException(expected_message)

    self.registry_mock.children.side_effect = exception

    with self.assertRaises(util.TokenRefreshError):
      self.List()
    self.AssertErrContains(expected_message)


if __name__ == '__main__':
  test_case.main()
