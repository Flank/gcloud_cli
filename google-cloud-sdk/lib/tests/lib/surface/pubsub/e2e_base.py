# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Base class for all Cloud Pub/Sub tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base


class CloudPubsubTestBase(e2e_base.WithServiceAuth):
  """Base class for Cloud Pub/Sub command e2e tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.retryer = retry.Retryer(max_retrials=4, exponential_sleep_multiplier=2)

  def ClearAndRun(self, command):
    self.ClearOutput()
    self.ClearErr()
    return self.Run('pubsub {0}'.format(command))

  def _CheckListContains(self, list_cmd, resource_name):
    self.ClearAndRun(list_cmd)
    self.AssertOutputContains(resource_name)

  @contextlib.contextmanager
  def _CreateTopic(self, topic_name):
    try:
      self.ClearAndRun(
          'topics list --format value(name) --filter {0}'.format(topic_name))
      self.AssertOutputNotContains(topic_name)

      topic_ref = util.ParseTopic(topic_name, self.Project())
      result = self.ClearAndRun('topics create {0}'.format(topic_name))
      self.AssertErrEquals(
          'Created topic [{0}].\n'.format(topic_ref.RelativeName()))
      yield result

      # There is a delay between creation and the resource appearing in list.
      self.retryer.RetryOnException(self._CheckListContains, [
          'topics list --format value(name) --filter {0}'.format(topic_name),
          topic_name
      ])
    finally:
      self.Run('pubsub topics delete {0}'.format(topic_name))

  @contextlib.contextmanager
  def _CreateSubscription(self, topic_name, subscription_name, ack_deadline=20):
    try:
      self.ClearAndRun('topics list-subscriptions {0}'.format(topic_name))
      self.AssertOutputNotContains(subscription_name)

      result = list(
          self.ClearAndRun('subscriptions create --topic {0} {1}'
                           ' --ack-deadline={2} --format=disable'.format(
                               topic_name, subscription_name, ack_deadline)))
      sub_ref = util.ParseSubscription(subscription_name, self.Project())
      self.AssertErrEquals(
          'Created subscription [{}].\n'.format(sub_ref.RelativeName()))
      yield result[0]

      # There is a delay between creation and the resource appearing in list.
      self.retryer.RetryOnException(self._CheckListContains, [
          'subscriptions list --format value(name) --filter {0}'.format(
              subscription_name), subscription_name
      ])
      self.retryer.RetryOnException(
          self._CheckListContains,
          ['topics list-subscriptions {0}'.format(topic_name),
           subscription_name])
    finally:
      self.Run('pubsub subscriptions delete {0}'.format(subscription_name))

  @contextlib.contextmanager
  def _CreateSnapshot(self, topic_name, subscription_name, snapshot_name):
    try:
      self.ClearAndRun(
          'snapshots list --format value(name) --filter {0}'.format(
              snapshot_name))
      self.AssertOutputNotContains(snapshot_name)

      self.ClearAndRun('topics list-snapshots {}'.format(topic_name))
      self.AssertOutputNotContains(snapshot_name)

      result = self.ClearAndRun(
          'snapshots create {0} --subscription {1}'.format(
              snapshot_name, subscription_name))
      snapshot_ref = util.ParseSnapshot(snapshot_name, self.Project())
      self.AssertErrEquals(
          'Created snapshot [{}].\n'.format(snapshot_ref.RelativeName()))
      yield result

      # There is a delay between creation and the resource appearing in list.
      self.retryer.RetryOnException(self._CheckListContains, [
          'snapshots list --format value(name) --filter {0}'.format(
              snapshot_name), snapshot_name
      ])
      self.retryer.RetryOnException(self._CheckListContains, [
          'topics list-snapshots {}'.format(topic_name), snapshot_name])
    finally:
      self.Run('pubsub snapshots delete {0}'.format(snapshot_name))
