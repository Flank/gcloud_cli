# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Integration tests for container node pools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container import base as testbase


class NodePoolsTestGA(testbase.IntegrationTestBase, parameterized.TestCase):

  def SetUp(self):
    self.releasetrack = calliope_base.ReleaseTrack.GA
    self.cluster_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='update-test'))
    self.network = 'do-not-delete-node-pools-ga'
    self.cluster_creation_timeout = 18 * 60  # leave 2 minutes for enabling
    # autoupgrade

  def _FormatNameAndLocation(self, location):
    """Helper function.

    Args:
      location: pre-formatted '--(zone|region)=<(zone|region) name>' string

    Returns:
      str: a string formatted with the provided values.
    """
    return '{name} {location}'.format(name=self.cluster_name, location=location)

  @contextlib.contextmanager
  def _CreateCluster(self, location, track):
    try:
      log.status.Print('Creating cluster {0}'.format(self.cluster_name))
      result = self.Run(
          'container clusters create {0} '
          '--network {1} '
          '--no-enable-autoupgrade '  # explicit since the default is
          # `--enable-autoupgrade`
          '--num-nodes=1 '
          '--timeout {2}'.format(
              self._FormatNameAndLocation(location),
              self.network,
              self.cluster_creation_timeout
          ), track=track
      )
      yield result
    except core_exceptions.Error as e:
      if 'is still running' in e.args[0]:
        raise core_exceptions.Error(
            'Creation of cluster {0} took longer than {1} minutes.'.format(
                self.cluster_name,
                int(self.cluster_creation_timeout / 60))
        )
      else:
        raise

    finally:
      try:
        log.status.Print('Cleaning up {}'.format(self.cluster_name))
        # Make cluster deletion asynchronous until gcloud allows a timeout
        # longer than 20 minutes.
        self.Run(
            'container clusters delete {name_and_location} --async -q'.format(
                name_and_location=self._FormatNameAndLocation(location)
            )
        )
      except core_exceptions.Error as error:
        log.warning(
            'Failed to delete cluster {}:\n{}'.format(self.cluster_name, error)
        )

  @parameterized.named_parameters(
      ('Zone', 'zone'),
      ('Region', 'region')
  )
  @sdk_test_base.Filters.RunOnlyInBundle
  def testNodePoolsUpdate(self, location):
    if location == 'zone':
      location = '--zone={}'.format(self.ZONE)
    else:
      location = '--region={}'.format(self.REGION)

    track = self.releasetrack
    with self._CreateCluster(location, track):
      self.AssertErrContains('Created')
      self.AssertOutputContains(self.cluster_name)
      self.AssertOutputContains('RUNNING')
      log.status.Print('Enabling auto-upgrade for cluster %s',
                       self.cluster_name)
      self.Run(
          'container node-pools update default-pool '
          '--cluster {name_and_location} --enable-autoupgrade'.format(
              name_and_location=self._FormatNameAndLocation(location)
          ),
          track=track
      )
      self.AssertErrContains('Updated')
      node_pool = self.Run(
          'container node-pools describe default-pool '
          '--cluster {name_and_location}'.format(
              name_and_location=self._FormatNameAndLocation(location)
          )
      )
      self.assertTrue(node_pool.management.autoUpgrade)


class NodePoolsTestBeta(NodePoolsTestGA):

  def SetUp(self):
    self.releasetrack = calliope_base.ReleaseTrack.BETA
    self.ZONE = 'us-east1-d'  # pylint: disable=invalid-name
    self.REGION = 'us-east1'  # pylint: disable=invalid-name
    self.network = 'do-not-delete-node-pools-beta'


if __name__ == '__main__':
  test_case.main()
