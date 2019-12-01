# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for compute instances vulnerabilities list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ListTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
               sdk_test_base.WithOutputCapture):
  """Test `compute instances vulnerabilities list` command.

  These tests assume that there are some existing Occurrences listed by the
  occurrences.List API call, and that *which* Occurrences are returned is
  determined by the "filter" field using Cloud filtering semantics.

  To that end, we fake out the List API to just return the matching set of
  resources using our implementation of filtering.
  """

  def _MakeOccurrence(self, instance, name, note_id, proj=None):
    severity = self.messages.VulnerabilityDetails.SeverityValueValuesEnum
    kind = self.messages.Occurrence.KindValueValuesEnum
    vulnerability_details = self.messages.VulnerabilityDetails(
        severity=severity.MINIMAL,
        cvssScore=2.71,
        packageIssue=[
            self.messages.PackageIssue(
                affectedLocation=self.messages.VulnerabilityLocation(
                    package='foobar',))
        ])

    proj = proj or self.Project()
    resource_url = ('https://www.compute.googleapis.com/compute'
                    '/projects/{}/zones/us-central1-a/instances/{}').format(
                        proj, instance)

    return self.messages.Occurrence(
        resourceUrl=resource_url,
        noteName='providers/goog-vulnz/notes/{}'.format(note_id),
        name=name,
        kind=kind.PACKAGE_VULNERABILITY,
        vulnerabilityDetails=vulnerability_details)

  def _MakeOccurences(self, filter_):
    return [
        self._MakeOccurrence(
            instance='instance1',
            name='occ1',
            note_id='CVE-2018-1111',
            proj='other-project'),
        self._MakeOccurrence(
            instance='instance2', name='occ2', note_id='CVE-2018-2222'),
    ]

  def _MockYieldFromList(self, filter_string):
    old_yield = list_pager.YieldFromList

    def _FakeYield(service, request, **kwargs):
      self.mock_client.projects_occurrences.List.Expect(
          self.messages.ContaineranalysisProjectsOccurrencesListRequest(
              filter=filter_string,
              pageSize=1000,
              parent='projects/fake-project'),
          self.messages.ListOccurrencesResponse(
              occurrences=self._MakeOccurences(filter_=request.filter)))
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
    self.messages = core_apis.GetMessagesModule('containeranalysis', 'v1alpha1')

  def testListVulnerabilities(self):
    self._MockYieldFromList(
        'kind = "PACKAGE_VULNERABILITY" AND '
        'has_prefix(resource_url, '
        '"https://www.googleapis.com/compute/projects/fake-project/zones/")')

    self.Run('compute instances vulnerabilities list')

    self.AssertOutputEquals(
        """\
NAME INSTANCE ZONE NOTE SEVERITY PACKAGES
occ1 instance1 us-central1-a CVE-2018-1111 MINIMAL foobar
occ2 instance2 us-central1-a CVE-2018-2222 MINIMAL foobar
""",
        normalize_space=True)

  def testListVulnerabilities_OverrideFilter(self):
    self._MockYieldFromList(
        'kind = "PACKAGE_VULNERABILITY" AND '
        'has_prefix(resource_url, '
        '"https://www.googleapis.com/compute/projects/fake-project/zones/")')

    self.Run('compute instances vulnerabilities list --filter ""')

    self.AssertOutputEquals(
        """\
NAME INSTANCE ZONE NOTE SEVERITY PACKAGES
occ1 instance1 us-central1-a CVE-2018-1111 MINIMAL foobar
occ2 instance2 us-central1-a CVE-2018-2222 MINIMAL foobar
""",
        normalize_space=True)

  def testListVulnerabilities_SpecifyInstance(self):
    self._MockYieldFromList(
        'kind = "PACKAGE_VULNERABILITY" AND '
        'has_prefix(resource_url, '
        '"https://www.googleapis.com/compute/projects/fake-project/'
        'zones/us-central1-a/instances/instance1")')

    self.Run('compute instances vulnerabilities list'
             ' --instance instance1 --instance-zone us-central1-a')

    self.AssertOutputEquals(
        """\
NAME INSTANCE ZONE NOTE SEVERITY PACKAGES
occ1 instance1 us-central1-a CVE-2018-1111 MINIMAL foobar
occ2 instance2 us-central1-a CVE-2018-2222 MINIMAL foobar
""",
        normalize_space=True)

  def testListVulnerabilities_Format(self):
    self._MockYieldFromList(
        'kind = "PACKAGE_VULNERABILITY" AND '
        'has_prefix(resource_url, '
        '"https://www.googleapis.com/compute/projects/fake-project/zones/")')

    self.Run('compute instances vulnerabilities list')

    self.AssertOutputEquals(
        """\
NAME INSTANCE ZONE NOTE SEVERITY PACKAGES
occ1 instance1 us-central1-a CVE-2018-1111 MINIMAL foobar
occ2 instance2 us-central1-a CVE-2018-2222 MINIMAL foobar
""",
        normalize_space=True)
