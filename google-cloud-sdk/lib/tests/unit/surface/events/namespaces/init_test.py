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
"""Unit tests for the `events namespaces init` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from tests.lib import cli_test_base
from tests.lib.surface.events import base


class InitTestBeta(base.EventsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.operations.CreateOrReplaceSourcesSecret.return_value = (None)

  def testNamespaceInitFailNonGke(self):
    """This command is for Anthos only."""
    with self.assertRaises(serverless_exceptions.ConfigurationError):
      self.Run(
          'events namespaces init --platform=managed --copy-default-secret')

  def testRequireDefaultFlag(self):
    """Test command requires copy-default-secret flag."""
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('events namespaces init --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a')

  def testNamespaceInitSuccess(self):
    """Tests successful namespaces init."""
    self.Run('events namespaces init --platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a --copy-default-secret')
    self.AssertErrContains('Initialized namespace')


class InitTestAlpha(InitTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testNamespaceInitFailNonGke(self):
    """This command is for anthos only."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events namespaces init --platform=managed '
               '--copy-default-secret')
