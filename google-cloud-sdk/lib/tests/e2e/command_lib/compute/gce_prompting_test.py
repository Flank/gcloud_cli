# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for differences between running on GCE and locally."""

import argparse
import contextlib
import logging
import re
import textwrap

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce as c_gce
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base

import mock


class GCloudComputeOnGCE(e2e_test_base.BaseTest):
  """End-to-end for resolving GCE zone/region properties on GCP."""

  def SetUp(self):
    self.instance_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-on-gce').next()
    self.instance_name = name
    self.instance_names_used.append(name)
    return name

  @contextlib.contextmanager
  def AnswerPromptForZone(self, zone):
    # self.Run() prints list of zones and blocks waiting for input. We can't
    # guess zone number before calling self.Run().
    # We are patching self.stderr.write to capture and extract information from
    # prompt. We need number of the zone. When information is printed
    # we extract it in patched_write and call self.WriteInput to provide
    # necessary input for blocked self.Run().
    real_write = self.stderr.write
    closure = argparse.Namespace()  # Eventually move to nonlocal when available
    closure.count = 0
    def patched_write(s):
      real_write(s)  # Do not replace - only decorate
      # This assumes zone line is written as a whole
      match = re.search(r'\[(\d+)]\s{}'.format(zone), s)
      if match:
        closure.count += 1
        self.WriteInput(match.group(1))
    patcher = mock.patch.object(self.stderr, 'write', patched_write)
    patcher.start()
    try:
      yield
    finally:
      patcher.stop()
      self.assertEqual(closure.count, 1,
                       'Expected exactly one occurrence of "{}", got {}'
                       .format(zone, closure.count))

  @sdk_test_base.Filters.DoNotRunOnGCE
  def testInstanceCreationNoGCE(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.GetInstanceName()
    with self.AssertRaisesToolExceptionRegexp(
        re.compile(
            ('.*Could not fetch.*projects/cloud-sdk-integration-testing/zones/'
             'us-central1-f/instances/{0}.*').
            format(self.instance_name), re.S)):
      with self.AnswerPromptForZone('us-central1-f'):
        self.Run('compute instances describe {0}'.format(self.instance_name))
    self.AssertNewErrContains(textwrap.dedent("""
        For the following instance:
         - [{0}]
        choose a zone:
         [1]""".format(self.instance_name)))

    self.Run('compute instances list')
    self.AssertNewOutputNotContains(self.instance_name)

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testInstanceDescriptionOnGCE(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    properties.VALUES.core.check_gce_metadata.Set(True)
    self.GetInstanceName()
    current_zone = c_gce.Metadata().Zone()
    self.assertNotEqual(current_zone, None)

    with self.AssertRaisesToolExceptionRegexp(
        re.compile(
            ('.*Could not fetch.*projects/cloud-sdk-integration-testing/zones/'
             '{0}/instances/{1}.*').
            format(current_zone, self.instance_name), re.S)):
      self.WriteInput('y\n')
      self.Run('compute instances describe {0}'.format(self.instance_name))
    self.AssertNewErrContains(
        'Did you mean zone [{0}] for instance: [{1}]'.format(
            current_zone, self.instance_name))

    self.Run('compute instances list')
    self.AssertNewOutputNotContains(self.instance_name)

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testInstanceCreationOnGCE(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    properties.VALUES.core.check_gce_metadata.Set(True)
    self.GetInstanceName()
    current_zone = c_gce.Metadata().Zone()
    self.assertNotEqual(current_zone, None)

    self.WriteInput('y\n')
    self.Run('compute instances create {0}'.format(self.instance_name))
    self.AssertNewErrContains(
        'Did you mean zone [{0}] for instance: [{1}]'.format(
            current_zone, self.instance_name))

    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)


if __name__ == '__main__':
  e2e_test_base.main()
