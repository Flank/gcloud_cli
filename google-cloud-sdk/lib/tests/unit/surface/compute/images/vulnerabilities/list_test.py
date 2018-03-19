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
"""Tests for images vulnerabilities list subcommand."""
from apitools.base.py import list_pager
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ListTest(
    sdk_test_base.WithFakeAuth,
    cli_test_base.CliTestBase,
    sdk_test_base.WithOutputCapture):
  """Test `images vulnerabilities list` command.

  These tests assume that there are some existing Occurrences listed by the
  occurrences.List API call, and that *which* Occurrences are returned is
  determined by the "filter" field using Cloud filtering semantics.

  To that end, we fake out the List API to just return the matching set of
  resources using our implementation of filtering.
  """

  def _MakeOccurrence(self, image, name, note_id, image_project=None):
    severity = self.messages.VulnerabilityDetails.SeverityValueValuesEnum
    kind = self.messages.Occurrence.KindValueValuesEnum
    vulnerability_details = self.messages.VulnerabilityDetails(
        severity=severity.MINIMAL,
        cvssScore=2.71,
        packageIssue=[
            self.messages.PackageIssue(
                affectedLocation=self.messages.VulnerabilityLocation(
                    package='foobar',
                )
            )
        ]
    )

    image_project = image_project or self.Project()
    resource_url = (
        'https://www.googleapis.com/compute/alpha'
        '/projects/{}/global/images/{}').format(image_project, image)

    return self.messages.Occurrence(
        resourceUrl=resource_url,
        noteName='providers/goog-vulnz/notes/{}'.format(note_id),
        name=name,
        kind=kind.PACKAGE_VULNERABILITY,
        vulnerabilityDetails=vulnerability_details)

  def _MakeOccurences(self, filter_):
    kind = self.messages.Occurrence.KindValueValuesEnum

    build_details = self._MakeOccurrence(
        image='atli/id/33333', name='build_details', note_id='CVE-2018-3333',
        image_project='other-project')
    build_details.kind = kind.BUILD_DETAILS

    max_fixed_package_issue = self.messages.PackageIssue(
        fixedLocation=self.messages.VulnerabilityLocation(
            package='gcc',
            version=self.messages.Version(
                kind=self.messages.Version.KindValueValuesEnum.MAXIMUM
            )
        ),
        affectedLocation=self.messages.VulnerabilityLocation(
            package='gcc',
            version=self.messages.Version(
                kind=self.messages.Version.KindValueValuesEnum.NORMAL
            )
        )
    )
    normal_fixed_package_issue = self.messages.PackageIssue(
        fixedLocation=self.messages.VulnerabilityLocation(
            package='g++',
            version=self.messages.Version(
                kind=self.messages.Version.KindValueValuesEnum.MAXIMUM
            )
        ),
        affectedLocation=self.messages.VulnerabilityLocation(
            package='g++',
            version=self.messages.Version(
                kind=self.messages.Version.KindValueValuesEnum.NORMAL
            )
        )
    )
    any_fixed_max_version = self._MakeOccurrence(
        image='atli/id/44444', name='any_fixed_max_version',
        note_id='CVE-2018-4444')
    any_fixed_max_version.vulnerabilityDetails.packageIssue = [
        max_fixed_package_issue, normal_fixed_package_issue
    ]

    all_fixed_max_version = self._MakeOccurrence(
        image='atli/id/55555', name='all_fixed_max_version',
        note_id='CVE-2018-5555')
    all_fixed_max_version.vulnerabilityDetails.packageIssue = [
        max_fixed_package_issue, max_fixed_package_issue
    ]

    occurrences = [
        self._MakeOccurrence(image='atli/id/11111', name='foo',
                             note_id='CVE-2018-1111',
                             image_project='other-project'),
        self._MakeOccurrence(image='my-image', name='foo2',
                             note_id='CVE-2018-2222'),
        build_details,
        any_fixed_max_version,
        all_fixed_max_version
    ]

    query = resource_filter.Compile(filter_)
    # Need to make serializable for filter to match enums
    return [o for o in occurrences if
            query.Evaluate(resource_projector.MakeSerializable(o))]

  def _MockYieldFromList(self):
    old_yield = list_pager.YieldFromList
    def _FakeYield(service, request, **kwargs):
      self.mock_client.projects_occurrences.List.Expect(
          self.messages.ContaineranalysisProjectsOccurrencesListRequest(
              filter=request.filter,
              pageSize=1000,
              parent='projects/fake-project'
          ),
          self.messages.ListOccurrencesResponse(
              occurrences=self._MakeOccurences(filter_=request.filter)
          )
      )
      return old_yield(service, request, **kwargs)
    self.StartObjectPatch(list_pager, 'YieldFromList', _FakeYield)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('containeranalysis', 'v1alpha1'),
        real_client=core_apis.GetClientInstance(
            'containeranalysis', 'v1alpha1', no_http=True),
    )
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')

  def testListVulnerabilities(self):
    self._MockYieldFromList()

    self.Run('compute images vulnerabilities list')

    self.AssertOutputEquals("""\
NAME NOTE SEVERITY CVSS_SCORE PACKAGES
foo CVE-2018-1111 MINIMAL 2.71 foobar
foo2 CVE-2018-2222 MINIMAL 2.71 foobar
""", normalize_space=True)

  def testListVulnerabilities_OverrideFilter(self):
    self._MockYieldFromList()

    self.Run('compute images vulnerabilities list --filter ""')

    self.AssertOutputEquals("""\
NAME NOTE SEVERITY CVSS_SCORE PACKAGES
foo CVE-2018-1111 MINIMAL 2.71 foobar
foo2 CVE-2018-2222 MINIMAL 2.71 foobar
any_fixed_max_version CVE-2018-4444 MINIMAL 2.71 gcc,g++
all_fixed_max_version CVE-2018-5555 MINIMAL 2.71 gcc,gcc
""", normalize_space=True)

  def testListVulnerabilities_SpecifyImage(self):
    self._MockYieldFromList()

    self.Run('compute images vulnerabilities list --image my-image')

    self.AssertOutputEquals("""\
NAME NOTE SEVERITY CVSS_SCORE PACKAGES
foo2 CVE-2018-2222 MINIMAL 2.71 foobar
""", normalize_space=True)

  def testListVulnerabilities_Format(self):
    self._MockYieldFromList()

    self.Run('compute images vulnerabilities list')

    self.AssertOutputEquals("""\
NAME NOTE SEVERITY CVSS_SCORE PACKAGES
foo CVE-2018-1111 MINIMAL 2.71 foobar
foo2 CVE-2018-2222 MINIMAL 2.71 foobar
""", normalize_space=True)
