# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for cloudbuild api_lib util functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class FieldMappingTest(sdk_test_base.WithTempCWD):
  """Test the ability to normalize config field names.
  """

  def testSnakeToCamelString(self):
    cases = [
        ('_', '_'),
        ('__', '__'),
        ('wait_for', 'waitFor'),
        ('foozleBop', 'foozleBop'),
        ('_xyz', '_xyz'),
        ('__xyz', '__xyz'),
        ('a__b', 'aB'),
    ]
    for input_string, expected in cases:
      self.assertEqual(
          cloudbuild_util.SnakeToCamelString(input_string), expected)

  def testSnakeToCamel(self):
    cases = [
        ({'wait_for': ['x', 'y', 'z']},
         {'waitFor': ['x', 'y', 'z']}),
        ({'super_duper': {'wait_for': ['x', 'y', 'z']}},
         {'superDuper': {'waitFor': ['x', 'y', 'z']}}),
        ({'super_list': [{'wait_for': ['x', 'y', 'z']}]},
         {'superList': [{'waitFor': ['x', 'y', 'z']}]}),
        # If the key is 'secret_env' the value is not transformed, while other
        # keys, and the key itself, are transformed.
        ({'camel_me': '', 'secret_env': {'FOO_BAR': 'asdf'}},
         {'camelMe': '', 'secretEnv': {'FOO_BAR': 'asdf'}}),
        # If the key is 'secretEnv' the value is not transformed.
        ({'secretEnv': {'FOO_BAR': 'asdf'}},
         {'secretEnv': {'FOO_BAR': 'asdf'}}),
        # Ensure the skip param works inside lists.
        ([{'secretEnv': {'FOO_BAR': 'asdf'}}],
         [{'secretEnv': {'FOO_BAR': 'asdf'}}]),
        # Ensure the skip param works inside dict values.
        ({'dummy': {'secretEnv': {'FOO_BAR': 'asdf'}}},
         {'dummy': {'secretEnv': {'FOO_BAR': 'asdf'}}}),
    ]
    for input_string, expected in cases:
      self.assertEqual(
          cloudbuild_util.SnakeToCamel(
              input_string, skip=['secretEnv', 'secret_env']), expected)

  def testMessageToFieldPaths_EmptyMessage(self):
    messages = cloudbuild_util.GetMessagesModule()

    self.assertEqual(
        len(cloudbuild_util.MessageToFieldPaths(messages.Build())), 0)

  def testMessageToFieldPaths_Build(self):
    messages = cloudbuild_util.GetMessagesModule()

    b = messages.Build()
    b.projectId = 'projectId'
    b.options = messages.BuildOptions()
    b.options.diskSizeGb = 123

    self.assertEqual(
        set(cloudbuild_util.MessageToFieldPaths(b)),
        set(['project_id', 'options.disk_size_gb']))


class DeriveRegionalEndpointTest(sdk_test_base.WithTempCWD):
  """Test the correctness of the derived regional endpoints."""

  def testProdHttpEndpoint(self):
    global_endpoint = 'http://name.googleapis.com/'
    regional_endpoint = cloudbuild_util.DeriveRegionalEndpoint(
        global_endpoint, 'my-loc1')
    self.assertEqual(regional_endpoint, 'http://my-loc1-name.googleapis.com/')

  def testProdHttpsEndpoint(self):
    global_endpoint = 'https://name.googleapis.com/'
    regional_endpoint = cloudbuild_util.DeriveRegionalEndpoint(
        global_endpoint, 'my-loc1')
    self.assertEqual(regional_endpoint, 'https://my-loc1-name.googleapis.com/')

  def testNonProdHttpEndpoint(self):
    global_endpoint = 'http://name.sandbox.googleapis.com/'
    regional_endpoint = cloudbuild_util.DeriveRegionalEndpoint(
        global_endpoint, 'my-loc1')
    self.assertEqual(regional_endpoint,
                     'http://my-loc1-name.sandbox.googleapis.com/')

  def testNonProdHttpsEndpoint(self):
    global_endpoint = 'https://name.sandbox.googleapis.com/'
    regional_endpoint = cloudbuild_util.DeriveRegionalEndpoint(
        global_endpoint, 'my-loc1')
    self.assertEqual(regional_endpoint,
                     'https://my-loc1-name.sandbox.googleapis.com/')


class OverrideEndpointOnceTest(sdk_test_base.WithTempCWD):
  """Test the ability override endpoints only once."""

  def SetUp(self):
    # There should be no override
    endpoint_property = properties.VALUES.api_endpoint_overrides.cloudbuild
    self.old_endpoint = endpoint_property.Get()
    endpoint_property.Set(None)

  def TearDown(self):
    # Restore the old override, just to be nice
    properties.VALUES.api_endpoint_overrides.cloudbuild.Set(self.old_endpoint)

  def testFirstOverrideWorks(self):
    endpoint_property = properties.VALUES.api_endpoint_overrides.cloudbuild
    self.assertIsNone(endpoint_property.Get())
    with cloudbuild_util.OverrideEndpointOnce('cloudbuild',
                                              'http://first.com/'):
      self.assertEqual(endpoint_property.Get(), 'http://first.com/')
    self.assertIsNone(endpoint_property.Get())

  def testSecondOverrideFails(self):
    endpoint_property = properties.VALUES.api_endpoint_overrides.cloudbuild
    self.assertIsNone(endpoint_property.Get())
    with cloudbuild_util.OverrideEndpointOnce('cloudbuild',
                                              'http://first.com/'):
      self.assertEqual(endpoint_property.Get(), 'http://first.com/')
      with cloudbuild_util.OverrideEndpointOnce('cloudbuild',
                                                'http://second.com/'):
        # Second override should have silently failed
        self.assertEqual(endpoint_property.Get(), 'http://first.com/')
      self.assertEqual(endpoint_property.Get(), 'http://first.com/')
    self.assertIsNone(endpoint_property.Get())


class IsRegionalWorkerPoolTest(sdk_test_base.WithTempCWD):

  def testRegionalWp(self):
    self.assertTrue(
        cloudbuild_util.IsRegionalWorkerPool(
            'projects/abc/locations/def/workerPools/ghi'))

  def testGlobalWp(self):
    self.assertFalse(
        cloudbuild_util.IsRegionalWorkerPool('projects/abc/workerPools/def'))


class GlobalWorkerPoolShortNameTest(sdk_test_base.WithTempCWD):

  def testValid(self):
    self.assertEqual(
        cloudbuild_util.GlobalWorkerPoolShortName(
            'projects/abc/workerPools/def'), 'def')

  def testInvalid(self):
    with self.assertRaisesRegex(ValueError, '.*'):
      cloudbuild_util.GlobalWorkerPoolShortName('badresource')


class RegionalWorkerPoolShortNameTest(sdk_test_base.WithTempCWD):

  def testValid(self):
    self.assertEqual(
        cloudbuild_util.RegionalWorkerPoolShortName(
            'projects/abc/locations/def/workerPools/ghi'), 'ghi')

  def testInvalid(self):
    with self.assertRaisesRegex(ValueError, '.*'):
      cloudbuild_util.RegionalWorkerPoolShortName('badresource')


class RegionalWorkerPoolRegionTest(sdk_test_base.WithTempCWD):

  def testValid(self):
    self.assertEqual(
        cloudbuild_util.RegionalWorkerPoolRegion(
            'projects/abc/locations/def/workerPools/ghi'), 'def')

  def testInvalid(self):
    with self.assertRaisesRegex(ValueError, '.*'):
      cloudbuild_util.RegionalWorkerPoolRegion('badresource')


if __name__ == '__main__':
  test_case.main()
