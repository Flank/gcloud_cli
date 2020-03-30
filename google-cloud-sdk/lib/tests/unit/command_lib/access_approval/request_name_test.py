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
from googlecloudsdk.command_lib.access_approval import request_name
from tests.lib import cli_test_base
from tests.lib.surface.access_approval import base


class RequestNameTest(base.AccessApprovalTestBase):

  def testValidNames(self):
    parser = argparse.ArgumentParser()
    request_name.Args(parser)

    for n in [
        'projects/123/approvalRequests/abc123',
        'projects/my-proj-123/approvalRequests/1',
        'folders/123/approvalRequests/abc123',
        'organizations/9/approvalRequests/a']:
      args = parser.parse_args([n])
      self.assertEqual(request_name.GetName(args), n)

  def testInvalidNames(self):
    parser = argparse.ArgumentParser()
    request_name.Args(parser)

    for n in [
        '',
        'projects//approvalRequests/1',
        'folders/1/approvalRequest/',
        'prefix/organizations/9/approvalRequests/a']:
      args = parser.parse_args([n])
      with self.assertRaises(exceptions.InvalidArgumentException):
        request_name.GetName(args)


if __name__ == '__main__':
  cli_test_base.main()
