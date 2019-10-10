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
"""Integration tests for bigtable command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import platforms
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import exec_utils
from tests.lib import sdk_test_base
from tests.lib import test_case


class BigtableIntegrationTest(sdk_test_base.BundledBase,
                              e2e_base.WithServiceAuth):
  """Integration tests for bigtable command group."""

  def RunB(self, command):
    self.Run('beta bigtable ' + command)

  def RunCbt(self, args, expected=None):
    cert_file = 'security/cacerts/for_connecting_to_google/roots.pem'
    if os.path.isfile(cert_file):
      args = [
          '-cert-file', 'security/cacerts/for_connecting_to_google/roots.pem'
      ] + args

    try:
      result = (self.ExecuteLegacyScript('cbt.exe', args)
                if platforms.OperatingSystem.IsWindows() else
                self.ExecuteScript('cbt', args))
      self.assertEqual(0, result.return_code)
      if expected is not None:
        self.assertIn(expected, result.stdout)
      return result
    except exec_utils.ExecutionError as e:
      self.fail('Error {e} could not execute cbt {argstr}.'.format(
          e=e, argstr=' '.join(args)))

  def SetUp(self):
    id_gen = e2e_utils.GetResourceNameGenerator(prefix='btinstanc')
    self.instance = next(id_gen)
    self.cluster = next(id_gen)
    self.table = next(id_gen)
    self.family = next(id_gen)
    self.row = next(id_gen)
    self.column = next(id_gen)
    self.value = next(id_gen)

    # Create an instance.
    self.RunB('instances create {0} --cluster {1} --cluster-num-nodes 3 '
              '--cluster-zone us-central1-b --display-name {0}'.format(
                  self.instance, self.cluster))

  def TearDown(self):
    # Delete the instance; confirm it is gone.
    self.RunB('instances delete {0}'.format(self.instance))
    self.ClearOutput()
    self.RunB('instances list')
    self.AssertOutputNotContains(self.instance)

  def testMainOps(self):
    """Test instance creation, instance list, cluster list, instance delete."""

    # Confirm the instance exists.
    self.ClearOutput()
    self.RunB('instances list')
    self.AssertOutputContains(self.instance)

    # Update the instance description.
    self.RunB('instances update {0} --display-name '
              '"My New Description"'.format(self.instance))

    # Describe the instance and verify the new description.
    self.ClearOutput()
    self.RunB('instances describe {0}'.format(self.instance))
    self.AssertOutputContains('My New Description')

    # Confirm the cluster within the instance exists.
    self.ClearOutput()
    self.RunB('clusters list --instances {0}'.format(self.instance))
    self.AssertOutputContains(self.cluster)

  @sdk_test_base.Filters.RunOnlyInBundle  # Requires cbt component
  def testCbtOps(self):
    """Make sure cbt operations work."""
    result = self.RunCbt(['listinstances'], self.instance)

    self.RunCbt(['-instance', self.instance, 'createtable', self.table])
    self.RunCbt(['-instance', self.instance, 'ls'], self.table)
    self.RunCbt(
        ['-instance', self.instance, 'createfamily', self.table, self.family])
    self.RunCbt([
        '-instance', self.instance, 'set', self.table, self.row,
        '%s:%s=%s' % (self.family, self.column, self.value)
    ])

    self.ClearOutput()
    result = self.RunCbt(
        ['-instance', self.instance, 'read', self.table,
         'start=%s' % self.row], self.value)
    self.assertIn(self.row, result.stdout)
    self.assertIn(self.column, result.stdout)


if __name__ == '__main__':
  test_case.main()
