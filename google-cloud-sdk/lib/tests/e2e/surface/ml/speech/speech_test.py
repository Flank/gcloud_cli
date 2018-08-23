# -*- coding: utf-8 -*- #
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

"""e2e tests for ml speech command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import test_case


class SpeechTests(e2e_base.WithServiceAuth):
  """E2E tests for ml speech command group."""

  def SetUp(self):
    self.testdata = self.Resource('tests', 'unit', 'command_lib', 'ml',
                                  'speech', 'testdata', 'sample.flac')
    self.track = base.ReleaseTrack.GA

  def testRecognize(self):
    """Test that gcloud ml speech recognize works."""
    result = self.Run(
        'ml speech recognize {} --max-alternatives 1 --language-code en-US'
        .format(self.testdata))
    # Assert results are not empty, that 1 alternative is given, and that
    # transcript is not empty.
    self.assertTrue(result.results)
    self.assertEqual(len(result.results[0].alternatives), 1)
    self.assertTrue(result.results[0].alternatives[0].transcript)

  def testRecognizeLongRunningAndOperations(self):
    """Test gcloud ml speech recognize-long-running and operations group."""
    result = self.Run(
        'ml speech recognize-long-running {} --max-alternatives 1 '
        '--language-code en-US --sample-rate 16000 --async --encoding FLAC'
        .format(self.testdata))

    operation_id = result.name
    op = self.Run('ml speech operations describe {}'.format(operation_id))
    # Assert result of describe command is the operation.
    self.assertEqual(op.name, operation_id)
    final = self.Run('ml speech operations wait {}'.format(operation_id))
    # Assert results are not empty, that there is 1 alternative, that
    # transcript is not empty.
    f = encoding.MessageToPyValue(final)
    self.assertTrue(f['results'])
    self.assertEqual(len(f['results'][0]['alternatives']), 1)
    self.assertTrue(f['results'][0]['alternatives'][0]['transcript'])


if __name__ == '__main__':
  test_case.main()
