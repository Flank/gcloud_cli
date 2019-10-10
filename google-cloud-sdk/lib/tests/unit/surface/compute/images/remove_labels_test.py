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
"""Tests for the images remove-labels subcommand."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import images_labels_test_base


class RemoveLabelsTest(images_labels_test_base.ImagesLabelsTestBase):
  """Images remove-labels test."""

  def testUpdateWithLabelsAndRemoveLabels(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )
    edited_labels = (('key2', 'value2'), ('key3', 'value3'))

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
        'compute images remove-labels {} --labels key1,key0'
        .format(image_ref.SelfLink()))
    self.assertEqual(response, updated_image)

  def testRemoveAll(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint=b'fingerprint-42')
    updated_image = self._MakeImageProto(image_ref, labels={})
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, image_ref)

    self._ExpectGetRequest(image_ref, image)
    self._ExpectLabelsSetRequest(
        image_ref, {}, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(image_ref, updated_image)

    response = self.Run(
        'compute images remove-labels {} --all'
        .format(image_ref.SelfLink()))
    self.assertEqual(response, updated_image)

  def testRemoveNonExisting(self):
    image_ref = self._GetImageRef('image-1')

    image_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))

    image = self._MakeImageProto(
        image_ref, labels=image_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(image_ref, image)

    response = self.Run(
        'compute images remove-labels {} --labels DoesNotExist'
        .format(image_ref.SelfLink()))
    self.assertEqual(response, image)

  def testRemoveWithNoLabelsOnImage(self):
    image_ref = self._GetImageRef('image-1')
    image = self._MakeImageProto(
        image_ref, labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(image_ref, image)

    response = self.Run(
        'compute images remove-labels {} --labels DoesNotExist'
        .format(image_ref.SelfLink()))
    self.assertEqual(response, image)

  def testNoLabelsOrAllSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--all | --labels) must be specified.'
        ):
      self.Run('compute images remove-labels image-1')

  def testResourceNotFound(self):
    image_ref = self._GetImageRef('some-image')
    error = http_error.MakeHttpError(
        code=404,
        message='some-image was not found',
        reason='NOT FOUND',
        content={},
        url='')

    self._ExpectGetRequest(
        image_ref=image_ref, image=None, exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'NOT FOUND: some-image was not found'):
      self.Run(
          'compute images remove-labels {} --all'
          .format(image_ref.SelfLink()))


if __name__ == '__main__':
  test_case.main()
