# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for cloudbuild execution handlers."""

from __future__ import absolute_import
from __future__ import unicode_literals
import threading
import time

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import keyboard_interrupt
from tests.lib import test_case


class ExecutionTest(test_case.TestCase):

  def testCtrlCMash(self):

    winners = []
    # Protects reads/writes of the winners list.
    winners_lock = threading.Lock()

    def SleepHandler(unused_signal_number, unused_stack_frame):
      with winners_lock:
        winners.append('startup')

      time.sleep(1)

      with winners_lock:
        winners.append('sleep')

    def MockCtrlCHandler(unused_signal_number, unused_stack_frame):
      with winners_lock:
        winners.append('backup')

    self.StartObjectPatch(
        keyboard_interrupt,
        'HandleInterrupt',
        new=MockCtrlCHandler)
    mash_handler = execution.MashHandler(SleepHandler)

    def MashTrigger():
      mash_handler(None, None)

    # Call the handler twice.
    t1 = threading.Thread(target=MashTrigger)
    t1.start()
    t2 = threading.Thread(target=MashTrigger)
    t2.start()

    # Give it a chance to start up and leave the signal.
    time.sleep(.1)

    # Check that the handler began to execute.
    with winners_lock:
      self.assertEqual(winners, ['startup'])

    # Call the handler for the third time, triggering the backup handler.
    t3 = threading.Thread(target=MashTrigger)
    t3.start()

    # Give it a chance to start up and leave the signal.
    time.sleep(.1)

    with winners_lock:
      self.assertEqual(winners, ['startup', 'backup'])

    time.sleep(2)

    with winners_lock:
      self.assertEqual(winners, ['startup', 'backup', 'sleep'])

    t1.join()
    t2.join()
    t3.join()


class CancelBuildHandlerTest(test_case.TestCase):

  def SetUp(self):
    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')

  def testCancelBuildHandler(self):

    self.mocked_cloudbuild_v1.projects_builds.Cancel.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCancelRequest(
            cancelBuildRequest=None,
            id='id',
            projectId='proj',
        ),
        response='ignored'
    )

    build_ref = resources.REGISTRY.Create(
        collection='cloudbuild.projects.builds',
        projectId='proj',
        id='id')

    handler = execution.GetCancelBuildHandler(
        self.mocked_cloudbuild_v1,
        self.cloudbuild_v1_messages,
        build_ref)

    handler(None, None)
