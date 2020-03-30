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
"""Integration tests for the datalab command."""

# TODO(b/64032647): Move this under //cloud/sdk/component_build/bundle_tests/

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import e2e_instances_test_base


class DatalabIntegrationTest(sdk_test_base.BundledBase,
                             e2e_instances_test_base.InstancesTestBase):
  """Integration tests for the datalab command.

  This inherits from the BundledBase class because it relies on the full SDK
  bundle being installed, and it inherits from the InstancesTestBase class
  because it creates VM instances, and that class will ensure the created
  instances are deleted if the test fails.
  """

  _SUCCESS_MSG = 'The connection to Datalab is now open'

  def SetUp(self):
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='datalab-test-network'))

  def TearDown(self):
    # Once we get to the teardown method, all we have to do is make
    # sure the test does not leave any project resources lying around.
    # This is more a matter of defense-in-depth rather than requirement,
    # as these resources will be cleaned up by the periodic test resource
    # cleaner if this step fails. As such, we only wait a short period
    # for the cleanups to complete, and then ignore all errors (other
    # than logging them).
    try:
      with self.ExecuteScript(
          'gcloud',
          ['compute', 'firewall-rules', 'delete', '--quiet',
           '{}-allow-ssh'.format(self.network_name)],
          timeout=30):
        pass
    except Exception as e:  # pylint: disable=broad-except
      # This can happen if the firewall rule was not created to begin with.
      # pylint: disable=logging-too-many-args
      logging.info('Error cleaning up the firewall-rule: %s. '
                   'This may not be an issue, look above for details', e)
    try:
      with self.ExecuteScript(
          'gcloud',
          ['compute', 'networks', 'delete', '--quiet', self.network_name],
          timeout=30):
        pass
    except Exception as e:  # pylint: disable=broad-except
      # This can happen if the network was not created to begin with.
      # pylint: disable=logging-too-many-args
      logging.info('Error cleaning up the network: %s. '
                   'This may not be an issue, look above for details', e)

  def RunDatalab(self, args, timeout=None):
    result = self.ExecuteScript('datalab', args, timeout=timeout)
    self.assertEqual(0, result.return_code, msg=str(result))
    self.assertNotIn('WARNING', result.stderr)
    return result

  @sdk_test_base.Filters.RunOnlyInBundle  # Requires datalab component
  def testDependencySetup(self):
    """Test the logic to setup dependencies."""
    self._TestSetup()
    self._TestDelete()
    return

  @sdk_test_base.Retry(why='b/64398640', max_retrials=3, sleep_ms=5000)
  def _TestSetup(self, machine_type=None):
    self._TestInstanceCreation(machine_type, create_repo=True)

    self.Run(
        'compute firewall-rules list --filter="network~^.*/' +
        self.network_name + '?"')
    self.AssertNewOutputContains(self.network_name + '-allow-ssh')
    self.Run('source repos list')
    self.AssertNewOutputContains('datalab-notebooks')
    return

  @sdk_test_base.Filters.RunOnlyInBundle  # Requires datalab component
  def testCreateAndDelete(self):
    self._TestInstanceCreationOnly()
    self._TestDelete()
    return

  def _TestInstanceCreationOnly(self, machine_type=None):
    self._TestInstanceCreation(machine_type)
    return

  def _TestInstanceCreation(self, machine_type=None, create_repo=False):
    """Test the create step."""
    self.GetInstanceName()
    create_cmd = ['create', '--zone', self.zone,
                  '--network-name', self.network_name,
                  '--image', 'gcr.io/cloud-datalab/mock-datalab',
                  '--quiet', '--no-connect']
    if not create_repo:
      create_cmd += ['--no-create-repository']
    if machine_type:
      create_cmd += ['--machine-type', machine_type]
    create_cmd.append(self.instance_name)
    create_result = self.RunDatalab(create_cmd, timeout=180)
    self.assertIn(
        'Creating the instance {0}'.format(self.instance_name),
        create_result.stdout)

    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)

    self.Run('compute instances describe '
             '--format=value(networkInterfaces.accessConfigs[0]) '
             '--zone {0} {1}'.format(self.zone, self.instance_name))
    self.AssertNewOutputContains('natIP')
    return

  def _TestDelete(self):
    self.RunDatalab([
        'delete', '--zone', self.zone, '--quiet',
        '--delete-disk', self.instance_name])
    return


if __name__ == '__main__':
  test_case.main()
