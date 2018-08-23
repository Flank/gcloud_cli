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


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.api_lib.app import service_util
from tests.lib.surface.app import instances_base
from six import moves


class InstancesListTest(instances_base.InstancesTestBase):

  PROJECT = 'fakeproject'

  def _RunTest(self, command, resource_paths):
    actual_instances = set(self.Run(command))
    expected_instances = set(moves.map(
        instances_util.Instance.FromResourcePath, resource_paths))
    self.assertEqual(actual_instances, expected_instances)

  def _RunList(self, command, resource_paths):
    # --format=disable disables output formatting with the side effect that
    # Run() returns the list of filtered resources. This is similar to
    # properties.VALUES.core.user_output_enabled.Set(False) except the latter
    # also disables interactive prompt dialogs, and that wouldn't work here.
    self._RunTest(command + ' --format=disable', resource_paths)

  def testListOutput(self):
    """Test that output in default format is right."""
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3-debug']),
            ('v2', ['i4'])])
    ])
    self.Run('app instances list')
    self.AssertOutputEquals(textwrap.dedent("""\
        SERVICE  VERSION  ID        VM_STATUS  DEBUG_MODE
        default  v1       i1        RUNNING
        default  v1       i2        RUNNING
        foo      v1       i3-debug  RUNNING    YES
        foo      v2       i4        RUNNING
        """))

  def testListAll(self):
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list',
                  ['default/v1/i1', 'default/v1/i2',
                   'foo/v1/i3', 'foo/v2/i4'])

  def testListUriOutput(self):
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])

    self.Run('app instances list --uri')
    self.AssertOutputContains('\n'.join(
        ['https://appengine.googleapis.com/v1/{inst}'.format(inst=instance)
         for instance in [
             'apps/{0}/services/default/versions/v1/instances/i1'.format(
                 self.PROJECT),
             'apps/{0}/services/default/versions/v1/instances/i2'.format(
                 self.PROJECT),
             'apps/{0}/services/foo/versions/v1/instances/i3'.format(
                 self.PROJECT),
             'apps/{0}/services/foo/versions/v2/instances/i4'.format(
                 self.PROJECT)]
        ]), normalize_space=True)

  def testListUriTransformOutput(self):
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])

    self.Run('app instances list --format=value(uri())')
    self.AssertOutputContains('\n'.join(
        ['https://appengine.googleapis.com/v1/{inst}'.format(inst=instance)
         for instance in [
             'apps/{0}/services/default/versions/v1/instances/i1'.format(
                 self.PROJECT),
             'apps/{0}/services/default/versions/v1/instances/i2'.format(
                 self.PROJECT),
             'apps/{0}/services/foo/versions/v1/instances/i3'.format(
                 self.PROJECT),
             'apps/{0}/services/foo/versions/v2/instances/i4'.format(
                 self.PROJECT)]
        ]), normalize_space=True)

  def testListFilterService(self):
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [])
    ])
    self._RunList('app instances list --service default',
                  ['default/v1/i1', 'default/v1/i2'])

    self._ExpectCalls([
        ('default', []),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list --service foo',
                  ['foo/v1/i3', 'foo/v2/i4'])

    self._ExpectCalls([
        ('default', []),
        ('foo', [])
    ])
    with self.assertRaises(service_util.ServicesNotFoundError):
      self.Run('app instances list --service badservice')

  def testListFilterVersion(self):
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', [])])
    ])
    self._RunList('app instances list --version v1',
                  ['default/v1/i1', 'default/v1/i2', 'foo/v1/i3'])

    self._ExpectCalls([
        ('default', [
            ('v1', [])]),
        ('foo', [
            ('v1', []),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list --version v2',
                  ['foo/v2/i4'])

    self._ExpectCalls([
        ('default', [
            ('v1', [])]),
        ('foo', [
            ('v1', []),
            ('v2', [])])
    ])
    self._RunList('app instances list --version badversion',
                  [])

  def testListFilterBoth(self):
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [])
    ])
    self._RunList('app instances list '
                  '--service default --version v1',
                  ['default/v1/i1', 'default/v1/i2'])
    # --filter flag works at list time
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list --verbosity=info '
                  '--filter="service:default version:v1"',
                  ['default/v1/i1', 'default/v1/i2'])

    self._ExpectCalls([
        ('default', [
            ('v1', [])]),
        ('foo', [])
    ])
    self._RunList('app instances list '
                  '--service default --version v2',
                  [])
    # --filter flag works at list time
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list '
                  '--filter="service:default version:v2"',
                  [])

    self._ExpectCalls([
        ('default', []),
        ('foo', [
            ('v1', ['i3']),
            ('v2', [])])
    ])
    self._RunList('app instances list '
                  '--service foo --version v1',
                  ['foo/v1/i3'])
    # --filter flag works at list time
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list '
                  '--filter="service:foo version:v1"',
                  ['foo/v1/i3'])

    # --filter flag works at list time
    self._ExpectCalls([
        ('default', []),
        ('foo', [
            ('v1', []),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list '
                  '--service foo --version v2',
                  ['foo/v2/i4'])
    # --filter flag works at list time
    self._ExpectCalls([
        ('default', [
            ('v1', ['i1', 'i2'])]),
        ('foo', [
            ('v1', ['i3']),
            ('v2', ['i4'])])
    ])
    self._RunList('app instances list '
                  '--filter="service:foo version:v2"',
                  ['foo/v2/i4'])

