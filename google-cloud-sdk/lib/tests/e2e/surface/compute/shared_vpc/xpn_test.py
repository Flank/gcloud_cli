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
"""Integration tests for Cross-Project Networking (XPN)."""
from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib
import sys

from googlecloudsdk.api_lib.compute import xpn_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import e2e_test_base


class ComputeXpnTest(e2e_test_base.BaseTest):
  _GCE_TEST_ORG = 1054311078602  # cloudsdktest.joonix.net
  _LIST_HOST_PROJECTS_TEST_ORG = 255493826784

  # Projects used in the test, indexed by major python version.
  _HOST_PROJECTS = {
      2: 'cloud-sdk-compute-xpn-test1',
      3: 'cloud-sdk-compute-xpn-test3'
  }
  _SERVICE_PROJECTS = {
      2: 'cloud-sdk-compute-xpn-test2',
      3: 'cloud-sdk-compute-xpn-test4'
  }

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    # We need to use a separate registry to use the appropriate API version.
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', xpn_api._DEFAULT_API_VERSION)
    # Choose projects based on major python version (so tests don't race)
    self.host_project = self._HOST_PROJECTS[sys.version_info.major]
    self.service_project = self._SERVICE_PROJECTS[sys.version_info.major]

  def _HostProjectUrl(self):
    project_ref = self.registry.Parse(
        self.host_project, collection='compute.projects')
    return project_ref.SelfLink()

  @contextlib.contextmanager
  def _EnableXpnProject(self, project_id):
    self.Run('compute shared-vpc enable {}'.format(project_id))
    try:
      yield
    finally:
      self.Run('compute shared-vpc disable {}'.format(project_id))

  @contextlib.contextmanager
  def _AddAssociatedProject(self, service_project, host_project):
    self.Run('compute shared-vpc associated-projects add {} '
             '--host-project={}'.format(service_project, host_project))
    try:
      yield
    finally:
      self.Run('compute shared-vpc associated-projects remove {} '
               '--host-project={}'.format(service_project, host_project))

  # This is a hack: the XPN functionality requires multiple projects, but we
  # don't have the ability to create projects on demand. Therefore, we're
  # subject to race conditions. This decorator minimizes (but does not
  # eliminate) the risk of race conditions.
  @test_case.Filters.RunOnlyOnLinux('Artificially limit run frequency.')
  def testXpn(self):
    with self._EnableXpnProject(self.host_project):
      self.AssertErrContains('Updated [{0}].'.format(self._HostProjectUrl()))
      self.ClearOutput()
      self.ClearErr()

      with self._AddAssociatedProject(self.service_project, self.host_project):
        self.AssertErrContains('Updated [{0}].'.format(self._HostProjectUrl()))
        self.ClearOutput()
        self.ClearErr()

        self.Run('compute shared-vpc get-host-project {}'.format(
            self.service_project))
        self.AssertOutputContains(self.host_project)
        self.ClearOutput()
        self.ClearErr()

        self.Run('compute shared-vpc organizations list-host-projects '
                 '{}'.format(self._LIST_HOST_PROJECTS_TEST_ORG))
        self.AssertErrMatches(r'Listed \d+ items.')
        self.ClearOutput()
        self.ClearErr()
      self.AssertErrContains('Updated [{0}].'.format(self._HostProjectUrl()))
      self.ClearOutput()
      self.ClearErr()
    self.AssertErrContains('Updated [{0}].'.format(self._HostProjectUrl()))
    self.ClearOutput()
    self.ClearErr()


if __name__ == '__main__':
  e2e_test_base.main()
