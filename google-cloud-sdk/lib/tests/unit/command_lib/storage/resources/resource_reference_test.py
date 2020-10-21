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

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from tests.lib import test_case


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ResourceEqualityTest(test_case.TestCase):

  def test_equal_resources(self):
    resource1 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    resource2 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    self.assertEqual(resource1, resource2)

  def test_resources_non_equal_storage_urls(self):
    resource1 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket1'))

    resource2 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket2'))

    self.assertNotEqual(resource1, resource2)

  def test_resources_non_equal_types(self):
    resource1 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    # Get another class with a storage_url attribute to test that type
    # comparison happens.
    OtherClass = collections.namedtuple('OtherClass', ['storage_url'])
    resource2 = OtherClass(storage_url=storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    self.assertNotEqual(resource1, resource2)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CloudResourceEqualityTest(test_case.TestCase):

  def test_equal_resources(self):
    resource1 = resource_reference.CloudResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    resource2 = resource_reference.CloudResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    self.assertEqual(resource1, resource2)

  def test_resources_non_equal_schemes(self):
    resource1 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    resource2 = resource_reference.Resource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.S3, bucket_name='bucket'))

    self.assertNotEqual(resource1, resource2)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class BucketResourceEqualityTest(test_case.TestCase):

  def test_equal_bucket_resources(self):
    resource1 = resource_reference.BucketResource(
        storage_url.CloudUrl(
            storage_url.ProviderPrefix.GCS, bucket_name='bucket'),
        etag='e', metadata={})
    resource2 = resource_reference.BucketResource(
        storage_url.CloudUrl(
            storage_url.ProviderPrefix.GCS, bucket_name='bucket'),
        etag='e', metadata={})

    self.assertEqual(resource1, resource2)

  def test_bucket_resources_non_equal_storage_urls(self):
    resource1 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket1'))
    resource2 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket2'))

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_names(self):
    resource1 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket1'))
    resource2 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket2'))

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_etags(self):
    resource1 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), etag='e1')
    resource2 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), etag='e2')

    self.assertNotEqual(resource1, resource2)

  def test_bucket_resources_non_equal_metadata(self):
    resource1 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), metadata={1: 2})
    resource2 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), metadata={1: 3})

    self.assertNotEqual(resource1, resource2)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ObjectEqualityTest(test_case.TestCase):

  def test_equal_object_resources(self):
    resource1 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), 'e', metadata={})
    resource2 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), 'e', metadata={})

    self.assertEqual(resource1, resource2)

  def test_object_resources_non_equal_storage_urls(self):
    resource1 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket1'))
    resource2 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket2'))

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_etags(self):
    resource1 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), etag='e1')
    resource2 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), etag='e2')

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_generations(self):
    resource1 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='b', object_name='o',
        generation='g'))
    resource2 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='b', object_name='o',
        generation='g2'))

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_metadata(self):
    resource1 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), metadata={1: 2})
    resource2 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'), metadata={1: 3})

    self.assertNotEqual(resource1, resource2)

  def test_object_resources_non_equal_types(self):
    resource1 = resource_reference.ObjectResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))
    resource2 = resource_reference.BucketResource(storage_url.CloudUrl(
        storage_url.ProviderPrefix.GCS, bucket_name='bucket'))

    self.assertNotEqual(resource1, resource2)
