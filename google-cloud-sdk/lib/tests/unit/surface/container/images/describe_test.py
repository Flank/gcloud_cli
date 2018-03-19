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
"""Tests for the container images describecommands."""

import httplib

from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import httplib2

import mock


_IMAGE_STR = (
    'gcr.io/foobar/baz@sha256:'
    '0422a02d982780308b998f12f9235d1afb26a3e736cafc04adb44c71a612d921')


class DescribeTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self._manifests = {}
    registry_mock = mock.Mock()
    registry_mock.manifests = lambda: self._manifests

    ctx_manager = self.StartObjectPatch(docker_image.FromRegistry, '__enter__')
    ctx_manager.return_value = registry_mock

  def Describe(self, image=_IMAGE_STR, args=None):
    cmd = ['container', 'images', 'describe', image]
    if args:
      cmd.extend(args)
    self.Run(cmd)

  def testOutput(self):
    self.Describe()
    self.AssertOutputContains('fully_qualified_digest: ' + _IMAGE_STR)

  def testDescribe_BadRepo(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.Describe('gcr.io/foo/badi$mage@sha256:dfdsfdfsf')
    self.AssertErrContains('Invalid repository: foo/badi$mage, acceptable '
                           'characters include')

  @mock.patch('googlecloudsdk.api_lib.container.images.util.GetDigestFromName')
  def testDescribe_NotFound(self, mock_get_digest_from_name):
    mock_get_digest_from_name.side_effect = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': httplib.NOT_FOUND
        }), '')
    test_image = 'gcr.io/foo/goodimage:latest'
    with self.assertRaises(util.UserRecoverableV2Error):
      self.Describe(test_image)
    self.AssertErrContains('Not found: ' + test_image)

  @mock.patch('googlecloudsdk.api_lib.container.images.util.GetDigestFromName')
  def testDescribe_Forbidden(self, mock_get_digest_from_name):
    mock_get_digest_from_name.side_effect = docker_http.V2DiagnosticException(
        httplib2.Response({
            'status': httplib.FORBIDDEN
        }), '')
    test_image = 'gcr.io/foo/goodimage:latest'
    with self.assertRaises(util.UserRecoverableV2Error):
      self.Describe(test_image)
    self.AssertErrContains('Access denied: ' + test_image)

  @mock.patch('googlecloudsdk.api_lib.container.images.util.GetDigestFromName')
  def testDescribe_TokenRefreshFailure(self, mock_get_digest_from_name):
    expected_message = 'Bad status during token exchange: 403'
    exception = docker_http.TokenRefreshException(expected_message)
    mock_get_digest_from_name.side_effect = exception
    test_image = 'gcr.io/foo/goodimage:latest'
    with self.assertRaises(util.TokenRefreshError):
      self.Describe(test_image)
    self.AssertErrContains(expected_message)


class DescribeAlphaOldTest(cli_test_base.CliTestBase,
                           sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self._manifests = {}
    registry_mock = mock.Mock()
    registry_mock.manifests = lambda: self._manifests

    ctx_manager = self.StartObjectPatch(docker_image.FromRegistry, '__enter__')
    ctx_manager.return_value = registry_mock

    self.fetch_occurrence_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.'
        'FetchOccurrencesForResource')

  def Describe(self, image=_IMAGE_STR, args=None):
    cmd = ['alpha', 'container', 'images', 'describe', image]
    if args:
      cmd.extend(args)
    self.Run(cmd)

  def testBuildDetailsContainerAnalysisOutput(self):
    self.fetch_occurrence_mock.return_value = [
        _BuildDetails('025192e7-6c4f-4352-96cf-f5dd7724105f'),
    ]
    self.Describe(args=['--show-build-details'])
    self.AssertOutputContains('fully_qualified_digest: ' + _IMAGE_STR)

    self.AssertOutputContains("""build_details_summary:
  build_details:
  - buildDetails:
      provenance:
        createTime: '2016-09-27T01:25:22.816218Z'
        creator: kokoro@google-appengine.iam.gserviceaccount.com
        id: 025192e7-6c4f-4352-96cf-f5dd7724105f
        logsBucket: gs/file/logs
    kind: BUILD_DETAILS
image_summary:
""")

  def testBaseImageContainerAnalysisOutput(self):
    self.fetch_occurrence_mock.return_value = [
        _ImageBasis('https://gcr.io/foo', dist=13),
        _ImageBasis('https://gcr.io/bar', dist=17),
    ]
    self.Describe(args=['--show-image-basis'])
    self.AssertOutputContains('fully_qualified_digest: ' + _IMAGE_STR)

    self.AssertOutputContains("""image_basis_summary:
  base_images:
  - derivedImage:
      baseResourceUrl: https://gcr.io/foo
      distance: 13
      layerInfo:
      - arguments: echo Hello World
        directive: RUN
    kind: IMAGE_BASIS
  - derivedImage:
      baseResourceUrl: https://gcr.io/bar
      distance: 17
      layerInfo:
      - arguments: echo Hello World
        directive: RUN
    kind: IMAGE_BASIS
""")

  def testBaseImageWithEmptyLayerInfoContainerAnalysisOutput(self):
    self.fetch_occurrence_mock.return_value = [
        _EmptyImageBasis('https://gcr.io/foo', dist=13),
    ]
    self.Describe(args=['--show-image-basis'])
    self.AssertOutputContains('fully_qualified_digest: ' + _IMAGE_STR)

    self.AssertOutputContains("""image_basis_summary:
  base_images:
  - derivedImage:
      baseResourceUrl: https://gcr.io/foo
      distance: 13
      layerInfo:
      - {}
    kind: IMAGE_BASIS
""")

  def testOccurrenceFilter(self):
    self.fetch_occurrence_mock.return_value = [
        _EmptyImageBasis('https://gcr.io/foo', dist=13),
    ]
    self.Describe(args=['--metadata-filter=kind = "IMAGE_BASIS"'])
    self.AssertOutputContains('fully_qualified_digest: ' + _IMAGE_STR)

    self.AssertOutputContains("""image_basis_summary:
  base_images:
  - derivedImage:
      baseResourceUrl: https://gcr.io/foo
      distance: 13
      layerInfo:
      - {}
    kind: IMAGE_BASIS
""")

  def testVulnzCount(self):
    messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    self.fetch_occurrence_mock.return_value = [
        _PackageVulnerability(
            messages.VulnerabilityDetails.SeverityValueValuesEnum.CRITICAL,
            'fixed_package', '1.0'),
        _PackageVulnerability(
            messages.VulnerabilityDetails.SeverityValueValuesEnum.HIGH,
            'not_fixed', '2.0', fixed=False),
    ]
    self.Describe(args=['--format=json', '--show-package-vulnerability'])
    self.AssertOutputContains('"total_vulnerability_found": 2')
    self.AssertOutputContains('"not_fixed_vulnerability_count": 1')

  def testDescribeBadRepo(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.Describe('gcr.io/foo/badi$mage@sha256:dfdsfdfsf')
    self.AssertErrContains('Invalid repository: foo/badi$mage, acceptable '
                           'characters include')


def _BuildDetails(uuid):
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  provenance = messages.BuildProvenance(id=uuid)
  bdo = messages.Occurrence(
      kind=messages.Occurrence.KindValueValuesEnum.BUILD_DETAILS,
      buildDetails=messages.BuildDetails(
          provenance=provenance,
      )
  )
  provenance.createTime = '2016-09-27T01:25:22.816218Z'
  provenance.creator = 'kokoro@google-appengine.iam.gserviceaccount.com'
  provenance.logsBucket = 'gs/file/logs'
  return bdo


def _PackageVulnerability(severity, package_name, version, epoch=None,
                          fixed=True):
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  if fixed:
    fixed_location = messages.Version(name=version, revision='2', epoch=epoch)
  else:
    fixed_location = messages.Version(
        name=version, kind=messages.Version.KindValueValuesEnum.MAXIMUM,
        epoch=epoch)
  vulnerability_details = messages.VulnerabilityDetails(severity=severity)
  package_issues = messages.PackageIssue(
      affectedLocation=messages.VulnerabilityLocation(
          package=package_name,
          version=messages.Version(name=version, revision='1', epoch=epoch)),
      fixedLocation=messages.VulnerabilityLocation(
          package=package_name,
          version=fixed_location))
  vulnerability_details.packageIssue.append(package_issues)
  return messages.Occurrence(
      noteName='providers/notes/{0}'.format(package_name),
      kind=messages.Occurrence.KindValueValuesEnum.PACKAGE_VULNERABILITY,
      vulnerabilityDetails=vulnerability_details)


def _ImageBasis(base_url, dist=1, arguments='echo Hello World'):
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  layer_info = {}
  if arguments:
    layer_info = messages.Layer(
        directive=messages.Layer.DirectiveValueValuesEnum.RUN,
        arguments=arguments)
  return messages.Occurrence(
      kind=messages.Occurrence.KindValueValuesEnum.IMAGE_BASIS,
      derivedImage=messages.Derived(
          baseResourceUrl=base_url,
          distance=dist,
          layerInfo=[layer_info]
      ))


def _EmptyImageBasis(base_url, dist):
  return _ImageBasis(base_url, dist, arguments=None)


if __name__ == '__main__':
  test_case.main()
