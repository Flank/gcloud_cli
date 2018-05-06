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

"""Tests for the prompt_completer module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from tests.lib import test_case


def _MockInstancesCompleter(prefix=''):
  del prefix
  return ['{}-{}-{}-{}'.format(a * 4, b * 5, c * 6, d * 7)
          for a in ('a', 'b', 'c', 'd')
          for b in ('e', 'f', 'g', 'h')
          for c in ('1', '2', '3', '4')
          for d in ('i', 'j', 'k', 'l')]


class PromptCompleterTest(test_case.WithOutputCapture):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetFontCode').side_effect = self.MockGetFontCode
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetRawKey').side_effect = self.MockGetRawKey
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetTermSize').side_effect = self.MockGetTermSize
    self.StartObjectPatch(console_io, 'IsInteractive', return_value=True)
    self.raw_keys = None
    self.term_size = (80, 10)
    self.normal = ''

  def TearDown(self):
    properties.VALUES.core.disable_prompts.Set(True)

  def MockGetFontCode(self, bold=False, italic=False):
    if bold:
      self.normal = '</B>'
      return '<B>'
    elif italic:
      self.normal = '</I>'
      return '<I>'
    else:
      normal = self.normal
      self.normal = ''
      return normal

  def MockGetRawKey(self):
    return self.raw_keys.pop(0) if self.raw_keys else None

  def MockGetTermSize(self):
    return self.term_size

  def SetRawKeys(self, keys):
    self.raw_keys = keys

  def testPromptCompleter(self):
    self.SetRawKeys([
        'a', '\t', '\t',
        'g', '\t', '\t',
        '2', '\t', '\t',
        'l', '\t', '\t',
    ])
    result = console_io.PromptResponse(
        message='Complete this: ', choices=_MockInstancesCompleter)
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Complete this: aaaa-
  aaaa-<B>e</B>eeee-111111-*  aaaa-<B>f</B>ffff-333333-*  aaaa-<B>h</B>hhhh-111111-*
  aaaa-<B>e</B>eeee-222222-*  aaaa-<B>f</B>ffff-444444-*  aaaa-<B>h</B>hhhh-222222-*
  aaaa-<B>e</B>eeee-333333-*  aaaa-<B>g</B>gggg-111111-*  aaaa-<B>h</B>hhhh-333333-*
  aaaa-<B>e</B>eeee-444444-*  aaaa-<B>g</B>gggg-222222-*  aaaa-<B>h</B>hhhh-444444-*
  aaaa-<B>f</B>ffff-111111-*  aaaa-<B>g</B>gggg-333333-*
  aaaa-<B>f</B>ffff-222222-*  aaaa-<B>g</B>gggg-444444-*
Complete this: aaaa-ggggg-
  aaaa-ggggg-<B>1</B>11111-iiiiiii  aaaa-ggggg-<B>3</B>33333-iiiiiii
  aaaa-ggggg-<B>1</B>11111-jjjjjjj  aaaa-ggggg-<B>3</B>33333-jjjjjjj
  aaaa-ggggg-<B>1</B>11111-kkkkkkk  aaaa-ggggg-<B>3</B>33333-kkkkkkk
  aaaa-ggggg-<B>1</B>11111-lllllll  aaaa-ggggg-<B>3</B>33333-lllllll
  aaaa-ggggg-<B>2</B>22222-iiiiiii  aaaa-ggggg-<B>4</B>44444-iiiiiii
  aaaa-ggggg-<B>2</B>22222-jjjjjjj  aaaa-ggggg-<B>4</B>44444-jjjjjjj
  aaaa-ggggg-<B>2</B>22222-kkkkkkk  aaaa-ggggg-<B>4</B>44444-kkkkkkk
  aaaa-ggggg-<B>2</B>22222-lllllll  aaaa-ggggg-<B>4</B>44444-lllllll
Complete this: aaaa-ggggg-222222-
  aaaa-ggggg-222222-<B>i</B>iiiiii  aaaa-ggggg-222222-<B>k</B>kkkkkk
  aaaa-ggggg-222222-<B>j</B>jjjjjj  aaaa-ggggg-222222-<B>l</B>llllll
Complete this: aaaa-ggggg-222222-lllllll
""")
    self.assertEqual('aaaa-ggggg-222222-lllllll', result)

  def testPromptCompleterOnChoices(self):
    self.SetRawKeys([
        'a', '\t', '\t',
        'g', '\t', '\t',
        '2', '\t', '\t',
        'l', '\t', '\t',
    ])
    choices = list(_MockInstancesCompleter())
    choices[0] = 'aaaa-'
    result = console_io.PromptResponse(
        message='Complete this: ',
        choices=choices)
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Complete this: aaaa-
  aaaa-                aaaa-<B>f</B>ffff-222222-*  aaaa-<B>g</B>gggg-444444-*
  aaaa-<B>e</B>eeee-111111-*  aaaa-<B>f</B>ffff-333333-*  aaaa-<B>h</B>hhhh-111111-*
  aaaa-<B>e</B>eeee-222222-*  aaaa-<B>f</B>ffff-444444-*  aaaa-<B>h</B>hhhh-222222-*
  aaaa-<B>e</B>eeee-333333-*  aaaa-<B>g</B>gggg-111111-*  aaaa-<B>h</B>hhhh-333333-*
  aaaa-<B>e</B>eeee-444444-*  aaaa-<B>g</B>gggg-222222-*  aaaa-<B>h</B>hhhh-444444-*
  aaaa-<B>f</B>ffff-111111-*  aaaa-<B>g</B>gggg-333333-*
Complete this: aaaa-ggggg-
  aaaa-ggggg-<B>1</B>11111-iiiiiii  aaaa-ggggg-<B>3</B>33333-iiiiiii
  aaaa-ggggg-<B>1</B>11111-jjjjjjj  aaaa-ggggg-<B>3</B>33333-jjjjjjj
  aaaa-ggggg-<B>1</B>11111-kkkkkkk  aaaa-ggggg-<B>3</B>33333-kkkkkkk
  aaaa-ggggg-<B>1</B>11111-lllllll  aaaa-ggggg-<B>3</B>33333-lllllll
  aaaa-ggggg-<B>2</B>22222-iiiiiii  aaaa-ggggg-<B>4</B>44444-iiiiiii
  aaaa-ggggg-<B>2</B>22222-jjjjjjj  aaaa-ggggg-<B>4</B>44444-jjjjjjj
  aaaa-ggggg-<B>2</B>22222-kkkkkkk  aaaa-ggggg-<B>4</B>44444-kkkkkkk
  aaaa-ggggg-<B>2</B>22222-lllllll  aaaa-ggggg-<B>4</B>44444-lllllll
Complete this: aaaa-ggggg-222222-
  aaaa-ggggg-222222-<B>i</B>iiiiii  aaaa-ggggg-222222-<B>k</B>kkkkkk
  aaaa-ggggg-222222-<B>j</B>jjjjjj  aaaa-ggggg-222222-<B>l</B>llllll
Complete this: aaaa-ggggg-222222-lllllll
""")
    self.assertEqual('aaaa-ggggg-222222-lllllll', result)

  def testPromptCompleterBackup(self):
    self.SetRawKeys([
        'a', '\t', '\t',
        '\b', '\b', '\b', '\b', '\b', '\b', '\b', '\b',
        'd', '\t', '\t',
    ])
    result = console_io.PromptResponse(
        message='Complete this: ', choices=_MockInstancesCompleter)
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Complete this: aaaa-
  aaaa-<B>e</B>eeee-111111-*  aaaa-<B>f</B>ffff-333333-*  aaaa-<B>h</B>hhhh-111111-*
  aaaa-<B>e</B>eeee-222222-*  aaaa-<B>f</B>ffff-444444-*  aaaa-<B>h</B>hhhh-222222-*
  aaaa-<B>e</B>eeee-333333-*  aaaa-<B>g</B>gggg-111111-*  aaaa-<B>h</B>hhhh-333333-*
  aaaa-<B>e</B>eeee-444444-*  aaaa-<B>g</B>gggg-222222-*  aaaa-<B>h</B>hhhh-444444-*
  aaaa-<B>f</B>ffff-111111-*  aaaa-<B>g</B>gggg-333333-*
  aaaa-<B>f</B>ffff-222222-*  aaaa-<B>g</B>gggg-444444-*
Complete this: aaaa-\b \b\b \b\b \b\b \b\b \bdddd-
  dddd-<B>e</B>eeee-111111-*  dddd-<B>f</B>ffff-333333-*  dddd-<B>h</B>hhhh-111111-*
  dddd-<B>e</B>eeee-222222-*  dddd-<B>f</B>ffff-444444-*  dddd-<B>h</B>hhhh-222222-*
  dddd-<B>e</B>eeee-333333-*  dddd-<B>g</B>gggg-111111-*  dddd-<B>h</B>hhhh-333333-*
  dddd-<B>e</B>eeee-444444-*  dddd-<B>g</B>gggg-222222-*  dddd-<B>h</B>hhhh-444444-*
  dddd-<B>f</B>ffff-111111-*  dddd-<B>g</B>gggg-333333-*
  dddd-<B>f</B>ffff-222222-*  dddd-<B>g</B>gggg-444444-*
Complete this: dddd-
""")
    self.assertEqual('dddd-', result)


if __name__ == '__main__':
  test_case.main()
