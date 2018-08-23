# -*- coding: utf-8 -*- #
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
"""Module for integration test base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import time

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import test_case
import mock
import six
from six.moves import range  # pylint: disable=redefined-builtin


ZONE = 'us-central1-f'
REGION = 'us-central1'

GLOBAL = 'global scope'
EXPLICIT_GLOBAL = '(explicit) global scope'
ZONAL = 'zonal scope'
REGIONAL = 'regional scope'


BOOT_POLLING_INTERVAL_SECS = 10


def main():
  return test_case.main()


class BaseTest(e2e_base.WithServiceAuth):
  """Base class for compute integration tests."""

  def SetUp(self):
    self.stdout_seek = 0
    self.stderr_seek = 0
    self.track = calliope_base.ReleaseTrack.GA
    self.zone = properties.VALUES.compute.zone.Get() or ZONE
    self.alternative_zone = self.MutatedZone(self.zone)
    self.region = properties.VALUES.compute.region.Get() or REGION
    self.scope_flag = {
        ZONAL: '--zone ' + self.zone,
        REGIONAL: '--region ' + self.region,
        GLOBAL: '',
        EXPLICIT_GLOBAL: '--global'}

  def GetNewErr(self, reset=True):
    self.stderr.seek(self.stderr_seek)
    new_stderr = self.stderr.read()
    if reset:
      self.stderr_seek = self.stderr.tell()
    return new_stderr

  def ClearErr(self):
    self.GetNewErr(True)

  def AssertNewErrContains(self, expected, reset=True, normalize_space=False):
    self.AssertNewErrContainsAll([expected], reset=reset,
                                 normalize_space=normalize_space)

  def AssertNewErrContainsAll(self, expected_list, reset=True,
                              normalize_space=False):
    new_stderr = self.GetNewErr(reset=reset)
    if normalize_space:
      new_stderr = test_case.NormalizeSpace(normalize_space, new_stderr)
    for expected in expected_list:
      if normalize_space:
        expected = test_case.NormalizeSpace(normalize_space, expected)
      if expected not in new_stderr:
        self.fail('stderr does not contain expected message [{0}]: [{1}]'
                  .format(expected, new_stderr))

  def AssertNewErrNotContains(self, expected, reset=True,
                              normalize_space=False):
    new_stderr = self.GetNewErr(reset=reset)
    if normalize_space:
      new_stderr = test_case.NormalizeSpace(normalize_space, new_stderr)
      expected = test_case.NormalizeSpace(normalize_space, expected)
    if expected in new_stderr:
      self.fail('stderr contains unexpected message [{0}]: [{1}]'
                .format(expected, new_stderr))

  def GetNewOutput(self, reset=True):
    self.stdout.seek(self.stdout_seek)
    new_output = self.stdout.read()
    if reset:
      self.stdout_seek = self.stdout.tell()
    return new_output

  def ClearOutput(self):
    self.GetNewOutput(True)

  def AssertNewOutputContains(self, expected, reset=True,
                              normalize_space=False):
    self.AssertNewOutputContainsAll([expected], reset=reset,
                                    normalize_space=normalize_space)

  def AssertNewOutputContainsAll(self, expected_list, reset=True,
                                 normalize_space=False):
    new_output = self.GetNewOutput(reset=reset)
    if normalize_space:
      new_output = test_case.NormalizeSpace(normalize_space, new_output)
    for expected in expected_list:
      if normalize_space:
        expected = test_case.NormalizeSpace(normalize_space, expected)
      if expected not in new_output:
        self.fail('stdout does not contain expected message [{0}]: [{1}]'
                  .format(expected, new_output))

  def AssertNewOutputNotContains(self, expected, reset=True,
                                 normalize_space=False):
    new_output = self.GetNewOutput(reset=reset)
    if normalize_space:
      new_output = test_case.NormalizeSpace(normalize_space, new_output)
      expected = test_case.NormalizeSpace(normalize_space, expected)
    if expected in new_output:
      self.fail('stdout contains unexpected message [{0}]: [{1}]'
                .format(expected, new_output))

  def ClearInput(self):
    self.stdin.truncate(0)

  def PatchEnvironment(self, additional_env=None):
    new_env = {
        'HOME': self.home_dir,
        'LOGNAME': self.logname,
    }
    if additional_env:
      new_env.update(additional_env)
    env_patcher = mock.patch.dict('os.environ', new_env)
    self.addCleanup(env_patcher.stop)
    env_patcher.start()

  def MutatedZone(self, zone):
    """Changes zone string into some similar zone string (heuristic)."""
    if zone[-1:] == 'a':
      return zone[:-1] + 'f'
    else:
      return zone[:-1] + 'a'

  def CreateInstance(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute instances create {0} --zone {1}'
             .format(name, self.zone))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Created')
    return stderr

  def DeleteInstance(self, name):
    # TODO(b/38260200) do not capture output here and use context manager.
    # Update seek position
    self.GetNewErr()
    self.Run('compute instances delete {0} --zone {1} --quiet'
             .format(name, self.zone))
    stderr = self.GetNewErr()
    return stderr

  def DeleteInstanceByUri(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute instances delete {0} --quiet'.format(name))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Deleted')
    return stderr

  def DeleteInstanceGroup(self, name):
    # TODO(b/38260200) do not capture output here and use context manager.
    # Update seek position
    self.GetNewErr()
    self.Run(('compute instance-groups unmanaged delete {0} --zone {1} '
              '--quiet').format(name, self.zone))
    stderr = self.GetNewErr()
    return stderr

  def DeleteInstanceGroupManager(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute instance-groups managed delete {0} --zone {1} '
             '--quiet'.
             format(name, self.zone))
    stderr = self.GetNewErr()
    self.AssertErrContains(stderr, 'Deleted')
    self.AssertErrContains('Deleting Managed Instance Group')
    return stderr

  def DeleteRegionalInstanceGroupManager(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute instance-groups managed delete {0} --region {1} '
             '--quiet'.
             format(name, self.region))
    stderr = self.GetNewErr()
    self.AssertErrContains(stderr, 'Deleted')
    self.AssertErrContains('Deleting Managed Instance Group')
    return stderr

  def DeleteInstanceTemplate(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute instance-templates delete {} --quiet'.format(name))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Deleted')
    return stderr

  def DeleteTargetPool(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute target-pools delete {0} --region {1} --quiet'.
             format(name, REGION))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Deleted')
    return stderr

  def DeleteHttpHealthCheck(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute http-health-checks delete {0} --quiet'.format(name))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Deleted')
    return stderr

  def DeleteHttpsHealthCheck(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute https-health-checks delete {0} --quiet'.format(name))
    stderr = self.GetNewErr()
    self.assertStartsWith(stderr, 'Deleted')
    return stderr

  def DeleteBackendBucket(self, name):
    # TODO(b/38260200) do not capture output here and use context manager.
    # Update seek position
    self.GetNewErr()
    self.Run('compute backend-buckets delete {0} --quiet'
             .format(name))
    stderr = self.GetNewErr()
    return stderr

  def DeleteSslPolicy(self, name):
    self.GetNewErr()
    self.Run('compute ssl-policies delete {0} --quiet'.format(name))
    stderr = self.GetNewErr()
    return stderr

  def DeleteDisk(self, disk):
    # Update seek position
    self.GetNewErr()
    self.Run('compute disks delete {0} --quiet'.format(disk))
    stderr = self.GetNewErr()
    self.AssertErrContains(stderr, 'Deleted')
    return stderr

  def assertStartsWith(self, actual, expected_start):
    if not actual.startswith(expected_start):
      self.fail('{0} does not start with {1}'.format(actual, expected_start))

  def CleanUpResource(self, name, res_type, scope=ZONAL, track='GA'):
    """Attempt to clean up a resource, without signaling an error on failure."""

    try:
      self.Run('compute {0} delete {1} {2} --quiet'.format(
          res_type, name, self.scope_flag[scope]))
    except exceptions.ToolException:
      pass

  def WaitForBoot(self, name, message, retries=5,
                  polling_interval=BOOT_POLLING_INTERVAL_SECS):
    """Monitor the Serial Port for a string, and return when found.

    The default values for retries and polling_interval are probably
    appropriate for Linux instances but will need to be adjusted for
    Windows instances.

    Args:
      name: Name of instance to monitor.
      message: String to search for in serial port.
      retries: The number of times to poll the serial port before giving up.
      polling_interval: How often, in seconds, to check the serial port.

    Returns:
      boolean: True if string is found, False if it is not found before number
               of retries has been reached.
    """
    for retry in range(retries):
      time.sleep(polling_interval)
      logging.info('Checking Serial Port Output (%s of %s)',
                   retry + 1, retries)
      self.Run('compute instances get-serial-port-output {0} --zone {1}'
               .format(name, self.zone))
      new_output = self.GetNewOutput()
      if message in new_output:
        return True
    return False

  def DeleteResources(self, resource_names, delete_func, resource_type_name):
    if isinstance(resource_names, six.string_types):
      resource_names = [resource_names]
    if not isinstance(resource_names, list):
      self.fail('resource_names {0!r} is not a string nor an iterable.'.format(
          resource_names))
    for name in resource_names:
      delete_func(name)
