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
"""Unit tests for the `events brokers create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from tests.lib.surface.events import base


class CreateAnthosTestBeta(base.EventsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.core_api_name = 'anthosevents'

  def testEventTypesFailFailNonGKE(self):
    """This command is for Anthos only."""
    with self.assertRaises(serverless_exceptions.ConfigurationError):
      self.Run('events brokers create default ' '--platform=managed')

  def testCreate(self):
    """Tests successful init with success message."""
    self.Run('events brokers create default '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.operations.UpdateNamespaceWithLabels.assert_called_once_with(
        self._CoreNamespaceRef('default'),
        {'knative-eventing-injection': 'enabled'})
    self.AssertErrContains('Created broker [default]')

  def testUsesCustomNamespace(self):
    self.Run('events brokers create default --namespace=roberto '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.operations.UpdateNamespaceWithLabels.assert_called_once_with(
        self._CoreNamespaceRef('roberto'),
        {'knative-eventing-injection': 'enabled'})

  def testNonDefaultBrokerNameFails(self):
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events brokers create not-default '
               '--platform=gke --cluster=cluster-1 '
               '--cluster-location=us-central1-a')
    self.AssertErrContains('Only brokers named "default" may be created.')


class CreateAnthosTestAlpha(CreateAnthosTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.core_api_name = 'anthosevents'

  def testEventTypesFailFailNonGKE(self):
    """This command is only for initializing a cluster."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events brokers create default '
               '--platform=managed --region=us-central1')
    self.AssertErrContains(
        'This command is only available with Cloud Run for Anthos.')
