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
"""Tests for images update."""

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import images_labels_test_base


class UpdateLabelsTestBeta(images_labels_test_base.ImagesLabelsTestBase):

  def testUpdateMissingNameOrLabels(self):
    image_ref = self._GetImageRef('image-1')
    with self.assertRaisesRegex(
        calliope_exceptions.RequiredArgumentException,
        'At least one of --update-labels, '
        '--remove-labels, or --clear-labels must be specified.'):
      self.Run('compute images update {}'.format(image_ref.Name()))

  def testUpdateAndRemoveLabels(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key2', 'update2'), ('key3', 'value3'), ('key4', 'value4'))

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint='fingerprint-42')
    updated_image = self._MakeImageProto(
        image_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, image_ref)

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(image_ref, updated_image)

    response = self.Run(
        'compute images update {} --update-labels {} '
        '--remove-labels key1,key0'
        .format(
            image_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])))
    self.assertEqual(response, updated_image)

  def testUpdateClearLabels(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    edited_labels = ()

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint='fingerprint-42')
    updated_image = self._MakeImageProto(
        image_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, image_ref)

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(image_ref, updated_image)

    response = self.Run(
        'compute images update {} --clear-labels'
        .format(image_ref.SelfLink()))
    self.assertEqual(response, updated_image)

  def testUpdateWithNoLabels(self):
    image_ref = self._GetImageRef('image-1')

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    image = self._MakeImageProto(
        image_ref, labels=(), fingerprint='fingerprint-42')
    updated_image = self._MakeImageProto(image_ref, labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, image_ref)

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref, update_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(image_ref, updated_image)

    response = self.Run(
        'compute images update {} --update-labels {} '
        .format(
            image_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, updated_image)

  def testRemoveWithNoLabelsOnImage(self):
    image_ref = self._GetImageRef('image-1')
    image = self._MakeImageProto(
        image_ref, labels={}, fingerprint='fingerprint-42')

    self._ExpectGetRequest(image_ref, image)

    response = self.Run(
        'compute images update {} --remove-labels DoesNotExist'
        .format(image_ref.SelfLink()))
    self.assertEqual(response, image)

  def testNoNetUpdate(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (
        ('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(image_ref, image)

    response = self.Run(
        'compute images update {} --update-labels {} --remove-labels key4'
        .format(
            image_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, image)


if __name__ == '__main__':
  test_case.main()
