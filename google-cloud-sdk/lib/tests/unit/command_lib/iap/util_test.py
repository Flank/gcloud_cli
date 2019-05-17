# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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

"""Tests for command_lib.iap.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iap import util as iap_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exc
from googlecloudsdk.command_lib.iap import util
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope import util as calliope_util


class ParseIapIamResourceTest(cli_test_base.CliTestBase,
                              parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  @parameterized.parameters(
      (['--project=project1'], iap_api.IAPWeb),
      (['--project=project1',
        '--resource-type=' + util.APP_ENGINE_RESOURCE_TYPE],
       iap_api.AppEngineApplication),
      (['--project=project1',
        '--resource-type=' + util.APP_ENGINE_RESOURCE_TYPE,
        '--service=service1'],
       iap_api.AppEngineService),
      (['--project=project1',
        '--resource-type=' + util.APP_ENGINE_RESOURCE_TYPE,
        '--service=service1',
        '--version=version1'],
       iap_api.AppEngineServiceVersion),
      (['--project=project1',
        '--resource-type=' + util.BACKEND_SERVICES_RESOURCE_TYPE],
       iap_api.BackendServices),
      (['--project=project1',
        '--resource-type=' + util.BACKEND_SERVICES_RESOURCE_TYPE,
        '--service=service1'],
       iap_api.BackendService),
  )
  def testParse(self, args, expected_type):
    self.get_client_instance = self.StartObjectPatch(apis, 'GetClientInstance')
    parser = calliope_util.ArgumentParser()
    parser.add_argument('--project', help='The project.')
    util.AddIapIamResourceArgs(parser)
    parsed_args = parser.parse_args(args)
    resource = util.ParseIapIamResource(self.track, parsed_args)
    self.assertEqual(type(resource), expected_type)

  @parameterized.parameters(
      (['--project=project1',
        '--resource-type=invalid-resource'],
       cli_test_base.MockArgumentError),
      (['--project=project1',
        '--resource-type=app-engine',
        '--version=invalid-version'],
       calliope_exc.InvalidArgumentException),
      (['--project=project1',
        '--resource-type=backend-services',
        '--version=invalid-version'],
       calliope_exc.InvalidArgumentException),
      (['--project=project1',
        '--service=invalid-service'],
       calliope_exc.InvalidArgumentException),
      (['--project=project1',
        '--version=invalid-version'],
       calliope_exc.InvalidArgumentException),
  )
  def testParseInvalid(self, args, expected_exception):
    self.get_client_instance = self.StartObjectPatch(apis, 'GetClientInstance')
    parser = calliope_util.ArgumentParser()
    parser.add_argument('--project', help='The project.')
    util.AddIapIamResourceArgs(parser)
    with self.assertRaises(expected_exception):
      parsed_args = parser.parse_args(args)
      util.ParseIapIamResource(self.track, parsed_args)


class ParseIapResourceTest(cli_test_base.CliTestBase,
                           parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  @parameterized.parameters(
      (['--project=project1',
        '--resource-type=' + util.APP_ENGINE_RESOURCE_TYPE],
       iap_api.AppEngineApplication),
      (['--project=project1',
        '--resource-type=' + util.BACKEND_SERVICES_RESOURCE_TYPE,
        '--service=service1'],
       iap_api.BackendService),
  )
  def testParse(self, args, expected_type):
    self.get_client_instance = self.StartObjectPatch(apis, 'GetClientInstance')
    parser = calliope_util.ArgumentParser()
    parser.add_argument('--project', help='The project.')
    util.AddIapIamResourceArgs(parser)
    parsed_args = parser.parse_args(args)
    resource = util.ParseIapResource(self.track, parsed_args)
    self.assertEqual(type(resource), expected_type)

  @parameterized.parameters(
      (['--project=project1',
        '--resource-type=app-engine',
        '--service=invalid-service'],
       calliope_exc.InvalidArgumentException),
      (['--project=project1',
        '--resource-type=backend-services'],
       calliope_exc.RequiredArgumentException),
  )
  def testParseInvalid(self, args, expected_exception):
    self.get_client_instance = self.StartObjectPatch(apis, 'GetClientInstance')
    parser = calliope_util.ArgumentParser()
    parser.add_argument('--project', help='The project.')
    util.AddIapIamResourceArgs(parser)
    with self.assertRaises(expected_exception):
      parsed_args = parser.parse_args(args)
      util.ParseIapResource(self.track, parsed_args)

if __name__ == '__main__':
  test_case.main()
