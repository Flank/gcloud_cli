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

from googlecloudsdk.api_lib.events import broker
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from tests.lib.surface.events import base


class CreateAnthosTestBeta(base.EventsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.core_api_name = 'anthosevents'

  def _MakeBroker(self, broker_name, namespace_name='default'):
    messages = self.mock_client.MESSAGES_MODULE
    broker_obj = broker.Broker.New(self.mock_client, namespace_name)
    broker_obj.name = broker_name
    broker_obj.spec = messages.BrokerSpec()
    return broker_obj

  def testEventTypesFailFailNonGKE(self):
    """This command is for Anthos only."""
    with self.assertRaises(serverless_exceptions.ConfigurationError):
      self.Run('events brokers create default --platform=managed')

  def testCreate(self):
    """Tests successful create broker."""

    # Arrange
    namespace_name = 'default'
    broker_name = 'default'
    broker_obj = self._MakeBroker(broker_name)
    self.operations.CreateBroker.return_value = broker_obj

    # Act
    self.Run('events brokers create default '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')

    # Assert
    self.operations.CreateBroker.assert_called_once_with(
        namespace_name,
        broker_name,
    )
    self.AssertErrContains('Created broker [default]')

  def testUsesCustomNamespace(self):
    # Arrange
    namespace_name = 'roberto'
    broker_name = 'default'
    broker_obj = self._MakeBroker(broker_name)
    self.operations.CreateBroker.return_value = broker_obj

    # Act
    self.Run('events brokers create default --namespace=roberto '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')

    # Assert
    self.operations.CreateBroker.assert_called_once_with(
        namespace_name,
        broker_name,
    )
    self.AssertErrContains('Created broker [default]')

  def testNonDefaultBrokerNameSucceeds(self):
    # Arrange
    namespace_name = 'default'
    broker_name = 'not-default'
    broker_obj = self._MakeBroker(broker_name)
    self.operations.CreateBroker.return_value = broker_obj

    # Act
    self.Run('events brokers create not-default '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')

    # Assert
    self.operations.CreateBroker.assert_called_once_with(
        namespace_name,
        broker_name,
    )
    self.AssertErrContains('Created broker [{}]'.format(broker_name))


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
