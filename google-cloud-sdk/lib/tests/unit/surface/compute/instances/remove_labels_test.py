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
"""Tests for the instances remove-labels subcommand."""

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import instances_labels_test_base


class RemoveLabelsTest(instances_labels_test_base.InstancesLabelsTestBase):
  """Instances remove-labels test."""

  def testUpdateWithLabelsAndRemoveLabels(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )
    edited_labels = (('key2', 'value2'), ('key3', 'value3'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint='fingerprint-42')
    updated_instance = self._MakeInstanceProto(
        instance_ref, labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'atlanta')
    operation = self._MakeOperationMessage(operation_ref, instance_ref)

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(instance_ref, updated_instance)

    response = self.Run(
        'compute instances remove-labels {} --labels key1,key0'
        .format(instance_ref.SelfLink()))
    self.assertEqual(response, updated_instance)

  def testRemoveAll(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint='fingerprint-42')
    updated_instance = self._MakeInstanceProto(instance_ref, labels={})

    operation_ref = self._GetOperationRef('operation-1', 'atlanta')
    operation = self._MakeOperationMessage(operation_ref, instance_ref)

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref, {}, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(instance_ref, updated_instance)

    response = self.Run(
        'compute instances remove-labels {} --all'
        .format(instance_ref.SelfLink()))
    self.assertEqual(response, updated_instance)

  def testRemoveNonExisting(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(instance_ref, instance)

    response = self.Run(
        'compute instances remove-labels {} --labels DoesNotExist'
        .format(instance_ref.SelfLink()))
    self.assertEqual(response, instance)

  def testRemoveWithNoLabelsOnInstance(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')
    instance = self._MakeInstanceProto(
        instance_ref, labels={}, fingerprint='fingerprint-42')

    self._ExpectGetRequest(instance_ref, instance)

    response = self.Run(
        'compute instances remove-labels {} --labels DoesNotExist'
        .format(instance_ref.SelfLink()))
    self.assertEqual(response, instance)

  def testNoLabelsOrAllSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--all | --labels) must be specified.'):
      self.Run('compute instances remove-labels instance-1')

  def testResourceNotFound(self):
    instance_ref = self._GetInstanceRef('some-instance', zone='atlanta')
    error = http_error.MakeHttpError(
        code=404,
        message='some-instance was not found',
        reason='NOT FOUND',
        content={},
        url='')

    self._ExpectGetRequest(
        instance_ref=instance_ref, instance=None, exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'NOT FOUND: some-instance was not found'):
      self.Run(
          'compute instances remove-labels {} --all'
          .format(instance_ref.SelfLink()))


if __name__ == '__main__':
  test_case.main()
