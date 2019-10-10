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
"""Unit tests for the `events triggers list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from tests.lib.surface.run import base

import six


class TriggersListTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeTriggers(self, num_triggers):
    """Creates triggers and assigns them as output to ListTriggers."""
    self.triggers = [
        trigger.Trigger.New(
            self.mock_serverless_client, 'fake-project')
        for _ in range(num_triggers)]
    for i, t in enumerate(self.triggers):
      t.name = 't{}'.format(i)
      t.status.conditions = [
          self.serverless_messages.TriggerCondition(
              type='Ready',
              status=six.text_type(bool(i % 2)))
      ]
      t.metadata.selfLink = '/apis/serving.knative.dev/v1alpha1/namespaces/{}/triggers/{}'.format(
          self.namespace.Name(), t.name)
      t.filter_attributes[
          trigger.EVENT_TYPE_FIELD] = 'com.google.event.type.{}'.format(i)
      t.subscriber = 's{}'.format(i)
    self.operations.ListTriggers.return_value = self.triggers

  def testTriggersFailNonGKE(self):
    """Triggers are not yet supported on managed Cloud Run."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events triggers list --region=us-central1')
    self.AssertErrContains(
        'Events are only available with Cloud Run for Anthos.')

  def testTriggersList(self):
    """Two triggers are listable."""
    self._MakeTriggers(num_triggers=2)
    out = self.Run('events triggers list --platform=gke '
                   '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.ListTriggers.assert_called_once_with(
        self._NamespaceRef(project='default'))
    self.assertEqual(out, self.triggers)
    self.AssertOutputEquals(
        """  TRIGGER EVENT TYPE TARGET
           X t0 com.google.event.type.0 s0
           + t1 com.google.event.type.1 s1
        """,
        normalize_space=True)

  def testTriggersListUri(self):
    """Two triggers are listable."""
    self._MakeTriggers(num_triggers=2)
    self._MockConnectionContext(is_gke_context=True)

    self.Run('events triggers list --uri --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.ListTriggers.assert_called_once_with(
        self._NamespaceRef(project='default'))
    self.AssertOutputEquals(
        """https://kubernetes.default/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/triggers/t0
        https://kubernetes.default/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/triggers/t1
        """,
        normalize_space=True)
