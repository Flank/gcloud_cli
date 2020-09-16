# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Unit tests for resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url
from tests.lib import test_case


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ResourceEqualityTest(test_case.TestCase):

  def test_equal_resources(self):
    resource1 = resource_reference.Resource(
        storage_url.CloudUrl('gs', bucket_name='bucket'))

    resource2 = resource_reference.Resource(
        storage_url.CloudUrl('gs', bucket_name='bucket'))

    self.assertEqual(resource1, resource2)

  def test_resources_non_equal_storage_urls(self):
    resource1 = resource_reference.Resource(
        storage_url.CloudUrl('gs', bucket_name='bucket1'))

    resource2 = resource_reference.Resource(
        storage_url.CloudUrl('gs', bucket_name='bucket2'))

    self.assertNotEqual(resource1, resource2)

  def test_resources_non_equal_types(self):
    resource1 = resource_reference.Resource(
        storage_url.CloudUrl('gs', bucket_name='bucket'))

    # Get another class with a storage_url attribute to test that type
    # comparison happens.
    OtherClass = collections.namedtuple('OtherClass', ['storage_url'])
    resource2 = OtherClass(
        storage_url=storage_url.CloudUrl('gs', bucket_name='bucket'))

    self.assertNotEqual(resource1, resource2)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class BucketResourceEqualityTest(test_case.TestCase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('storage', 'v1')

  def test_equal_bucket_resources(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        'bucket', 'e', {})
    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        'bucket', 'e', {})

    self.assertEqual(resource1, resource2)

  def test_bucket_resources_non_equal_storage_urls(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket1'), 'bucket')
    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket2'), 'bucket')

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_names(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket1')
    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket2')

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_etags(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket', 'e1')
    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket', 'e2')

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_metadata(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket',
        metadata={1: 2})
    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket',
        metadata={1: 3})

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_resource_types(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket')
    resource2 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket')

    self.assertNotEqual(resource1, resource2)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ObjectEqualityTest(test_case.TestCase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('storage', 'v1')

  def test_equal_object_resources(self):
    resource1 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data'})

    resource2 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data'})

    self.assertEqual(resource1, resource2)

  def test_object_resources_non_equal_storage_urls(self):
    resource1 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket1'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data'})

    resource2 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket2'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data'})

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_messages(self):
    resource1 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object1'),
        additional_metadata={'meta': 'data'})

    resource2 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object2'),
        additional_metadata={'meta': 'data'})

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_metadata(self):
    resource1 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data1'})

    resource2 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data2'})

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_types(self):
    resource1 = resource_reference.ObjectResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'),
        self.messages.Object(name='object'),
        additional_metadata={'meta': 'data'})

    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl('gs', bucket_name='bucket'), 'bucket',
        metadata=self.messages.Object(name='object'))

    self.assertNotEqual(resource1, resource2)

