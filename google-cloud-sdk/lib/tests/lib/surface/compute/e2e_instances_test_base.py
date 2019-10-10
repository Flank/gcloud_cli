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
"""Module for instance integration test base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import os.path

from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class InstancesTestBase(e2e_test_base.BaseTest):
  """Base Class for integration tests of Instances."""

  def SetUp(self):
    self.instance_names_used = []
    # No hash on login name, since we really only care about the timestamp
    self.logname = next(
        e2e_utils.GetResourceNameGenerator(prefix='bundledtest', hash_len=0))
    self.home_dir = self.CreateTempDir(name=os.path.join('home', self.logname))
    self.ssh_dir = self.CreateTempDir(name=os.path.join(self.home_dir, '.ssh'))
    self.private_key_file = os.path.join(self.ssh_dir, 'google_compute_engine')
    self.public_key_file = self.private_key_file + '.pub'

    self.PatchEnvironment()

  def TearDown(self):
    logging.info('Starting TearDown (will delete instance if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure a new name is used if the test is retried, and make sure all
    # used names get cleaned up
    name = next(
        e2e_utils.GetResourceNameGenerator(prefix='gcloud-compute-test'))
    self.instance_name = name
    self.instance_names_used.append(name)
    return name

  def _TestInstanceCreation(self, metadata=None):
    self.GetInstanceName()
    # metadata should be a dictionary of key/value pairs to add to the
    # instance metadata.
    metadata_flag = ''
    if metadata:
      # Convert the metadata dictionary to a comma-separated string of 'a=b'
      # pairs. e.g. {'a':'b', 'c':'d'} ==> 'a=b,c=d'
      metadata_values = ','.join('='.join(item) for item in metadata.items())
      metadata_flag = '--metadata {0}'.format(metadata_values)
    self.Run('compute instances create {0} --zone {1} {2}'.format(
        self.instance_name, self.zone, metadata_flag))
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)
