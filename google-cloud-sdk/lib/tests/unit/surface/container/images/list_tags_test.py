# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for the container images list-tags commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.docker import docker
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import httplib2
import mock
import six


_IMAGE = 'gcr.io/foobar/baz'

# Real value from gcr.io/google-appengine/java-compat with digest:
# sha256:0422a02d982780308b998f12f9235d1afb26a3e736cafc04adb44c71a612d921
_TIME_CREATED_MS = 1460666826974
_TIME_CREATED = round(float(_TIME_CREATED_MS) / 1000, 0)
_NEWER_TIME_CREATED_MS = 1490807651000  # 3/29/2017, 5:14pm UTC
_NEWER_TIME_CREATED = round(float(_NEWER_TIME_CREATED_MS) / 1000, 0)
_UNDERFLOW_CREATED_MS = -62135596800000  # Observed in the wild.


class ListTagsGATest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self._manifests = {}
    registry_mock = mock.Mock()
    registry_mock.manifests = lambda: self._manifests

    ctx_manager = self.StartObjectPatch(docker_image.FromRegistry, '__enter__')
    ctx_manager.return_value = registry_mock

  def ListTags(self, image=_IMAGE):
    params = ['container', 'images', 'list-tags', image]
    self.Run(params)

  def testListEmpty(self):
    self.ListTags()
    self.AssertErrContains('Listed 0 items.')

  def testDockerError_403(self):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')
    response = httplib2.Response({'status': 403, 'body': 'some body'})
    exception = docker_http.V2DiagnosticException(
        response, 'some content'.encode('utf-8'))
    transform_manifests_mock.side_effect = exception
    with self.assertRaises(util.UserRecoverableV2Error) as cm:
      self.ListTags()
    self.assertTrue('Access denied', six.text_type(cm.exception))

  def testDockerError_404(self):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')
    response = httplib2.Response({'status': 404, 'body': 'some body'})
    exception = docker_http.V2DiagnosticException(
        response, 'some content'.encode('utf-8'))
    transform_manifests_mock.side_effect = exception
    with self.assertRaises(util.UserRecoverableV2Error) as cm:
      self.ListTags()
    self.assertTrue('Not found', six.text_type(cm.exception))

  def testListTagsNoOccurrences(self):
    # Intercept FormatDateTime to use UTC for test portability.
    real_format_date_time = times.FormatDateTime

    def _FormatDateTimeUTC(dt, fmt=None, tzinfo=None):
      del tzinfo
      return real_format_date_time(dt, fmt=fmt, tzinfo=times.UTC)

    self.StartObjectPatch(
        times, 'FormatDateTime', side_effect=_FormatDateTimeUTC)

    self._manifests = {
        _MakeSha('sha1'): {
            'tag': ['tag1'],
            'timeCreatedMs': _TIME_CREATED_MS,
        },
        _MakeSha('sha2'): {
            'tag': ['tag2', 'tag3'],
            'timeCreatedMs': _TIME_CREATED_MS + 1000,  # +1s to ensure ordering.
        },
    }
    self.ListTags()
    self.AssertOutputEquals("""\
DIGEST TAGS TIMESTAMP
sha2 tag2,tag3 2016-04-14T20:47:08
sha1 tag1 2016-04-14T20:47:07
""", normalize_space=True)

  def testListTagsBadInput(self):
    with self.assertRaises(util.InvalidImageNameError):
      self.ListTags('gcr.io/foo/badi$mage')
    self.AssertErrContains('Invalid repository: foo/badi$mage, acceptable '
                           'characters include')

  def testListTagsUnsupportedInput(self):
    with self.assertRaises(docker.UnsupportedRegistryError):
      self.ListTags('myregistry.io/badimage')
    self.AssertErrContains(
        'myregistry.io/badimage is not in a supported registry.  '
        'Supported registries are')

  def testListTagsOutput(self):
    self._manifests = {
        _MakeSha('sha1'): {
            'tag': ['tag1'],
            'timeCreatedMs': _TIME_CREATED_MS
        },
        _MakeSha('sha2'): {
            'tag': ['tag2', 'tag3'],
            'timeCreatedMs': _NEWER_TIME_CREATED_MS
        },
        _MakeSha('sha3'): {
            'tag': ['tag4'],
            'timeCreatedMs': _UNDERFLOW_CREATED_MS
        }
    }

    self.ListTags()
    expected_time = times.FormatDateTime(
        times.GetDateTimeFromTimeStamp(_TIME_CREATED), '%Y-%m-%dT%H:%M:%S')
    newer_expected_time = times.FormatDateTime(
        times.GetDateTimeFromTimeStamp(
            _NEWER_TIME_CREATED), '%Y-%m-%dT%H:%M:%S')

    self.AssertOutputContains('DIGEST TAGS TIMESTAMP', normalize_space=True)
    self.AssertOutputContains(
        '{digest} {tags} {timestamp}'.format(
            digest='sha1', tags='tag1', timestamp=expected_time),
        normalize_space=True)
    self.AssertOutputContains(
        '{digest} {tags} {timestamp}'.format(
            digest='sha2', tags='tag2,tag3', timestamp=newer_expected_time),
        normalize_space=True)
    self.AssertOutputMatches(
        '{digest}.*{tags}'.format(digest='sha3', tags='tag4'),
        normalize_space=True)

    # Verify descending order of the timestamps.
    self.assertLess(
        self.GetOutput().index('sha2'), self.GetOutput().index('sha1'))
    self.assertLess(
        self.GetOutput().index('sha1'), self.GetOutput().index('sha3'))


class ListTagsAlphaAndBetaTest(cli_test_base.CliTestBase,
                               sdk_test_base.WithFakeAuth,
                               parameterized.TestCase):

  def SetUp(self):
    self._manifests = {}
    registry_mock = mock.Mock()
    registry_mock.manifests = lambda: self._manifests

    ctx_manager = self.StartObjectPatch(docker_image.FromRegistry, '__enter__')
    ctx_manager.return_value = registry_mock

    self.fetch_occurrence_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.FetchOccurrences')
    self.fetch_summary_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.FetchSummary')

  def ListTags(self,
               track,
               image=_IMAGE,
               show_occurrences=True,
               show_occurrences_from=None):
    params = [track, 'container', 'images', 'list-tags', image]
    if not show_occurrences:
      params.append('--no-show-occurrences')
    if show_occurrences_from:
      params.append('--show-occurrences-from=%s' % show_occurrences_from)
    self.Run(params)

  @parameterized.parameters(('alpha'), ('beta'))
  def testListEmpty(self, track):
    self.ListTags(track)
    self.AssertErrContains('Listed 0 items.')

  @parameterized.parameters(('alpha'), ('beta'))
  def testV2DockerError_403(self, track):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')
    response = httplib2.Response({'status': 403, 'body': 'some body'})
    exception = docker_http.V2DiagnosticException(
        response, 'some content'.encode('utf-8'))
    transform_manifests_mock.side_effect = exception
    with self.assertRaises(util.UserRecoverableV2Error) as cm:
      self.ListTags(track)
    self.assertTrue('Access denied', six.text_type(cm.exception))

  @parameterized.parameters(('alpha'), ('beta'))
  def testV2DockerError_404(self, track):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')
    response = httplib2.Response({'status': 404, 'body': 'some body'})
    exception = docker_http.V2DiagnosticException(
        response, 'some content'.encode('utf-8'))
    transform_manifests_mock.side_effect = exception
    with self.assertRaises(util.UserRecoverableV2Error) as cm:
      self.ListTags(track)
    self.assertTrue('Not found', six.text_type(cm.exception))

  @parameterized.parameters(('alpha'), ('beta'))
  def testBadStateException_CredentialRefreshError(self, track):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')
    expected_message = 'Bad status during token exchange: 403'
    exception = docker_http.TokenRefreshException(expected_message)
    transform_manifests_mock.side_effect = exception
    with self.assertRaises(util.TokenRefreshError) as cm:
      self.ListTags(track)
    self.assertIn(expected_message, six.text_type(cm.exception))

  @parameterized.parameters(('alpha'), ('beta'))
  def testBadStateException_UnexpectedErrorsRaised(self, track):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')
    exception = docker_http.BadStateException('some unexpected error')
    transform_manifests_mock.side_effect = exception
    with self.assertRaises(docker_http.BadStateException):
      self.ListTags(track)

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsNoOccurrences(self, track):
    # Intercept FormatDateTime to use UTC for test portability.
    real_format_date_time = times.FormatDateTime

    def _FormatDateTimeUTC(dt, fmt=None, tzinfo=None):
      del tzinfo
      return real_format_date_time(dt, fmt=fmt, tzinfo=times.UTC)

    self.StartObjectPatch(
        times, 'FormatDateTime', side_effect=_FormatDateTimeUTC)

    self.fetch_occurrence_mock.return_value = {}
    self._manifests = {
        _MakeSha('sha1'): {
            'tag': ['tag1'],
            'timeCreatedMs': _TIME_CREATED_MS,
        },
        _MakeSha('sha2'): {
            'tag': ['tag2', 'tag3'],
            'timeCreatedMs': _TIME_CREATED_MS + 1000,  # +1s to ensure ordering.
        },
    }
    self.ListTags(track)
    self.AssertOutputEquals("""\
DIGEST TAGS TIMESTAMP
sha2 tag2,tag3 2016-04-14T20:47:08
sha1 tag1 2016-04-14T20:47:07
""", normalize_space=True)

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsBadInput(self, track):
    with self.assertRaises(util.InvalidImageNameError):
      self.ListTags(track, 'gcr.io/foo/badi$mage')
    self.AssertErrContains('Invalid repository: foo/badi$mage, acceptable '
                           'characters include')

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsUnsupportedInput(self, track):
    with self.assertRaises(docker.UnsupportedRegistryError):
      self.ListTags(track, 'myregistry.io/badimage')
    self.AssertErrContains(
        'myregistry.io/badimage is not in a supported registry.  '
        'Supported registries are')

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsDoNotShowOccurrences(self, track):
    self._manifests = {_MakeSha('sha1'): {'tag': ['tag1'],
                                          'timeCreatedMs': _TIME_CREATED_MS},
                       _MakeSha('sha2'): {'tag': ['tag2', 'tag3'],
                                          'timeCreatedMs': _TIME_CREATED_MS}}
    self.ListTags(track, show_occurrences=False)
    for digest, data in six.iteritems(self._manifests):
      self.AssertOutputContains(_StripSha(digest))
      for tag in data['tag']:
        self.AssertOutputContains(tag)

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsRespectsVulnerabilityLimitCount(self, track):
    resource_url1 = 'https://{repo}@{digest}'.format(
        repo=_IMAGE, digest=_MakeSha('sha1'))
    resource_url2 = 'https://{repo}@{digest}'.format(
        repo=_IMAGE, digest=_MakeSha('sha2'))
    self._manifests = {
        _MakeSha('sha1'): {
            'tag': [''], 'timeCreatedMs': _TIME_CREATED_MS},
        _MakeSha('sha2'): {
            'tag': [''], 'timeCreatedMs': _NEWER_TIME_CREATED_MS}}
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')

    # Limit to only the most recent occurrence.
    self.ListTags(track, show_occurrences_from=1)
    _, kwargs = transform_manifests_mock.call_args
    self.assertListEqual(kwargs['resource_urls'], [resource_url2])

    # Limit to the two most recent occurrences (both, in this test).
    transform_manifests_mock.reset_mock()
    self.ListTags(track, show_occurrences_from=2)
    _, kwargs = transform_manifests_mock.call_args
    self.assertListEqual(
        kwargs['resource_urls'], [resource_url2, resource_url1])

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsDoesNotFilterResourceUrlsWhenFlagIsUnlimited(self, track):
    transform_manifests_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.TransformManifests')

    # Set unlimited limit of images for which to show occurrences.
    self.ListTags(track, show_occurrences_from='unlimited')
    _, kwargs = transform_manifests_mock.call_args
    self.assertEqual(None, kwargs['resource_urls'])

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsRaisesErrorWhenShowOccurrenceFlagsConflict(self, track):
    # If --show-occurrences-from is explicitly provided when
    # --show-occurrences=False, an ArgumentError is raised.
    with self.assertRaises(exceptions.Error):
      self.ListTags(track, show_occurrences=False, show_occurrences_from=10)

  @parameterized.parameters(('alpha'), ('beta'))
  def testListTagsOutput(self, track):
    resource_url1 = 'https://{repo}@{digest}'.format(
        repo=_IMAGE, digest=_MakeSha('sha1'))
    resource_url2 = 'https://{repo}@{digest}'.format(
        repo=_IMAGE, digest=_MakeSha('sha2'))
    resource_url3 = 'https://{repo}@{digest}'.format(
        repo=_IMAGE, digest=_MakeSha('sha3'))

    messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    self.fetch_occurrence_mock.return_value = {
        resource_url1: [
            _BuildDetails('025192e7-6c4f-4352-96cf-f5dd7724105f',
                          'deadbeefbaadf00d'),
            _PackageVulnerability(
                messages.VulnerabilityDetails.SeverityValueValuesEnum.CRITICAL),
            _PackageVulnerability(
                messages.VulnerabilityDetails.SeverityValueValuesEnum.HIGH),
            _PackageVulnerability(
                messages.VulnerabilityDetails.SeverityValueValuesEnum.MEDIUM),
            _DerivedImage(
                'https://gcr.io/google-appengine/debian@sha256:abcdefg', 20),
            _DerivedImage('https://gcr.io/google-appengine/base@sha256:0123345',
                          10),
            _DerivedImage('https://gcr.io/google-appengine/java@sha256:a1b2c3',
                          3),
        ],
        resource_url2: [
            _BuildDetails('2076ecf0-e411-4828-843e-88ad3a97b897',
                          'baadf00ddeadbeef'),
            _PackageVulnerability(
                messages.VulnerabilityDetails.SeverityValueValuesEnum.HIGH),
            _PackageVulnerability(
                messages.VulnerabilityDetails.SeverityValueValuesEnum.HIGH),
            _DerivedImage(
                'https://gcr.io/google-appengine/debian@sha256:abcdefg', 20),
            _DerivedImage(
                'https://gcr.io/google-appengine/python@sha256:d5e6f7', 4),
            _DerivedImage('https://gcr.io/google-appengine/base@sha256:0123345',
                          10),
        ],
        resource_url3: [
            _BuildDetails('2076ecf0-e411-4828-843e-88427a97b444',
                          'f000f000deadbeef'),
            _PackageVulnerability(
                messages.VulnerabilityDetails.SeverityValueValuesEnum.HIGH),
            _DerivedImage(
                'https://gcr.io/google-appengine/base@sha256:deadf000', 10),
        ],
    }
    def _MockSummaryFunc(unused_repository, resource_url):
      # `prefix` a convenience var for shorter line length below.
      prefix = messages.SeverityCount.SeverityValueValuesEnum
      if resource_url == resource_url1:
        return messages.GetVulnzOccurrencesSummaryResponse(
            counts=[
                messages.SeverityCount(count=1, severity=prefix.CRITICAL),
                messages.SeverityCount(count=1, severity=prefix.HIGH),
                messages.SeverityCount(count=1, severity=prefix.MEDIUM)])
      elif resource_url == resource_url2:
        return messages.GetVulnzOccurrencesSummaryResponse(
            counts=[messages.SeverityCount(count=2, severity=prefix.HIGH)])
      elif resource_url == resource_url3:
        return messages.GetVulnzOccurrencesSummaryResponse(
            counts=[messages.SeverityCount(count=1, severity=prefix.HIGH)])
    self.fetch_summary_mock.side_effect = _MockSummaryFunc

    self._manifests = {
        _MakeSha('sha1'): {
            'tag': ['tag1'],
            'timeCreatedMs': _TIME_CREATED_MS
        },
        _MakeSha('sha2'): {
            'tag': ['tag2', 'tag3'],
            'timeCreatedMs': _NEWER_TIME_CREATED_MS
        },
        _MakeSha('sha3'): {
            'tag': ['tag4'],
            'timeCreatedMs': _UNDERFLOW_CREATED_MS
        }
    }

    self.ListTags(track)

    expected_time = times.FormatDateTime(
        times.GetDateTimeFromTimeStamp(_TIME_CREATED), '%Y-%m-%dT%H:%M:%S')
    newer_expected_time = times.FormatDateTime(
        times.GetDateTimeFromTimeStamp(
            _NEWER_TIME_CREATED), '%Y-%m-%dT%H:%M:%S')

    self.AssertOutputContains(
        'DIGEST TAGS TIMESTAMP GIT_SHA VULNERABILITIES FROM BUILD',
        normalize_space=True)
    self.AssertOutputContains(
        '{digest} {tags} {timestamp} {sha1} {vulnz} {_from} {build}'.format(
            digest='sha1', tags='tag1', timestamp=expected_time,
            vulnz='CRITICAL=1,HIGH=1,MEDIUM=1', sha1='deadbeef',
            _from='gcr.io/google-appengine/java',
            build='025192e7-6c4f-4352-96cf-f5dd7724105f'),
        normalize_space=True)
    self.AssertOutputContains(
        '{digest} {tags} {timestamp} {sha1} {vulnz} {_from} {build}'.format(
            digest='sha2', tags='tag2,tag3', timestamp=newer_expected_time,
            vulnz='HIGH=2', sha1='baadf00d',
            _from='gcr.io/google-appengine/python',
            build='2076ecf0-e411-4828-843e-88ad3a97b897'),
        normalize_space=True)
    self.AssertOutputMatches(
        '{digest} {tags}.*{sha1} {vulnz} {_from} {build}'.format(
            digest='sha3',
            tags='tag4',
            vulnz='HIGH=1',
            sha1='f000f000',
            _from='gcr.io/google-appengine/base',
            build='2076ecf0-e411-4828-843e-88427a97b444'),
        normalize_space=True)

    # Verify descending order of the timestamps.
    self.assertLess(
        self.GetOutput().index('sha2'), self.GetOutput().index('sha1'))
    self.assertLess(
        self.GetOutput().index('sha1'), self.GetOutput().index('sha3'))


def _MakeSha(sha):
  return 'sha256:{0}'.format(sha)


def _StripSha(sha):
  return sha.replace('sha256:', '')


def _BuildDetails(uuid, sha1):
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  provenance = messages.BuildProvenance(id=uuid)
  bdo = messages.Occurrence(
      kind=messages.Occurrence.KindValueValuesEnum.BUILD_DETAILS,
      buildDetails=messages.BuildDetails(
          provenance=provenance,
      )
  )
  if not sha1:
    return bdo

  src_ctxt = messages.GoogleDevtoolsContaineranalysisV1alpha1SourceContext
  crs = messages.GoogleDevtoolsContaineranalysisV1alpha1CloudRepoSourceContext
  provenance.sourceProvenance = messages.Source(
      context=src_ctxt(
          cloudRepo=crs(revisionId=sha1),
      ),
  )
  return bdo


def _PackageVulnerability(severity):
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  return messages.Occurrence(
      kind=messages.Occurrence.KindValueValuesEnum.PACKAGE_VULNERABILITY,
      vulnerabilityDetails=messages.VulnerabilityDetails(severity=severity))


def _DerivedImage(base_resource_url, distance):
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  return messages.Occurrence(
      kind=messages.Occurrence.KindValueValuesEnum.IMAGE_BASIS,
      derivedImage=messages.Derived(
          distance=distance,
          baseResourceUrl=base_resource_url,
      )
  )


if __name__ == '__main__':
  test_case.main()
