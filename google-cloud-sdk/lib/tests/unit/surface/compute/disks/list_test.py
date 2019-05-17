# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the disks list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class DisksListCompleterTestGA(
    test_base.BaseTest, completer_test_base.CompleterBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.MultiScopeLister',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_multi_scope_lister = lister_patcher.start()
    self.mock_multi_scope_lister.return_value.return_value = (
        resource_projector.MakeSerializable(test_resources.DISKS))

  def testDisksCompleter(self):
    self.RunCompleter(
        completers.DisksCompleter,
        expected_command=[
            'compute',
            'disks',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['disk-1', 'disk-2', 'disk-3'],
        cli=self.cli,
    )


class DisksListCompleterTestBeta(DisksListCompleterTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DisksListCompleterTestAlpha(DisksListCompleterTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class RegionalDisksListTestGA(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SelectApi(self.api_version)

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testOutputFormat(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.DISKS + [
            self.messages.Disk(
                name='disk-3',
                selfLink=('https://www.googleapis.com/compute/v1/projects/'
                          'my-project/regions/region-1/disks/disk-3'),
                sizeGb=10,
                status=self.messages.Disk.StatusValueValuesEnum.READY,
                type=(
                    'https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/region-1/diskTypes/pd-standard'),
                region=(
                    'https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/region-1'))
        ])
    ]

    self.Run('compute disks list')

    self.list_json.assert_called_once_with(
        requests=[(self.compute.disks, 'AggregatedList',
                   self.messages.ComputeDisksAggregatedListRequest(
                       project='my-project',))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
              NAME LOCATION LOCATION_SCOPE SIZE_GB TYPE STATUS
              disk-1 zone-1 zone 10 pd-ssd READY
              disk-2 zone-1 zone 10 pd-ssd READY
              disk-3 zone-1 zone 10 pd-standard READY
              disk-3 region-1 region 10 pd-standard READY
              """), normalize_space=True)

  def testOnlyRegional(self):
    self.list_json.side_effect = [
        [encoding.MessageToDict(self.messages.Disk(
            name='disk-3',
            selfLink=('https://www.googleapis.com/compute/v1/projects/'
                      'my-project/regions/region-1/disks/disk-3'),
            sizeGb=10,
            status=self.messages.Disk.StatusValueValuesEnum.READY,
            type=(
                'https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1/diskTypes/pd-standard'),
            region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/region-1')))]]

    self.Run('compute disks list --regions region-1')

    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionDisks, 'List',
                   self.messages.ComputeRegionDisksListRequest(
                       project='my-project',
                       region='region-1',))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
              NAME LOCATION LOCATION_SCOPE SIZE_GB TYPE STATUS
              disk-3 region-1 region 10 pd-standard READY
              """), normalize_space=True)


class RegionalDisksListTestBeta(RegionalDisksListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class RegionalDisksListTestAlpha(RegionalDisksListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
