# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Module for os-config test calliope_base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.compute.os_config import osconfig_utils
from tests.lib import cli_test_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


class OsConfigBaseTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Base class for gcloud os-config unit tests."""

  def Project(self):
    """Overrides."""
    return 'my-project'

  def SetUpMockApis(self, release_track):
    self.messages = osconfig_utils.GetClientMessages(release_track)
    self.mock_osconfig_client = api_mock.Client(
        osconfig_utils.GetClientClass(release_track),
        real_client=osconfig_utils.GetClientInstance(release_track))
    self.mock_osconfig_client.Mock()
    self.addCleanup(self.mock_osconfig_client.Unmock)

  def CreatePatchJob(self,
                     project,
                     name,
                     filter='id=*',
                     description=None,
                     dry_run=False,
                     duration=None,
                     patch_config=None,
                     state=None):
    return self.messages.PatchJob(
        name=osconfig_utils.GetPatchJobUriPath(project, name),
        filter=filter,
        description=description,
        dryRun=dry_run,
        duration=duration,
        patchConfig=patch_config,
        state=state,
        instanceDetailsSummary=self.messages.InstanceDetailsSummary(
            instancesSucceeded=1))


class OsConfigE2EBaseTest(e2e_test_base.BaseTest):
  """Base class for gcloud os-config e2e tests."""

  def GetInstanceName(self, prefix):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up.
    return next(e2e_utils.GetResourceNameGenerator(prefix=prefix))

  def CreateInstance(self, name):
    # Update seek position, in reference to e2e_test_base's CreateInstance.
    self.GetNewErr()
    self.Run('compute instances create {0} --zone {1}'
             ' --scopes cloud-platform'
             ' --metadata os-patch-enabled=true'.format(name, self.zone))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Created')
    return stderr

  def GetPatchJobId(self, path):
    return path.split('/')[-1]
