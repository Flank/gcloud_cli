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
"""Integration tests for creating/using/deleting instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class InstancesTest(e2e_instances_test_base.InstancesTestBase):

  def testInstances(self):
    self._TestInstanceCreation()
    self._TestInstanceDeletion()

  def _TestInstanceDeletion(self):
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)
    self.WriteInput('y\n')
    self.Run('compute instances delete {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following instances will be deleted', reset=False)
    self.AssertNewErrContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputNotContains(self.instance_name)

  def testCustomInstanceCreationErrors(self):
    self.GetInstanceName()
    with self.assertRaisesRegex(exceptions.ToolException,
                                r'Memory size for a 2 vCPU instance must be '
                                'between'):
      self.Run('compute instances create {0} --custom-cpu 2 '
               '--custom-memory 14 --zone {1}'.format(self.instance_name,
                                                      self.zone))
    with self.assertRaisesRegex(exceptions.ToolException,
                                r'Memory should be a multiple of 256MiB'):
      self.Run('compute instances create {0} '
               '--custom-cpu 2 --custom-memory '
               '3000MiB --zone {1}'.format(self.instance_name, self.zone))
    with self.assertRaisesRegex(exceptions.ToolException,
                                r'Number of vCPUs should be an even number if '
                                'greater than 1'):
      self.Run('compute instances create {0} '
               '--custom-cpu 3 --custom-memory '
               '10 --zone {1}'.format(self.instance_name, self.zone))

  def testMetadataAdditionDeletion(self):
    self.GetInstanceName()
    self.Run('compute instances create {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputNotContains('key: apple')

    self.Run('compute instances add-metadata {0} --zone {1}'
             ' --metadata="apple=a day"'.format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputContainsAll(['key: apple', 'value: a day'])

    self.Run('compute instances remove-metadata {0} --zone {1}'
             ' --keys="apple"'.format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputNotContains('key: apple')

  def testImprovedMissingmachineTypeErrorMessage(self):
    self.GetInstanceName()
    with self.assertRaisesRegex(
        exceptions.ToolException,
        r'Use `gcloud compute machine-types list --zones` to see the available '
        r'machine  types.'):
      self.Run('compute instances create {0} --zone {1} '
               '--machine-type fake-type'.format(
                   self.instance_name, self.zone))


class LabelsTest(e2e_instances_test_base.InstancesTestBase):
  """Instance add/remove labels tests and labels support during creation."""

  def SetUp(self):
    self.track = base.ReleaseTrack.GA

  def testCreateWithLabels(self):
    instance_labels = (('x', 'y'), ('abc', 'xyz'))
    self.GetInstanceName()
    self.Run('compute instances create {0} --zone {1} --labels {2}'
             .format(self.instance_name, self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in instance_labels])))
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

  def testAddRemoveLabels(self):
    self.GetInstanceName()

    self.Run('compute instances create {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute instances add-labels {0} --zone {1} --labels {2}'
             .format(self.instance_name,
                     self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')
    self.ClearOutput()

    remove_labels = ('abc',)
    self.Run('compute instances remove-labels {0} --zone {1} --labels {2}'
             .format(self.instance_name,
                     self.zone,
                     ','.join(['{0}'.format(k)
                               for k in remove_labels])))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('x: y', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')

    self.Run('compute instances remove-labels {0} --zone {1} --all '
             .format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputNotContains('labels')

  def testUpdateLabels(self):
    self.GetInstanceName()

    self.Run('compute instances create {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute instances update {0} --zone {1} --update-labels {2}'
             .format(self.instance_name,
                     self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    update_labels = (('x', 'a'), ('abc', 'xyz'), ('t123', 't7890'))
    remove_labels = ('abc',)
    self.Run(
        """
         compute instances update {0} --zone {1}
             --update-labels {2} --remove-labels {3}
        """
        .format(self.instance_name,
                self.zone,
                ','.join(['{0}={1}'.format(pair[0], pair[1])
                          for pair in update_labels]),
                ','.join(['{0}'.format(k)
                          for k in remove_labels])))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContainsAll(['t123: t7890', 'x: a'], reset=False)
    self.AssertNewOutputNotContains('abc: xyz')


class DeletionProtectionTest(e2e_instances_test_base.InstancesTestBase):
  """Instance deletion protection tests."""

  def _DeleteInstance(self, instance_name):
    """Clean up method that handles unsetting deletion protection attribute."""
    try:
      self.Run('compute instances update {0} --zone {1} '
               '--no-deletion-protection'.format(instance_name, self.zone))
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))
    except:  # pylint:disable=bare-except
      # If these fail, it's probably because the instances were alreay deleted.
      pass

  def _TestInstanceDeletion(self, instance_name, is_protected):
    self.Run('compute instances list')
    self.AssertNewOutputContains(instance_name)

    self.WriteInput('y\n')
    try:
      self.Run('compute instances delete {0} --zone {1}'.format(
          instance_name, self.zone))
    except exceptions.ToolException as e:
      if not is_protected:
        # Something else failed.
        raise e
    self.ClearInput()
    self.AssertNewErrContains(
        'The following instances will be deleted', reset=False)
    self.AssertNewErrContains(instance_name, reset=(not is_protected))
    if is_protected:
      self.AssertNewErrContains(
          'Resource cannot be deleted if it\'s protected against deletion.')

    self.Run('compute instances list')
    if is_protected:
      self.AssertNewOutputContains(instance_name)
    else:
      self.AssertNewOutputNotContains(instance_name)

  @contextlib.contextmanager
  def _TestInstanceCreation(self, deletion_protection):
    try:
      instance_name = self.GetInstanceName()
      flag_prefix = '--' if deletion_protection else '--no-'
      self.Run('compute instances create {0} --zone {1} {2}deletion-protection'
               .format(instance_name, self.zone, flag_prefix))
      self.AssertNewOutputContains(instance_name)
      self.Run('compute instances list')
      self.AssertNewOutputContains(instance_name)
      self._TestDescribeInstanceDeletionProtection(
          instance_name, deletion_protection)
      yield instance_name
    finally:
      self._DeleteInstance(instance_name)

  def _TestUpdateInstance(self, instance_name, deletion_protection):
    flag_prefix = '--' if deletion_protection else '--no-'
    self.Run('compute instances update {0} --zone {1} '
             '{2}deletion-protection'.format(
                 instance_name, self.zone, flag_prefix))
    self._TestDescribeInstanceDeletionProtection(
        instance_name, deletion_protection)

  def _TestDescribeInstanceDeletionProtection(self, instance_name,
                                              deletion_protection):
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputContains('deletionProtection: {}'.format(
        str(deletion_protection).lower()))

  def testDeletionProtection(self):
    with self._TestInstanceCreation(deletion_protection=False) as instance_name:
      self._TestUpdateInstance(instance_name, deletion_protection=True)
      self._TestInstanceDeletion(instance_name, is_protected=True)
      self._TestUpdateInstance(instance_name, deletion_protection=False)
      self._TestInstanceDeletion(instance_name, is_protected=False)


if __name__ == '__main__':
  e2e_test_base.main()
