# Lint as: python3
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
"""Tests for google3.third_party.py.tests.unit.command_lib.privateca.resource_args."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.calliope import util

import mock


class ResourceArgsTest(cli_test_base.CliTestBase, test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()

  def CreateReusableConfigResourceSpecUsesDefaultLocationAndProject(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    args = self.parser.parse_args(['--reusable-config', 'foobar'])
    reusable_config = args.CONCEPTS.reusable_config.Parse()
    self.assertEqual(
        reusable_config.RelativeName(),
        'projects/privateca-data/locations/us-west1/reusableConfigs/foobar')

  def CreateReusableConfigResourceSpecTakesFullResourceId(self):
    resource_id = 'projects/foo/locations/us-west1/reusableConfigs/bar'
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    args = self.parser.parse_args(['--reusable-config', resource_id])
    reusable_config = args.CONCEPTS.reusable_config.Parse()
    self.assertEqual(reusable_config.RelativeName(), resource_id)


def GetSampleCertificateAuthority(location):
  return resources.REGISTRY.ParseRelativeName(
      relative_name='projects/p1/locations/{}/certificateAuthorities/ca'
      .format(location),
      collection='privateca.projects.locations.certificateAuthorities')


class LocationValidationTest(cli_test_base.CliTestBase):

  @mock.patch.object(locations, 'GetSupportedLocations', autospec=True)
  def testValidationPassesForKmsKeyVersionInSupportedLocations(self, mock_fn):
    mock_fn.return_value = ['us-west1', 'europe-west1']
    for location in ['us-west1', 'europe-west1']:
      resource_ref = GetSampleCertificateAuthority(location)
      resource_args.ValidateResourceLocation(resource_ref,
                                             'CERTIFICATE_AUTHORITY')

  @mock.patch.object(locations, 'GetSupportedLocations', autospec=True)
  def testValidationFailsForKmsKeyVersionInUnsupportedLocation(self, mock_fn):
    mock_fn.return_value = ['us-west1', 'europe-west1']
    resource_ref = GetSampleCertificateAuthority('us')
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'CERTIFICATE_AUTHORITY'):
      resource_args.ValidateResourceLocation(resource_ref,
                                             'CERTIFICATE_AUTHORITY')


if __name__ == '__main__':
  test_case.main()
