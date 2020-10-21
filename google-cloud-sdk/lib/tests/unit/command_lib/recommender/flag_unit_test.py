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
"""Tests for Recommender API Flags Module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import flag_utils
from googlecloudsdk.api_lib.recommender import service as recommender_service
from googlecloudsdk.command_lib.recommender import flags
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.calliope import util as calliope_util

MESSAGES = recommender_service.RecommenderMessages()
LOCATION = 'my-location'
RECOMMENDER = 'my-recommender'
INSIGHT_TYPE = 'my-insight-type'
RECOMMENDATION = 'my-recommendation'
INSIGHT = 'my-insight'

ORGANIZATION = 'my-organization'
ORGANIZATION_PARENT_RESOURCE = '/organizations/my-organization/locations/my-location/recommenders/my-recommender/recommendations'
ORGANIZATION_LIST_RECOMMENDATION_REQUEST = MESSAGES.RecommenderOrganizationsLocationsRecommendersRecommendationsListRequest(
    parent=ORGANIZATION_PARENT_RESOURCE)
PROJECT = 'my-project'
PROJECT_PARENT_RESOURCE = '/projects/my-project/locations/my-location/recommenders/my-recommender/recommendations'
PROJECT_LIST_RECOMMENDATION_REQUEST = MESSAGES.RecommenderProjectsLocationsRecommendersRecommendationsListRequest(
    parent=PROJECT_PARENT_RESOURCE)
PROJECT_LIST_RECOMMENDATION_PARENT_RESOURCE = 'projects/my-project/locations/my-location/recommenders/my-recommender'
PROJECT_MARK_RECOMMENDATION_PARENT_RESOURCE = PROJECT_LIST_RECOMMENDATION_PARENT_RESOURCE + '/recommendations/my-recommendation'
PROJECT_LIST_INSIGHT_PARENT_RESOURCE = 'projects/my-project/locations/my-location/insightTypes/my-insight-type'
PROJECT_MARK_INSIGHT_PARENT_RESOURCE = PROJECT_LIST_INSIGHT_PARENT_RESOURCE + '/insights/my-insight'

FOLDER = 'my-folder'
FOLDER_PARENT_RESOURCE = '/folders/my-folder/locations/my-location/recommenders/my-recommender/recommendations'
FOLDER_LIST_RECOMMENDATION_REQUEST = MESSAGES.RecommenderFoldersLocationsRecommendersRecommendationsListRequest(
    parent=FOLDER_PARENT_RESOURCE)
BILLING_ACCOUNT = 'my-billing-account'
BILLING_ACCOUNT_PARENT_RESOURCE = '/billingAccounts/my-billing-account/locations/my-location/recommenders/my-recommender/recommendations'
BILLING_ACCOUNT_LIST_RECOMMENDATION_REQUEST = MESSAGES.RecommenderBillingAccountsLocationsRecommendersRecommendationsListRequest(
    parent=BILLING_ACCOUNT_PARENT_RESOURCE)


class ParentFlagsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.parser = calliope_util.ArgumentParser()
    flags.AddParentFlagsToParser(self.parser)
    self.parser.add_argument('--location', metavar='LOCATION', help='Location')
    self.parser.add_argument(
        '--recommender',
        metavar='RECOMMENDER',
        help='Recommender of recommendation')
    self.parser.add_argument(
        '--insight-type',
        metavar='Insight Type',
        help='Insight Type of the insights')

  def testParseOrganization(self):
    args = self.parser.parse_args(['--organization', ORGANIZATION])
    self.assertEqual(args.organization, ORGANIZATION)
    list_request = flag_utils.GetListRequestFromArgs(
        args, ORGANIZATION_PARENT_RESOURCE, is_insight_api=False)
    self.assertEqual(list_request, ORGANIZATION_LIST_RECOMMENDATION_REQUEST)

  def testParseProject(self):
    args = self.parser.parse_args(['--project', PROJECT])
    self.assertEqual(args.project, PROJECT)
    list_request = flag_utils.GetListRequestFromArgs(
        args, PROJECT_PARENT_RESOURCE, is_insight_api=False)
    self.assertEqual(list_request, PROJECT_LIST_RECOMMENDATION_REQUEST)

  def testParseFolder(self):
    args = self.parser.parse_args(['--folder', FOLDER])
    self.assertEqual(args.folder, FOLDER)
    list_request = flag_utils.GetListRequestFromArgs(
        args, FOLDER_PARENT_RESOURCE, is_insight_api=False)
    self.assertEqual(list_request, FOLDER_LIST_RECOMMENDATION_REQUEST)

  def testParseBillingAccount(self):
    args = self.parser.parse_args(['--billing-account', BILLING_ACCOUNT])
    self.assertEqual(args.billing_account, BILLING_ACCOUNT)
    list_request = flag_utils.GetListRequestFromArgs(
        args, BILLING_ACCOUNT_PARENT_RESOURCE, is_insight_api=False)
    self.assertEqual(list_request, BILLING_ACCOUNT_LIST_RECOMMENDATION_REQUEST)

  def testParseTooManyFlags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.parser.parse_args(
          ['--organization', ORGANIZATION, '--folder', FOLDER])

  def testParseNotEnoughFlags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.parser.parse_args([])

  def testGetRecommendationParentFromFlags(self):
    args = self.parser.parse_args([
        '--project', PROJECT, '--location', LOCATION, '--recommender',
        RECOMMENDER
    ])
    self.assertEqual(
        PROJECT_LIST_RECOMMENDATION_PARENT_RESOURCE,
        flags.GetParentFromFlags(args, is_list_api=True, is_insight_api=False))
    self.parser.add_argument(
        'RECOMMENDATION',
        type=str,
        help='Recommendation id used for mark recommendations APIs')
    args = self.parser.parse_args([
        RECOMMENDATION, '--project', PROJECT, '--location', LOCATION,
        '--recommender', RECOMMENDER
    ])
    self.assertEqual(
        PROJECT_MARK_RECOMMENDATION_PARENT_RESOURCE,
        flags.GetParentFromFlags(args, is_list_api=False, is_insight_api=False))

  def testGetInsightParentFromFlags(self):
    args = self.parser.parse_args([
        '--project', PROJECT, '--location', LOCATION, '--insight-type',
        INSIGHT_TYPE
    ])
    self.assertEqual(
        PROJECT_LIST_INSIGHT_PARENT_RESOURCE,
        flags.GetParentFromFlags(args, is_list_api=True, is_insight_api=True))
    self.parser.add_argument(
        'INSIGHT',
        type=str,
        help='Insight id used for insight APIs',
    )
    args = self.parser.parse_args([
        INSIGHT, '--project', PROJECT, '--location', LOCATION, '--insight-type',
        INSIGHT_TYPE
    ])
    self.assertEqual(
        PROJECT_MARK_INSIGHT_PARENT_RESOURCE,
        flags.GetParentFromFlags(args, is_list_api=False, is_insight_api=True))


if __name__ == '__main__':
  test_case.main()
