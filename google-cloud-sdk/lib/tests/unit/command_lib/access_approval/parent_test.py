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

"""Unit tests for Access Approval parent module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.access_approval import parent
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib.surface.access_approval import base


class ParentTest(base.AccessApprovalTestBase):

  def testOnlyOneParentAllowed(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    # Note: I had trouble getting self.assertRaises to work in this test and
    # gave up. I think it may be because of the test running in both py2 and py3
    # contexts but felt it wasn't worth spending a lot of time on it.
    try:
      parser.parse_args(['--project', '123', '--folder', '456'])
    except:  # pylint: disable=bare-except
      return
    raise AssertionError('parse_args should have raised an exception')

  def testProjectNumber(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--project', '123'])
    self.assertEqual(parent.GetParent(args), 'projects/123')

  def testProject_invalid(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--project', '123AAABBCC'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      parent.GetParent(args)

  def testProjectId(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--project', 'my-project-abc123'])
    self.assertEqual(parent.GetParent(args), 'projects/my-project-abc123')

  def testFolder(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--folder', '123'])
    self.assertEqual(parent.GetParent(args), 'folders/123')

  def testFolder_invalid(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--folder', 'folder123'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      parent.GetParent(args)

  def testOrganization(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--organization', '123'])
    self.assertEqual(parent.GetParent(args), 'organizations/123')

  def testOrganization_invalid(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    args = parser.parse_args(['--organization', 'abc'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      parent.GetParent(args)

  def testDefaultToCoreProject(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    properties.VALUES.core.project.Set('my-project-123')

    args = parser.parse_args([])
    self.assertEqual(parent.GetParent(args), 'projects/my-project-123')

  def testNoCoreProjectSet(self):
    parser = argparse.ArgumentParser()
    parent.Args(parser)

    properties.PersistProperty(properties.VALUES.core.project, None)

    args = parser.parse_args([])
    with self.assertRaises(properties.RequiredPropertyError):
      parent.GetParent(args)


if __name__ == '__main__':
  cli_test_base.main()
