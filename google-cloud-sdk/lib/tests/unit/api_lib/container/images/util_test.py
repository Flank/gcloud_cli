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

"""Tests for googlecloudsdk.api_lib.container.images.utils."""

import time

from apitools.base.py.testing import mock as apitools_mock
from containerregistry.client import docker_name

from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.api_lib.containeranalysis import util as containeranalysis_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.docker import constants
from googlecloudsdk.core.docker import docker
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


class ValidateRepositoryPathTest(test_case.TestCase):

  def testUnsupportedRegistry(self):
    with self.assertRaises(docker.UnsupportedRegistryError):
      util.ValidateRepositoryPath('myhub.com/myrepository/myimage')

  def testSupportedRegistries(self):
    # No exceptions should be thrown.
    repository = 'myrepository/myimage'
    for registry in constants.ALL_SUPPORTED_REGISTRIES:
      r = util.ValidateRepositoryPath('{0}/{1}'.format(registry, repository))
      self.assertEqual(r.registry, registry)
      self.assertEqual(r.repository, repository)


class GetImageNameTest(test_case.TestCase):

  def testDigest(self):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    image_name = '{repo}@sha256:{hex_str}'.format(repo=repo, hex_str=hex_str)
    expected_digest = docker_name.Digest(image_name)

    digest = util.GetDockerImageFromTagOrDigest(image_name)
    self.assertEqual(expected_digest, digest)

  def testBadDigestPrefix(self):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    image_name = '{repo}@sha25:{hex_str}'.format(repo=repo, hex_str=hex_str)
    with self.assertRaises(util.InvalidImageNameError):
      util.GetDockerImageFromTagOrDigest(image_name)

  def testNoDigestPrefix(self):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    image_name = '{repo}@{hex_str}'.format(repo=repo, hex_str=hex_str)
    with self.assertRaises(util.InvalidImageNameError):
      util.GetDockerImageFromTagOrDigest(image_name)


class ValidateImageTest(test_case.TestCase):

  def testFullyQualified(self):
    for image in ['gcr.io/foo/bar:tag', 'gcr.io/foo/bar@digest']:
      with self.assertRaises(util.InvalidImageNameError):
        util.ValidateRepositoryPath(image)

  def testInvalid(self):
    for image in ['gcr.io/foo/ba$r', 'gcr.io/foo/bar' + 'a'*500, 'gcr.io/foo/']:
      with self.assertRaises(util.InvalidImageNameError):
        util.ValidateRepositoryPath(image)

  def testValid(self):
    # No exceptions should be thrown.
    for image in ['gcr.io/foo/bar', 'us.gcr.io/foo/bar/baz',]:
      i = util.ValidateRepositoryPath(image)
      self.assertEqual(str(i), image)


class TransformManifestsTest(test_case.TestCase):

  def SetUp(self):
    self._repository = docker_name.Repository('gcr.io/my-project/my-image')

    self.fetch_occurrence_mock = self.StartPatch(
        'googlecloudsdk.api_lib.container.images.util.FetchOccurrences')

  def testNoTags(self):
    response = {'digest1': {'timeCreatedMs': 123e6},
                'digest2': {'timeCreatedMs': 234e6}}
    transformed = util.TransformManifests(response, self._repository)
    self.assertEqual(len(response), len(transformed))

    # Make sure each digest is in the transformed response.
    digests = set([t['digest'] for t in transformed])
    for digest in response:
      self.assertIn(digest, digests)

    for t in transformed:
      self.assertEqual(t['tags'], [])

  def testTagsNoOccurrences(self):
    response = {'digest1': {'timeCreatedMs': 123e6, 'tag': ['a', 'b', 'c']},
                'digest2': {'timeCreatedMs': 234e6, 'tag': ['d', 'e', 'f']}}
    self.fetch_occurrence_mock.return_value = {}
    transformed = util.TransformManifests(response, self._repository)
    self.assertEqual(len(response), len(transformed))

    # Make sure each digest is in the transformed response.
    digests = set([t['digest'] for t in transformed])
    for digest in response:
      self.assertIn(digest, digests)

    for t in transformed:
      self.assertEqual(t['tags'], response[t['digest']]['tag'])

  def testTagsOneWithOccurrence(self):
    response = {'digest1': {'timeCreatedMs': 123e6, 'tag': ['a', 'b', 'c']},
                'digest2': {'timeCreatedMs': 234e6, 'tag': ['d', 'e', 'f']}}
    messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    pvo = messages.Occurrence(
        kind=messages.Occurrence.KindValueValuesEnum.PACKAGE_VULNERABILITY)
    bdo = messages.Occurrence(
        kind=messages.Occurrence.KindValueValuesEnum.BUILD_DETAILS)
    self.fetch_occurrence_mock.return_value = {
        'https://{repo}@digest1'.format(repo=str(self._repository)): [pvo, bdo],
    }
    transformed = util.TransformManifests(
        response, self._repository, show_occurrences=True)
    self.assertEqual(len(response), len(transformed))

    # Make sure each digest is in the transformed response.
    digests = set([t['digest'] for t in transformed])
    for digest in response:
      self.assertIn(digest, digests)

    for t in transformed:
      if t['digest'] != 'digest1':
        continue
      self.assertEqual([pvo], t[pvo.kind])
      self.assertEqual([bdo], t[bdo.kind])

    for t in transformed:
      self.assertEqual(t['tags'], response[t['digest']]['tag'])

  def testTimeStampTransformation_MillisecondPrecision(self):
    ts = time.time()
    dt = util._TimeCreatedToDateTime(ts)
    # There should be no microseconds
    self.assertEqual(dt.microsecond, 0)

  @test_case.Filters.DoNotRunInDebPackage('overflow does not occur here')
  @test_case.Filters.DoNotRunInRpmPackage('overflow does not occur here')
  def testTimeStampTransformation_ConversionErrorReturnsNone(self):
    overflow_time_created = -62135596800000  # Observed in the wild.
    dt = util._TimeCreatedToDateTime(overflow_time_created)
    # Return none when the timestamp cannot be converted.
    self.assertIsNone(dt)


class FetchSummaryTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self._repository = docker_name.Repository('gcr.io/my-project/my-image')
    self.messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    self.client = apitools_mock.Client(
        client_class=apis.GetClientClass('containeranalysis', 'v1alpha1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def testSummary(self):
    resource_url = 'https://%s@digest' % str(self._repository)
    # `prefix` a convenience var for shorter line length below.
    prefix = self.messages.SeverityCount.SeverityValueValuesEnum
    self.client.projects_occurrences.GetVulnerabilitySummary.Expect(
        request=(
            self.messages
            .ContaineranalysisProjectsOccurrencesGetVulnerabilitySummaryRequest(
                parent='projects/my-project',
                filter='resource_url = "%s"' % resource_url)),
        response=self.messages.GetVulnzOccurrencesSummaryResponse(
            counts=[
                self.messages.SeverityCount(count=9, severity=prefix.CRITICAL),
                self.messages.SeverityCount(count=8, severity=prefix.HIGH),
                self.messages.SeverityCount(count=7, severity=prefix.MEDIUM),
                self.messages.SeverityCount(count=6, severity=prefix.LOW),
                self.messages.SeverityCount(count=5, severity=prefix.MINIMAL),
                self.messages.SeverityCount(
                    count=4, severity=prefix.SEVERITY_UNSPECIFIED)]))

    summary = util.FetchSummary(self._repository, resource_url)
    sev_to_count = {str(x.severity): x.count for x in summary.counts}
    expected_counts = {
        'CRITICAL': 9, 'HIGH': 8, 'MEDIUM': 7, 'LOW': 6, 'MINIMAL': 5,
        'SEVERITY_UNSPECIFIED': 4}
    self.assertEqual(sev_to_count, expected_counts)


class FetchOccurrencesTest(cli_test_base.CliTestBase,
                           sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self._repository = docker_name.Repository('gcr.io/my-project/my-image')
    self.messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    self.client = apitools_mock.Client(
        client_class=apis.GetClientClass('containeranalysis', 'v1alpha1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self._original_maximum_resource_url_chunk_size = (
        containeranalysis_util._MAXIMUM_RESOURCE_URL_CHUNK_SIZE)

  def TearDown(self):
    containeranalysis_util._MAXIMUM_RESOURCE_URL_CHUNK_SIZE = (
        self._original_maximum_resource_url_chunk_size)

  def testFetchOccurrencesWithoutChunking(self):
    pvo = self.messages.Occurrence(
        resourceUrl='https://{repository}@digest2'.format(
            repository=str(self._repository)),
        kind=self.messages.Occurrence.KindValueValuesEnum.PACKAGE_VULNERABILITY)
    bdo = self.messages.Occurrence(
        resourceUrl='https://{repository}@digest1'.format(
            repository=str(self._repository)),
        kind=self.messages.Occurrence.KindValueValuesEnum.BUILD_DETAILS)
    self.client.projects_occurrences.List.Expect(
        request=self.messages.ContaineranalysisProjectsOccurrencesListRequest(
            parent='projects/my-project',
            pageSize=1000,
            filter=('has_prefix(resource_url, "https://{repository}@")')
            .format(repository=str(self._repository))),
        response=self.messages.ListOccurrencesResponse(
            occurrences=[bdo, pvo]))

    # occurrences is a map from resource url to occurrences list
    occurrences = util.FetchOccurrences(self._repository)
    self.assertEqual([bdo], occurrences[bdo.resourceUrl])
    self.assertEqual([pvo], occurrences[pvo.resourceUrl])

  def testFetchOccurrencesWithChunking(self):
    resource_url1 = 'https://{repository}@digest1'.format(
        repository=str(self._repository))
    resource_url2 = 'https://{repository}@digest2'.format(
        repository=str(self._repository))

    pvo1 = self.messages.Occurrence(
        resourceUrl=resource_url1,
        kind=self.messages.Occurrence.KindValueValuesEnum.PACKAGE_VULNERABILITY)
    pvo2 = self.messages.Occurrence(
        resourceUrl=resource_url2,
        kind=self.messages.Occurrence.KindValueValuesEnum.PACKAGE_VULNERABILITY)

    self.client.projects_occurrences.List.Expect(
        request=self.messages.ContaineranalysisProjectsOccurrencesListRequest(
            parent='projects/my-project',
            pageSize=1000,
            filter=(
                'has_prefix(resource_url, "https://{repository}@") AND '
                '(resource_url="{url}")')
            .format(repository=str(self._repository), url=resource_url1)),
        response=self.messages.ListOccurrencesResponse(
            occurrences=[pvo1]))
    self.client.projects_occurrences.List.Expect(
        request=self.messages.ContaineranalysisProjectsOccurrencesListRequest(
            parent='projects/my-project',
            pageSize=1000,
            filter=(
                'has_prefix(resource_url, "https://{repository}@") AND '
                '(resource_url="{url}")')
            .format(repository=str(self._repository), url=resource_url2)),
        response=self.messages.ListOccurrencesResponse(
            occurrences=[pvo2]))

    # Overwrite the constant in util.py to force chunking for two resource URLs.
    containeranalysis_util._MAXIMUM_RESOURCE_URL_CHUNK_SIZE = 1

    # occurrences is a map from resource url to occurrences list
    occurrences = util.FetchOccurrences(
        self._repository, resource_urls=[resource_url1, resource_url2])
    self.assertEqual([pvo1], occurrences[pvo1.resourceUrl])
    self.assertEqual([pvo2], occurrences[pvo2.resourceUrl])


class GetDigestFromNameTest(cli_test_base.CliTestBase,
                            sdk_test_base.WithFakeAuth):

  def testDigest(self):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    expected_digest = docker_name.Digest('{repo}@sha256:{hex_str}'.format(
        repo=repo, hex_str=hex_str))
    digest = util.GetDigestFromName(str(expected_digest))

    self.assertEqual(expected_digest, digest)

  @mock.patch('containerregistry.client.v2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image_list.FromRegistry')
  def testTagV2(self, list_registry, v2_2_registry, v2_registry):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    expected_digest = docker_name.Digest('{repo}@sha256:{hex_str}'.format(
        repo=repo, hex_str=hex_str))

    v2_registry.return_value.__enter__.return_value.exists.return_value = True
    v2_registry.return_value.__enter__.return_value.digest.return_value = (
        expected_digest.digest)
    v2_2_registry.return_value.__enter__.return_value.exists.return_value = (
        False)
    list_registry.return_value.__enter__.return_value.exists.return_value = (
        False)

    digest = util.GetDigestFromName(repo + ':foo')
    self.assertEqual(expected_digest, digest)

  @mock.patch('containerregistry.client.v2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image_list.FromRegistry')
  def testRepoV22(self, list_registry, v2_2_registry, v2_registry):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    expected_digest = docker_name.Digest('{repo}@sha256:{hex_str}'.format(
        repo=repo, hex_str=hex_str))

    v2_registry.return_value.__enter__.return_value.exists.return_value = False
    v2_2_registry.return_value.__enter__.return_value.exists.return_value = True
    v2_2_registry.return_value.__enter__.return_value.digest.return_value = (
        expected_digest.digest)
    list_registry.return_value.__enter__.return_value.exists.return_value = (
        False)

    digest = util.GetDigestFromName(repo)
    self.assertEqual(expected_digest, digest)

  @mock.patch('containerregistry.client.v2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image_list.FromRegistry')
  def testTagManifestList(self, list_registry, v2_2_registry, v2_registry):
    repo = 'gcr.io/google-appengine/java-compat'
    hex_str = '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'
    expected_digest = docker_name.Digest('{repo}@sha256:{hex_str}'.format(
        repo=repo, hex_str=hex_str))

    v2_registry.return_value.__enter__.return_value.exists.return_value = True
    v2_2_registry.return_value.__enter__.return_value.exists.return_value = (
        True)
    list_registry.return_value.__enter__.return_value.exists.return_value = (
        True)
    list_registry.return_value.__enter__.return_value.digest.return_value = (
        expected_digest.digest)

    digest = util.GetDigestFromName(repo + ':foo')
    self.assertEqual(expected_digest, digest)

  @mock.patch('containerregistry.client.v2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image.FromRegistry')
  @mock.patch('containerregistry.client.v2_2.docker_image_list.FromRegistry')
  def testUnknownRepo(self, list_registry, v2_2_registry, v2_registry):
    repo = 'gcr.io/google-appengine/java-compat'
    v2_registry.return_value.__enter__.return_value.exists.return_value = False
    v2_2_registry.return_value.__enter__.return_value.exists.return_value = (
        False)
    list_registry.return_value.__enter__.return_value.exists.return_value = (
        False)

    with self.assertRaises(util.InvalidImageNameError):
      util.GetDigestFromName(repo)


class RecoverProjectIdTest(cli_test_base.CliTestBase,
                           sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self._hex_str = ('01ba4719c80b6fe911b091a7c05124b6'
                     '4eeece964e09c058ef8f9805daca546b')

  def testGcrRegistry(self):
    self._AssertRepoProject(repo='gcr.io/google-appengine/java-compat',
                            hex_str=self._hex_str,
                            expected_project='google-appengine')

  def testMirrorRegistry(self):
    self._AssertRepoProject(repo='us-mirror.gcr.io/java-compat',
                            hex_str=self._hex_str,
                            expected_project='cloud-containers-mirror')

  def testLauncherRegistry(self):
    self._AssertRepoProject(repo='launcher.gcr.io/java-compat',
                            hex_str=self._hex_str,
                            expected_project='cloud-marketplace')

  def testDomainPrefixedRepo(self):
    self._AssertRepoProject('gcr.io/google.com/project-name/img-name',
                            hex_str=self._hex_str,
                            expected_project='google.com:project-name')

  def _AssertRepoProject(self, repo, hex_str, expected_project):
    digest = docker_name.Digest('{repo}@sha256:{hex_str}'.format(
        repo=repo, hex_str=hex_str))
    project = util.RecoverProjectId(digest)
    self.assertEqual(expected_project, project)

if __name__ == '__main__':
  test_case.main()
