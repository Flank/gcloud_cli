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
"""Tests for instances add-labels."""

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import instances_labels_test_base


class AddLabelsTest(instances_labels_test_base.InstancesLabelsTestBase):
  """Instances add-labels test."""

  def testUpdateWithNoLabels(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    add_labels = (('key2', 'update2'), ('key4', 'value4'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=(), fingerprint='fingerprint-42')
    updated_instance = self._MakeInstanceProto(instance_ref, labels=add_labels)

    operation_ref = self._GetOperationRef('operation-1', 'atlanta')
    operation = self._MakeOperationMessage(operation_ref, instance_ref)

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref, add_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(instance_ref, updated_instance)

    response = self.Run(
        'compute instances add-labels {} --labels {} '
        .format(
            instance_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, updated_instance)

  def testUpdateWithLabelsAndRemoveLabels(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (('key1', 'value1'), ('key2', 'value2'))
    add_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = ((
        ('key1', 'value1'), ('key2', 'update2'), ('key4', 'value4')
    ))

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
        'compute instances add-labels {} --labels {} '
        .format(
            instance_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, updated_instance)

  def testNoUpdate(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )
    add_labels = (('key1', 'value1'), ('key3', 'value3'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(instance_ref, instance)

    response = self.Run(
        'compute instances add-labels {} --labels {} '
        .format(
            instance_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, instance)

  def testNoLabelsSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --labels: Must be specified.'):
      self.Run('compute instances add-labels instance-1')

  def testInvalidLabel(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance = self._MakeInstanceProto(
        instance_ref, labels={}, fingerprint='fingerprint-42')
    add_labels = (('+notvalid', 'a'),)

    error = http_error.MakeHttpError(
        code=400,
        message='+notvalid',
        reason='Invalid label',
        content={},
        url='')

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref=instance_ref,
        labels=add_labels,
        fingerprint='fingerprint-42',
        exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'Invalid label: +notvalid'):
      self.Run(
          'compute instances add-labels {} --labels {} '
          .format(
              instance_ref.SelfLink(),
              ','.join(['{0}={1}'.format(pair[0], pair[1])
                        for pair in add_labels])
          ))


if __name__ == '__main__':
  test_case.main()
