# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for prompt_helper module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import config
from googlecloudsdk.core.util import prompt_helper
from tests.lib import sdk_test_base
from tests.lib import test_case


class OptInRecordTest(sdk_test_base.WithOutputCapture, sdk_test_base.SdkBase):

  def SetUp(self):
    self.tempdir = self.CreateTempDir()
    self.StartPatch(
        'googlecloudsdk.core.config.Paths.opt_in_prompting_cache_path',
        new=os.path.join(self.tempdir, 'opt_in_prompt_file'))
    self.last_prompt_time = 1544643641

  def testReadSavePromptRecord(self):
    record = prompt_helper.OptInPromptRecord()
    with record as r:
      r.last_prompt_time = self.last_prompt_time
    new_record = prompt_helper.OptInPromptRecord()
    self.assertEqual(new_record.last_prompt_time, self.last_prompt_time)

  def testReadPromptRecordBadFile(self):
    with open(config.Paths().opt_in_prompting_cache_path, 'w') as f:
      f.write('bad data')
    record = prompt_helper.OptInPromptRecord()
    self.assertEqual(record.last_prompt_time, None)


class OptInPrompterTest(sdk_test_base.WithOutputCapture,
                        sdk_test_base.SdkBase,
                        test_case.WithInput):

  def SetUp(self):
    self.tempdir = self.CreateTempDir()
    self.StartPatch(
        'googlecloudsdk.core.config.Paths.opt_in_prompting_cache_path',
        new=os.path.join(self.tempdir, 'opt_in_prompt_file'))
    self.StartPatch('time.time', return_value=1544651979)
    self.StartPatch('googlecloudsdk.core.log.out.isatty', return_value=True)
    self.StartPatch('googlecloudsdk.core.log.err.isatty', return_value=True)

  def testPrompt(self):
    err = ("You may choose to opt in this\\ncollection now (by choosing \'Y\'"
           " at the below prompt), or at any time in the\\nfuture by running"
           " the following command")
    with prompt_helper.OptInPromptRecord() as pr:
      pr.last_prompt_time = 0
    prompter = prompt_helper.OptInPrompter()
    prompter.Prompt()
    with prompt_helper.OptInPromptRecord() as pr:
      self.assertEqual(pr.last_prompt_time, 1544651979)
    self.assertIn(err, self.GetErr())

  def testShouldNotPromptEarly(self):
    with prompt_helper.OptInPromptRecord() as pr:
      pr.last_prompt_time = 1544651959
    prompter = prompt_helper.OptInPrompter()
    self.assertFalse(prompter.ShouldPrompt())

