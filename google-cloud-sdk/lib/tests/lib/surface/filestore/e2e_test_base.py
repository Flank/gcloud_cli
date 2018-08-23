# -*- coding: utf-8 -*- #
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
"""Module for instance integration test base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import logging
import random

from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from six.moves import range


class InstancesTestBase(e2e_base.WithServiceAuth):
  """Base Class for integration tests of Instances.

    Attributes:
      stdout_seek: An integer indicating the byte position in stdout to read.
      stderr_seek: An integer indicating the byte position in stderr to read.
      instance_names_used: Set of instance names that were created for testing.
      location: The zone to create/delete Filestore instances.
      track: The launch track for Cloud Filestore gcloud (ie. Alpha, Beta).

    Typical usage example:

    class InstancesTests(e2e_instances_test_base.InstancesTestBase):
      def test(self):
        name = self.GetInstanceName()
        args = ''
        with self.CreateInstance(name, args) as instance:
          self.Run('filestore instances list --location {}'.format(
            self.location))
  """

  def SetUp(self):
    self.stdout_seek = 0
    self.stderr_seek = 0
    self.instance_names_used = set()
    self.location = 'us-central1-c'
    self.track = base.ReleaseTrack.ALPHA

  def TearDown(self):
    logging.info('Starting TearDown (will delete instance if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name)

  @contextlib.contextmanager
  def CreateInstance(self, name, location, args=''):
    try:
      resource = self.Run('filestore instances create {} --location {} {}'
                          .format(name, location, args))
      yield resource
    finally:
      # Any test failure will hit this try-finally block and run the delete
      # command.
      self.Run(
          'filestore instances delete {} --location {}'.format(
              name, location))

  def GetInstanceName(self, prefix):
    # Make sure a new name is used if the test is retried, and make sure all
    # used names get cleaned up.
    return next(e2e_utils.GetResourceNameGenerator(prefix=prefix))

  def GetNewOutput(self):
    self.stdout.seek(self.stdout_seek)
    new_output = self.stdout.read()
    self.stdout_seek = self.stdout.tell()
    return new_output

  def GetNewErr(self):
    self.stderr.seek(self.stderr_seek)
    new_err = self.stderr.read()
    self.stderr_seek = self.stderr.tell()
    return new_err

  def AssertNewOutputContains(self, expected):
    new_output = self.GetNewOutput()
    if expected not in new_output:
      self.fail('stdout does not contain expected message [{0}]: [{1}]'.format(
          expected, new_output))

  def AssertNewOutputNotContains(self, expected):
    new_output = self.GetNewOutput()
    if expected in new_output:
      self.fail('stdout contains unexpected message [{0}]: [{1}]'.format(
          expected, new_output))

  def AssertNewErrContains(self, expected):
    new_err = self.GetNewErr()
    if expected not in new_err:
      self.fail('stderr does not contain expected message [{0}]: [{1}]'.format(
          expected, new_err))

  def AssertNewErrNotContains(self, expected):
    new_err = self.GetNewErr()
    if expected in new_err:
      self.fail('stderr contains unexpected message [{0}]: [{1}]'.format(
          expected, new_err))

  def NonDefaultRandCIDR(self):
    """Generates a randomly valid /29 CIDR block.

    NonDefaultRandCIDR gets a random /29 CIDR block in the 10.0.0.0/8 range,
    excluding [10.128.0.0, 10.155.0.0), which is partially used
    by the default network, which we know our consumer project will use.
    There are approximately 1.8 million CIDRs we can randomly choose from,
    so the chances of collision are small.

    Returns:
      A string representing the randomly valid IP range.
    """
    # Only use the 10.0.0.0/8 range for simplicity.
    first_octet = 10
    # Don't use between 10.128.0.0 and 10.155.0.0, which is used by default
    # network.
    second_octet = random.choice(list(range(0, 127)) + list(range(156, 255)))
    third_octet = random.randint(0, 255)
    # Only use the first IP in a 29 block.
    fourth_octet = random.randint(0, 31) << 3
    return '{0}.{1}.{2}.{3}/29'.format(first_octet, second_octet, third_octet,
                                       fourth_octet)
