# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Unit tests for the Run flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.api_lib.run import traffic_pair
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import parameterized
from tests.lib import test_case


MESSAGES = core_apis.GetMessagesModule('run', 'v1')
URL_FORMAT = 'https://{}---service.uc.a.run.app/'


def NewTrafficTargets(percentages):
  targets = [
      TrafficTarget(name, percentage)
      for name, percentage in percentages.items()
  ]
  return TrafficTargets(targets)


def TrafficTarget(key, percent=None, tag=None, populate_url=False):
  target = traffic.NewTrafficTarget(MESSAGES, key, percent, tag)
  if tag and populate_url:
    target.url = URL_FORMAT.format(tag)
  return target


def TrafficTargets(targets_to_wrap):
  return traffic.TrafficTargets(MESSAGES, targets_to_wrap)


def NewTrafficTargetPair(latest_revision_name,
                         spec_percent=None,
                         spec_latest=None,
                         spec_revision_name=None,
                         status_percent=None,
                         status_latest=None,
                         status_revision_name=None,
                         status_percent_override=None,
                         service_url=''):

  if (spec_percent is not None
      or spec_latest is not None
      or spec_revision_name is not None):
    spec_traffic = [
        MESSAGES.TrafficTarget(
            latestRevision=spec_latest,
            revisionName=spec_revision_name,
            percent=spec_percent)
    ]
  else:
    spec_traffic = []

  if (status_percent is not None
      and (status_latest is not None
           or status_revision_name is not None)):
    status_traffic = [
        MESSAGES.TrafficTarget(
            latestRevision=status_latest,
            revisionName=status_revision_name,
            percent=status_percent)
    ]
  else:
    status_traffic = []

  revision_name = (
      spec_revision_name or status_revision_name or latest_revision_name)
  is_latest = spec_latest or status_latest
  return traffic_pair.TrafficTargetPair(spec_traffic, status_traffic,
                                        revision_name, is_latest,
                                        status_percent_override, service_url)


class TrafficTargetPairTest(test_case.TestCase):

  def testSpecOnlyLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_latest=True)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '100% (currently -)')

  def testSpecOnlyRevisionName(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_revision_name='s1-r2')
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '100% (currently -)')

  def testStatusOnlyLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', status_percent=100, status_latest=True)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '-    (currently 100%)')

  def testStatusOnlyRevisionName(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', status_percent=100, status_revision_name='s1-r2')
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '-    (currently 100%)')

  def testBothLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_latest=True,
        status_percent=100, status_revision_name='s1-r1', status_latest=True)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '100%')

  def testBothRevisionName(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_revision_name='s1-r2',
        status_percent=100, status_revision_name='s1-r2')
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '100%')

  def testBothStatusLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=40, spec_latest=True,
        status_percent=60, status_revision_name='s1-r1')
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '40')
    self.assertEqual(target_pair.statusPercent, '60')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '40%  (currently 60%)')

  def testBothStatusLatestWithStatusPercentOverride(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=40, spec_latest=True,
        status_percent=60, status_revision_name='s1-r1',
        status_percent_override=40)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '40')
    self.assertEqual(target_pair.statusPercent, '40')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '40%')

  def testMultipleSpecTargetsWithPercentRevisionName(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget('s1-r2', 40),
        TrafficTarget('s1-r2', None),
        TrafficTarget('s1-r2', 60)
    ], [], 's1-r2', False, None)
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '100% (currently -)')

  def testMultipleStatusTargetsWithPercentRevisionName(self):
    target_pair = traffic_pair.TrafficTargetPair([], [
        TrafficTarget('s1-r2', 40),
        TrafficTarget('s1-r2', None),
        TrafficTarget('s1-r2', 60)
    ], 's1-r2', False, None)
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '-    (currently 100%)')

  def testMultipleSpecTargetsWithPercentLatest(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget(traffic.LATEST_REVISION_KEY, 40),
        TrafficTarget(traffic.LATEST_REVISION_KEY, None),
        TrafficTarget(traffic.LATEST_REVISION_KEY, 60)
    ], [], 's1-r2', True, None)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 'LATEST (currently s1-r2)')
    self.assertEqual(target_pair.displayPercent, '100% (currently -)')

  def testMultipleStatusTargetsWithPercentLatest(self):
    target_pair = traffic_pair.TrafficTargetPair([], [
        TrafficTarget(traffic.LATEST_REVISION_KEY, 40),
        TrafficTarget(traffic.LATEST_REVISION_KEY, None),
        TrafficTarget(traffic.LATEST_REVISION_KEY, 60)
    ], 's1-r2', True, None)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 'LATEST (currently s1-r2)')
    self.assertEqual(target_pair.displayPercent, '-    (currently 100%)')

  def testMultipleStatusTargetsWithOverrideLatest(self):
    target_pair = traffic_pair.TrafficTargetPair([], [
        TrafficTarget(traffic.LATEST_REVISION_KEY, 40),
        TrafficTarget(traffic.LATEST_REVISION_KEY, None),
        TrafficTarget(traffic.LATEST_REVISION_KEY, 60)
    ], 's1-r2', True, 80)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '80')
    self.assertEqual(target_pair.displayRevisionId, 'LATEST (currently s1-r2)')
    self.assertEqual(target_pair.displayPercent, '-    (currently 80%)')

  def testSpecOneTag(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate')
    ], [], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, 'candidate')
    self.assertEqual(target_pair.statusTags, '-')
    self.assertEqual(target_pair.urls, [])
    self.assertEqual(target_pair.displayTags, 'candidate (currently -)')

  def testSpecMultipleTags(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate'),
        TrafficTarget('s1-r1', None, tag='head')
    ], [], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, 'candidate, head')
    self.assertEqual(target_pair.statusTags, '-')
    self.assertEqual(target_pair.urls, [])
    self.assertEqual(target_pair.displayTags, 'candidate, head (currently -)')

  def testStatusOneTag(self):
    target_pair = traffic_pair.TrafficTargetPair([], [
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate', populate_url=True)
    ], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, '-')
    self.assertEqual(target_pair.statusTags, 'candidate')
    self.assertEqual(target_pair.urls,
                     ['https://candidate---service.uc.a.run.app/'])
    self.assertEqual(target_pair.displayTags, '- (currently candidate)')

  def testStatusMultipleTags(self):
    target_pair = traffic_pair.TrafficTargetPair([], [
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate', populate_url=True),
        TrafficTarget('s1-r1', None, tag='head', populate_url=True)
    ], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, '-')
    self.assertEqual(target_pair.statusTags, 'candidate, head')
    self.assertEqual(target_pair.urls, [
        'https://candidate---service.uc.a.run.app/',
        'https://head---service.uc.a.run.app/'
    ])
    self.assertEqual(target_pair.displayTags, '- (currently candidate, head)')

  def testBothOneTag(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate')
    ], [
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate', populate_url=True)
    ], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, 'candidate')
    self.assertEqual(target_pair.statusTags, 'candidate')
    self.assertEqual(target_pair.urls,
                     ['https://candidate---service.uc.a.run.app/'])
    self.assertEqual(target_pair.displayTags, 'candidate')

  def testBothMultipleTags(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate'),
        TrafficTarget('s1-r1', None, tag='head')
    ], [
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', None, tag='candidate', populate_url=True),
        TrafficTarget('s1-r1', None, tag='head', populate_url=True)
    ], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, 'candidate, head')
    self.assertEqual(target_pair.statusTags, 'candidate, head')
    self.assertEqual(target_pair.urls, [
        'https://candidate---service.uc.a.run.app/',
        'https://head---service.uc.a.run.app/'
    ])
    self.assertEqual(target_pair.displayTags, 'candidate, head')

  def testBothNoTags(self):
    target_pair = traffic_pair.TrafficTargetPair(
        [TrafficTarget('s1-r1', 100)], [
            TrafficTarget('s1-r1', 100),
        ], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, '-')
    self.assertEqual(target_pair.statusTags, '-')
    self.assertEqual(target_pair.urls, [])
    self.assertEqual(target_pair.displayTags, '')

  def testSortsTagsAndUrls(self):
    target_pair = traffic_pair.TrafficTargetPair([
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', tag='c'),
        TrafficTarget('s1-r1', tag='b'),
        TrafficTarget('s1-r1', tag='a'),
        TrafficTarget('s1-r1', tag='d')
    ], [
        TrafficTarget('s1-r1', 100),
        TrafficTarget('s1-r1', tag='d', populate_url=True),
        TrafficTarget('s1-r1', tag='c', populate_url=True),
        TrafficTarget('s1-r1', tag='a', populate_url=True),
        TrafficTarget('s1-r1', tag='b', populate_url=True),
    ], 's1-r1', False, None)
    self.assertEqual(target_pair.specTags, 'a, b, c, d')
    self.assertEqual(target_pair.statusTags, 'a, b, c, d')
    self.assertEqual(target_pair.urls, [
        'https://a---service.uc.a.run.app/',
        'https://b---service.uc.a.run.app/',
        'https://c---service.uc.a.run.app/',
        'https://d---service.uc.a.run.app/',
    ])
    self.assertEqual(target_pair.displayTags, 'a, b, c, d')

  def testSetsServiceUrl(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_latest=True, service_url='<url>')
    self.assertEqual(target_pair.serviceUrl, '<url>')


class GetTrafficPairsTest(test_case.TestCase, parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name':
              'single_target',
          'spec_targets':
              [TrafficTarget('s1-r1', 10),
               TrafficTarget('s1-r2', 90)],
      }, {
          'testcase_name':
              'multiple_targets',
          'spec_targets': [
              TrafficTarget('s1-r1', 8),
              TrafficTarget('s1-r1', 2),
              TrafficTarget('s1-r2', 40),
              TrafficTarget('s1-r2', 50)
          ],
      })
  def testSpecOnlyNoLatest(self, spec_targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(spec_targets),
        status_traffic=TrafficTargets([]),
        is_platform_managed=False,
        latest_ready_revision_name=None)
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'targets': [TrafficTarget('s1-r1', 10),
                      TrafficTarget('s1-r2', 90)],
      }, {
          'testcase_name':
              'multiple_targets',
          'targets': [
              TrafficTarget('s1-r1', 8),
              TrafficTarget('s1-r1', 2),
              TrafficTarget('s1-r2', 40),
              TrafficTarget('s1-r2', 50)
          ]
      })
  def testBothNoLatestMatch(self, targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(targets),
        status_traffic=TrafficTargets(targets),
        is_platform_managed=False,
        latest_ready_revision_name=None)
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '10')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '90')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'spec_targets': [TrafficTarget('s1-r1', 100)],
          'status_targets': [TrafficTarget('s1-r2', 100)]
      }, {
          'testcase_name':
              'multiple_targets',
          'spec_targets':
              [TrafficTarget('s1-r1', 60),
               TrafficTarget('s1-r1', 40)],
          'status_targets':
              [TrafficTarget('s1-r2', 30),
               TrafficTarget('s1-r2', 70)]
      })
  def testBothNoLatestNoMatch(self, spec_targets, status_targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(spec_targets),
        status_traffic=TrafficTargets(status_targets),
        is_platform_managed=False,
        latest_ready_revision_name=None)
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')

  @parameterized.named_parameters(
      {
          'testcase_name':
              'single_target',
          'spec_targets':
              [TrafficTarget('s1-r1', 90),
               TrafficTarget('LATEST', 10)],
      }, {
          'testcase_name':
              'multiple_targets',
          'spec_targets': [
              TrafficTarget('s1-r1', 40),
              TrafficTarget('s1-r1', 50),
              TrafficTarget('LATEST', 6),
              TrafficTarget('LATEST', 4)
          ],
      })
  def testSpecOnlyExplicitLatest(self, spec_targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(spec_targets),
        status_traffic=TrafficTargets([]),
        is_platform_managed=False,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'targets': [TrafficTarget('s1-r1', 90),
                      TrafficTarget('LATEST', 10)],
      }, {
          'testcase_name':
              'multiple_targets',
          'targets': [
              TrafficTarget('s1-r1', 40),
              TrafficTarget('s1-r1', 50),
              TrafficTarget('LATEST', 6),
              TrafficTarget('LATEST', 4)
          ],
      })
  def testBothExplicitLatest(self, targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(targets),
        status_traffic=TrafficTargets(targets),
        is_platform_managed=False,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '90')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '10')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'spec_targets':
              [TrafficTarget('s1-r1', 90),
               TrafficTarget('LATEST', 10)],
          'status_targets': [TrafficTarget('s1-r1', 100)]
      }, {
          'testcase_name':
              'multiple_targets',
          'spec_targets': [
              TrafficTarget('s1-r1', 30),
              TrafficTarget('s1-r1', 60),
              TrafficTarget('LATEST', 2),
              TrafficTarget('LATEST', 8),
          ],
          'status_targets':
              [TrafficTarget('s1-r1', 30),
               TrafficTarget('s1-r1', 70)]
      })
  def testBothImplicitLatestMissingStatusGke(self, spec_targets,
                                             status_targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(spec_targets),
        status_traffic=TrafficTargets(status_targets),
        is_platform_managed=False,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'spec_targets':
              [TrafficTarget('s1-r1', 90),
               TrafficTarget('LATEST', 10)],
          'status_targets': [TrafficTarget('s1-r1', 100)]
      }, {
          'testcase_name':
              'multiple_targets',
          'spec_targets': [
              TrafficTarget('s1-r1', 30),
              TrafficTarget('s1-r1', 60),
              TrafficTarget('LATEST', 2),
              TrafficTarget('LATEST', 8),
          ],
          'status_targets':
              [TrafficTarget('s1-r1', 30),
               TrafficTarget('s1-r1', 70)]
      }, {
          'testcase_name':
              'multiple_targets_with_none_percent',
          'spec_targets': [
              TrafficTarget('s1-r1', 30),
              TrafficTarget('s1-r1', 60),
              TrafficTarget('s1-r1', None),
              TrafficTarget('LATEST', 2),
              TrafficTarget('LATEST', 8),
              TrafficTarget('LATEST', None),
          ],
          'status_targets':
              [TrafficTarget('s1-r1', 30),
               TrafficTarget('s1-r1', 70),
               TrafficTarget('s1-r1', None)]
      })
  def testBothImplicitManaged(self, spec_targets, status_targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(spec_targets),
        status_traffic=TrafficTargets(status_targets),
        is_platform_managed=True,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '90')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '10')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'spec_targets':
              [TrafficTarget('LATEST', 100)],
          'status_targets': [TrafficTarget('s1-r1', 100)]
      }, {
          'testcase_name':
              'multiple_targets',
          'spec_targets': [
              TrafficTarget('LATEST', 20),
              TrafficTarget('LATEST', 80),
          ],
          'status_targets':
              [TrafficTarget('s1-r1', 30),
               TrafficTarget('s1-r1', 70)]
      }, {
          'testcase_name':
              'multiple_targets_with_none_percent',
          'spec_targets': [
              TrafficTarget('LATEST', 20),
              TrafficTarget('LATEST', 80),
              TrafficTarget('LATEST', None),
          ],
          'status_targets':
              [TrafficTarget('s1-r1', 30),
               TrafficTarget('s1-r1', 70),
               TrafficTarget('s1-r1', None)]
      })
  def testLatestImplicitManaged(self, spec_targets, status_targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(spec_targets),
        status_traffic=TrafficTargets(status_targets),
        is_platform_managed=True,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 1)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  @parameterized.named_parameters(
      {
          'testcase_name': 'single_target',
          'targets':
              [TrafficTarget('s1-r1', 100)],
      }, {
          'testcase_name':
              'multiple_targets',
          'targets': [
              TrafficTarget('s1-r1', 20),
              TrafficTarget('s1-r1', 80),
          ],
      }, {
          'testcase_name':
              'multiple_targets_with_none_percent',
          'targets': [
              TrafficTarget('s1-r1', 20),
              TrafficTarget('s1-r1', 80),
              TrafficTarget('s1-r1', None),
          ],
      })
  def testLatestByNameOnlyManaged(self, targets):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(targets),
        status_traffic=TrafficTargets(targets),
        is_platform_managed=True,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 1)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')

  def testSetsServiceUrl(self):
    traffic_pairs = traffic_pair.GetTrafficTargetPairs(
        spec_traffic=TrafficTargets(
            [TrafficTarget('s1-r1', 10),
             TrafficTarget('s1-r2', 90)]),
        status_traffic=TrafficTargets([]),
        is_platform_managed=False,
        latest_ready_revision_name=None,
        service_url='<url>')
    self.assertEqual(traffic_pairs[0].serviceUrl, '<url>')
    self.assertEqual(traffic_pairs[1].serviceUrl, '<url>')


if __name__ == '__main__':
  test_case.main()
