# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Base for Monitoring surface unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class MonitoringTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for Monitoring unit tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.client = mock.Client(client_class=apis.GetClientClass('monitoring',
                                                               'v3'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('monitoring', 'v3')
    self.comparison_enum = (
        self.messages.MetricThreshold.ComparisonValueValuesEnum)
    properties.VALUES.core.user_output_enabled.Set(False)

  def CreateAggregation(self, alignment_period=None, cross_series_reducer=None,
                        group_by_fields=None, per_series_aligner=None):
    csr_value = cross_series_reducer and getattr(
        self.messages.Aggregation.CrossSeriesReducerValueValuesEnum,
        cross_series_reducer)
    psa_value = per_series_aligner and getattr(
        self.messages.Aggregation.PerSeriesAlignerValueValuesEnum,
        per_series_aligner)
    return self.messages.Aggregation(
        alignmentPeriod=alignment_period,
        groupByFields=group_by_fields or [],
        crossSeriesReducer=csr_value,
        perSeriesAligner=psa_value)

  def CreateCondition(self, display_name, condition_filter, duration,
                      trigger_count=None, trigger_percent=None,
                      aggregations=None, comparison=None, threshold_value=None,
                      name=None):
    if trigger_count and trigger_percent:
      raise ValueError('Can only specify one of '
                       '[trigger_count, trigger_percent]')
    if bool(comparison) ^ bool(threshold_value):
      raise ValueError('Must specify both comparison and threshold_value or '
                       'neither.')

    condition = self.messages.Condition(displayName=display_name, name=name)

    trigger = None
    if trigger_count or trigger_percent:
      trigger = self.messages.Trigger(
          count=trigger_count, percent=trigger_percent)
    kwargs = {
        'aggregations': aggregations or [],
        'trigger': trigger,
        'duration': duration,
        'filter': condition_filter,
    }
    if comparison:
      comparison_enum = self.messages.MetricThreshold.ComparisonValueValuesEnum
      condition.conditionThreshold = self.messages.MetricThreshold(
          comparison=getattr(comparison_enum, comparison),
          thresholdValue=threshold_value,
          **kwargs)
    else:
      condition.conditionAbsent = self.messages.MetricAbsence(**kwargs)
    return condition

  def CreatePolicy(self, name=None, display_name=None, conditions=None,
                   enabled=None, documentation_content=None,
                   notification_channels=None, user_labels=None):
    documentation = None
    if documentation_content:
      documentation = self.messages.Documentation(
          content=documentation_content,
          mimeType='text/markdown')

    return self.messages.AlertPolicy(
        name=name,
        displayName=display_name,
        conditions=conditions or [],
        enabled=enabled,
        documentation=documentation,
        notificationChannels=notification_channels or [],
        userLabels=user_labels)

  def CreateChannel(self, name=None, display_name=None, description=None,
                    enabled=None, channel_type=None, user_labels=None,
                    channel_labels=None):
    return self.messages.NotificationChannel(
        name=name,
        displayName=display_name,
        description=description,
        enabled=enabled,
        type=channel_type,
        userLabels=user_labels,
        labels=channel_labels)
