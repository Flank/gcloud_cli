# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Base classes for debug command group tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time
import uuid

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.api_lib.debug import errors
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class DebugTest(cli_test_base.CliTestBase):
  """Base class for all debug CLI surface tests."""

  def RunDebug(self, command):
    return self.Run(['debug'] + command)

  def RunDebugBeta(self, command):
    return self.Run(['beta', 'debug'] + command)


class DebugSdkTest(sdk_test_base.WithFakeAuth, DebugTest):
  """Base class for debug CLI surface unit tests."""

  def SetUp(self):
    self.project_id = 'test-project'
    self.project_number = 12345
    self.messages = core_apis.GetMessagesModule('clouddebugger', 'v2')
    self.debuggee = debug.Debuggee(self.messages.Debuggee(
        project=str(self.project_number),
        id='test-default-debuggee', uniquifier='unique-12345',
        labels=self.messages.Debuggee.LabelsValue(
            additionalProperties=[
                self.messages.Debuggee.LabelsValue.AdditionalProperty(
                    key='module', value='test-gae-module')])))
    self.StartObjectPatch(
        debug.Debugger, 'DefaultDebuggee', return_value=self.debuggee)


class DebugIntegrationTest(e2e_base.WithServiceAuth, DebugTest):
  """Base class for all debug integration tests."""

  DEBUGGEE_UNIQUIFIER = 'dummy-uniquifier/{0}'.format(uuid.uuid4().hex)

  def SetUp(self):
    # Register a dummy debuggee with the Cloud Debugger.
    project_id = properties.VALUES.core.project.Get(required=True)
    self.debugger = debug.Debugger(project_id)
    self.debuggee = None
    self._RegisterDebuggee()

  def TearDown(self):
    # Delete all breakpoints associated with the temporary debuggee
    try:
      breakpoints = self.debuggee.ListBreakpoints()
      for b in breakpoints:
        self.debuggee.DeleteBreakpoint(b.id)
    except errors.UnknownHttpError:
      log.exception('Ignoring exception during cleanup.')

  @sdk_test_base.Retry(
      why=('RegisterDebuggee may time out, and the registration may take time '
           'to propagate.'),
      max_retrials=6, sleep_ms=5000)
  def _RegisterDebuggee(self):
    if not self.debuggee:
      self.debuggee = self.debugger.RegisterDebuggee(
          'gcloud integration test dummy target',
          self.DEBUGGEE_UNIQUIFIER)
    # Wait for the backend caches to get in sync. It usually takes << 1 sec.
    # We have no way of forcing affinity to a cell, so checking for the
    # existence of the debuggee is no guarantee that the tests will be
    # able to find it. Wait a fixed 3 seconds, which should be sufficient.
    time.sleep(3)


class DebugIntegrationTestWithTargetArg(DebugIntegrationTest):
  """Base class for all debug integration tests."""

  def RunDebug(self, command):
    return self.Run(
        ['beta', 'debug'] + command + ['--target', self.debuggee.target_id])
