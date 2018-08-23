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
"""Tests for images add-labels subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import images_labels_test_base


class AddLabelsTest(images_labels_test_base.ImagesLabelsTestBase):
  """Images add-labels test."""

  def testAddWithNoLabels(self):
    image_ref = self._GetImageRef('image-1')

    add_labels = (('key2', 'update2'), ('key4', 'value4'))

    image = self._MakeImageProto(
        image_ref, labels=(), fingerprint=b'fingerprint-42')
    updated_image = self._MakeImageProto(image_ref, labels=add_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, image_ref)

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref, add_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(image_ref, updated_image)

    response = self.Run(
        'compute images add-labels {} --labels {} '
        .format(
            image_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, updated_image)

  def testAddWithLabelsAndUpdateLabels(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (('key1', 'value1'), ('key2', 'value2'))
    add_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = ((
        ('key1', 'value1'), ('key2', 'update2'), ('key4', 'value4')
    ))

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint=b'fingerprint-42')
    updated_image = self._MakeImageProto(
        image_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, image_ref)

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(image_ref, updated_image)

    response = self.Run(
        'compute images add-labels {} --labels {} '
        .format(
            image_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, updated_image)

  def testNoUpdate(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )
    add_labels = (('key1', 'value1'), ('key3', 'value3'))

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(image_ref, image)

    response = self.Run(
        'compute images add-labels {} --labels {} '
        .format(
            image_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, image)

  def testNoLabelsSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --labels: Must be specified.'
        ):
      self.Run('compute images add-labels image-1')

  def testInvalidLabel(self):
    image_ref = self._GetImageRef('image-1')

    image = self._MakeImageProto(
        image_ref, labels={}, fingerprint=b'fingerprint-42')
    add_labels = (('+notvalid', 'a'),)

    error = http_error.MakeHttpError(
        code=400,
        message='+notvalid',
        reason='Invalid label',
        content={},
        url='')

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref=image_ref,
        labels=add_labels,
        fingerprint=b'fingerprint-42',
        exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'Invalid label: +notvalid'):
      self.Run(
          'compute images add-labels {} --labels {} '
          .format(
              image_ref.SelfLink(),
              ','.join(['{0}={1}'.format(pair[0], pair[1])
                        for pair in add_labels])
          ))


if __name__ == '__main__':
  test_case.main()
