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

"""Test resource_managers test lib."""

import re
import unittest

from googlecloudsdk.core import resources
from tests.lib import e2e_resource_managers
from tests.lib import mock_matchers
import mock


class Instance(e2e_resource_managers.CreateDeleteResourceContexManagerBase):

  @property
  def _command_group(self):
    return 'compute instances'


class TestResourceParameters(unittest.TestCase):

  def assertAcuallyMatchesRegex(self, regex, string):
    self.assertTrue(
        re.match(regex, string),
        string + ' does not match ' + regex)

  def GetIntanceUrlRegex(self, name):
    return r'{}/projects/{}/zones/{}/instances/{}[\w-]+'.format(
        self.compute_uri, self.project, self.zone, name)

  def setUp(self):
    self.registry = resources.Registry()
    self.compute_uri = 'https://www.googleapis.com/compute/v1'
    self.project = 'long-island'
    self.zone = 'local-group'

  def testCreateDeleteInstance(self):
    runner = mock.MagicMock()
    instance_ref = self.registry.Parse(
        'bob', collection='compute.instances',
        params={'zone': self.zone, 'project': self.project})
    resource_parameters = e2e_resource_managers.ResourceParameters(instance_ref)

    with Instance(runner, resource_parameters):
      pass

    expected_create = (
        r'^compute instances create ' + self.GetIntanceUrlRegex('bob'))
    expected_delete = (
        r'^compute instances delete ' + self.GetIntanceUrlRegex('bob'))
    runner.assert_has_calls([
        mock.call(mock_matchers.RegexMatcher(expected_create)),
        mock.call(mock_matchers.RegexMatcher(expected_delete))])

  def testCreateDeleteInstanceReuseParams(self):
    runner = mock.MagicMock()
    instance_ref = self.registry.Parse(
        'bob', collection='compute.instances',
        params={'zone': self.zone, 'project': self.project})
    resource_parameters = e2e_resource_managers.ResourceParameters(instance_ref)

    with Instance(runner, resource_parameters):
      with Instance(runner, resource_parameters):
        pass

    expected_create = (
        r'^compute instances create ' + self.GetIntanceUrlRegex('bob'))
    expected_delete = (
        r'^compute instances delete ' + self.GetIntanceUrlRegex('bob'))
    runner.assert_has_calls([
        mock.call(mock_matchers.RegexMatcher(expected_create)),
        mock.call(mock_matchers.RegexMatcher(expected_create)),
        mock.call(mock_matchers.RegexMatcher(expected_delete)),
        mock.call(mock_matchers.RegexMatcher(expected_delete)),
    ])

  def testCreateDeleteInstanceParametrized(self):
    runner = mock.MagicMock()
    instance_ref = self.registry.Parse(
        'bob', collection='compute.instances',
        params={'zone': self.zone, 'project': self.project})
    resource_parameters = e2e_resource_managers.ResourceParameters(
        instance_ref, extra_creation_flags=[('--can-ip-forward', '')])

    with Instance(runner, resource_parameters):
      pass

    expected_create = (
        r'^compute instances create {} --can-ip-forward *$'.format(
            self.GetIntanceUrlRegex('bob')))
    expected_delete = (
        r'^compute instances delete '  + self.GetIntanceUrlRegex('bob'))
    runner.assert_has_calls([
        mock.call(mock_matchers.RegexMatcher(expected_create)),
        mock.call(mock_matchers.RegexMatcher(expected_delete))])

  def testAccessObjectsProperties(self):
    runner = mock.MagicMock()
    instance_ref = self.registry.Parse(
        'bob', collection='compute.instances',
        params={'zone': self.zone, 'project': self.project})
    resource_parameters = e2e_resource_managers.ResourceParameters(
        instance_ref, extra_creation_flags=[
            ('FROSTING', 'NO'),
            ('--decoration', 'NOPE'),
            ('FROSTING', 'MAYBE')])

    with Instance(runner, resource_parameters) as the_cake:
      self.assertAcuallyMatchesRegex(
          self.GetIntanceUrlRegex('bob'), the_cake.ref.SelfLink())
      self.assertAcuallyMatchesRegex(r'bob[\w-]+', the_cake.ref.Name())
      self.assertEqual(
          ['NO', 'MAYBE'], the_cake.GetExtraCreationFlag('FROSTING'))
      self.assertEqual(
          ['NOPE'], the_cake.GetExtraCreationFlag('--decoration'))

if __name__ == '__main__':
  unittest.main()
