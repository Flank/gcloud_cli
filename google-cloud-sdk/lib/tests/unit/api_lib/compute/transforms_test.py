# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for the transforms module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import transforms
from tests.lib import test_case
import six


class ComputeTransformTest(test_case.Base):

  _RESOURCE = [
      {
          'IPProtocol': 'tcp',
          'name': 'debian-8-jessie-foo-bar',
          'ports':
          [
              '1234-5678',
              '6543-9876',
          ],
          'quota':
          {
              'usage': 1234.5678,
              'limit': 9999.8765,
          },
          'selfLink': 'https://oo/projects/debian-cloud/someone',  # NOTYPO
          'status': 'UNKNOWN',
      },
      {
          'IPProtocol': 'udp',
          'maintenance':
          [
              {
                  'beginTime': '2015-07-17T03:02:01',
                  'endTime': '2015-07-17T04:03:02',
              },
              {
                  'beginTime': '2015-07-16T01:02:03',
                  'endTime': '2015-07-16T02:03:04',
              },
              {
                  'beginTime': '2015-07-04T07:08:09',
                  'endTime': '2015-07-04T12:23:34',
              },
          ],
          'quota':
          {
              'usage': 1234.0,
              'limit': 9999.0,
          },
          'selfLink': 'https://oo/projects/debian-cloud/someone',  # NOTYPO
          'status': 'DONE',
          'deprecated':
          {
              'state': 123,
          },
      },
      {
          'name': 'coreos-stable-test-test-test',
          'ports':
          [
              '1111-2222',
              '8888-9999',
          ],
          'quota':
          {
              'usage': 1234,
              'limit': 9999,
          },
          'selfLink': 'https://oo/projects/coreos-stable/someone',  # NOTYPO
      },
  ]

  _LOCATION_RESOURCE = [
      {
          'name': 'abc',
          'zone': '/my/ZONE',
      },
      {
          'name': 'xyz',
          'region': '/my/REGION',
      },
      {
          'name': 'global',
      },
  ]

  def Run(self, resource, key, transform, args, expected):
    """Applies transform to the value of key in each resource item.

    Args:
      resource: The resource to transform.
      key: Resource key name.
      transform: The transform function to apply to the key value.
      args: The list of arg strings for the transform function.
      expected: The list of expected transformed values, one per resource item.
    """
    self.maxDiff = None
    actual = []
    for item in resource:
      value = item.get(key, None) if key else item
      actual.append(transform(value, *args))
    self.assertEqual(expected, actual)

  def testFirewallRuleTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformFirewallRule, [],
             ['tcp:1234-5678,tcp:6543-9876',
              'udp',
              ''])
    self.Run(self._RESOURCE, 'name', transforms.TransformFirewallRule, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'ports', transforms.TransformFirewallRule, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'quota', transforms.TransformFirewallRule, [],
             ['',
              '',
              ''])

  def testImageAliasTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformImageAlias, [],
             ['debian-8',
              '',
              ''])
    self.Run(self._RESOURCE, 'ports', transforms.TransformImageAlias, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'selfLink', transforms.TransformImageAlias, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'UnKnOwN', transforms.TransformImageAlias, [],
             ['',
              '',
              ''])

  def testLocationTransform(self):
    self.Run(self._LOCATION_RESOURCE, None, transforms.TransformLocation, [],
             ['ZONE',
              'REGION',
              ''])
    self.Run(self._RESOURCE, None, transforms.TransformLocation, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'ports', transforms.TransformLocation, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'selfLink', transforms.TransformLocation, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'UnKnOwN', transforms.TransformLocation, [],
             ['',
              '',
              ''])

  def testLocationScopeTransform(self):
    self.Run(self._LOCATION_RESOURCE, None, transforms.TransformLocationScope,
             [],
             ['zone',
              'region',
              ''])
    self.Run(self._RESOURCE, None, transforms.TransformLocationScope, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'ports', transforms.TransformLocationScope, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'selfLink', transforms.TransformLocationScope, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'UnKnOwN', transforms.TransformLocationScope, [],
             ['',
              '',
              ''])

  def testMachineTypeTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformMachineType, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'ports', transforms.TransformMachineType, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'selfLink', transforms.TransformMachineType, [],
             ['https://oo/projects/debian-cloud/someone',  # NOTYPO
              'https://oo/projects/debian-cloud/someone',  # NOTYPO
              'https://oo/projects/coreos-stable/someone'])  # NOTYPO
    self.Run(self._RESOURCE, 'UnKnOwN', transforms.TransformMachineType, [],
             ['',
              '',
              ''])

  def testNameTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformName, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'ports', transforms.TransformName, [],
             ['',
              '',
              ''])
    self.Run(self._RESOURCE, 'selfLink', transforms.TransformName, [],
             ['someone',
              'someone',
              'someone'])
    self.Run(self._RESOURCE, 'UnKnOwN', transforms.TransformName, [],
             ['',
              '',
              ''])

  def testNextMaintenanceTransform(self):
    self.Run(self._RESOURCE, 'maintenance', transforms.TransformNextMaintenance,
             [],
             ['',
              '2015-07-04T07:08:09--2015-07-04T12:23:34',
              ''])

  def testOperationHttpStatusTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformOperationHttpStatus,
             [],
             ['',
              200,
              ''])

  def testProjectTransform(self):
    self.assertEqual(
        transforms.TransformProject({
            'selfLink': 'https://oo/projects/coreos-stable/someone'  # NOTYPO
        }, 'undefined'), 'coreos-stable')
    self.assertEqual(
        transforms.TransformProject({
            'bad selfLink':
            'https://oo/projects/coreos-stable/someone'  # NOTYPO
        }, 'undefined'), 'undefined')

  def testProjectZone(self):
    self.assertEqual(
        transforms.TransformZone({
            'selfLink': 'https://oo/zones/my-zone/someone'  # NOTYPO
        }, 'undefined'), 'my-zone')
    self.assertEqual(
        transforms.TransformZone({
            'bad selfLink': 'https://oo/zones/my-zone/someone'  # NOTYPO
        }, 'undefined'), 'undefined')

  def testQuotaTransform(self):
    self.Run(self._RESOURCE, 'quota', transforms.TransformQuota,
             [],
             ['1234.57/9999.88',
              '1234/9999',
              '1234/9999'])
    self.Run([{'usage': None, 'limit': None}], None, transforms.TransformQuota,
             [], [''])
    self.Run([{'usage': 'x', 'limit': None}], None, transforms.TransformQuota,
             [], [''])
    self.Run([{'usage': None, 'limit': 'y'}], None, transforms.TransformQuota,
             [], [''])
    self.Run([{'usage': 'x', 'limit': 'y'}], None, transforms.TransformQuota,
             [], [''])
    self.Run([None], None, transforms.TransformQuota, [], [''])

  def testScopedSuffixesTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformScopedSuffixes, [],
             [['IPProtocol', 'name', 'ports', 'quota', 'selfLink', 'status'],
              ['IPProtocol', 'deprecated', 'maintenance', 'quota', 'selfLink',
               'status'],
              ['name', 'ports', 'quota', 'selfLink']])
    self.Run(self._RESOURCE, 'ports', transforms.TransformScopedSuffixes, [],
             [['1234-5678', '6543-9876'],
              '',
              ['1111-2222', '8888-9999']])
    self.Run(self._RESOURCE, 'selfLink', transforms.TransformScopedSuffixes, [],
             [['', '', '', '', '', '-', ':', 'a', 'b', 'c', 'c', 'd', 'd', 'e',
               'e', 'e', 'e', 'h', 'i', 'j', 'l', 'm', 'n', 'n', 'o', 'o', 'o',
               'o', 'o', 'o', 'p', 'p', 'r', 's', 's', 's', 't', 't', 't', 'u'],
              ['', '', '', '', '', '-', ':', 'a', 'b', 'c', 'c', 'd', 'd', 'e',
               'e', 'e', 'e', 'h', 'i', 'j', 'l', 'm', 'n', 'n', 'o', 'o', 'o',
               'o', 'o', 'o', 'p', 'p', 'r', 's', 's', 's', 't', 't', 't', 'u'],
              ['', '', '', '', '', '-', ':', 'a', 'b', 'c', 'c', 'e', 'e', 'e',
               'e', 'e', 'h', 'j', 'l', 'm', 'n', 'o', 'o', 'o', 'o', 'o', 'o',
               'o', 'p', 'p', 'r', 'r', 's', 's', 's', 's', 's', 't', 't', 't',
               't']])
    self.Run(self._RESOURCE, 'UnKnOwN', transforms.TransformScopedSuffixes, [],
             ['',
              '',
              ''])
    self.Run([None], None, transforms.TransformScopedSuffixes, [], [''])
    self.Run([123], None, transforms.TransformScopedSuffixes, [], [''])

  def testStatusTransform(self):
    self.Run(self._RESOURCE, None, transforms.TransformStatus,
             [],
             ['UNKNOWN',
              'DONE (123)',
              ''])

  def testTypeSuffix(self):
    paths = {
        'global':
            'https://www.example.com/projects/my-project/names/my-name',
        'regional': (
            'https://www.example.com/projects/my-project/regions/my-region/'
            'names/my-name'),
        'zonal': (
            'https://www.example.com/projects/my-project/zones/my-zone/names/'
            'my-name'),
    }

    expected_suffix = {
        'global': 'names/my-name',
        'regional': 'names/my-name',
        'zonal': 'names/my-name',
    }

    for object_type, path in six.iteritems(paths):
      suffix = transforms.TransformTypeSuffix(path)
      self.assertEqual(expected_suffix[object_type], suffix)

    self.Run([None], None, transforms.TransformTypeSuffix, [], [''])
    self.Run([123], None, transforms.TransformTypeSuffix, [], [''])

if __name__ == '__main__':
  test_case.main()
