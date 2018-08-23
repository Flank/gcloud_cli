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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import command_loading
from googlecloudsdk.core.util import pkg_resources
from tests.lib import sdk_test_base
from tests.lib import test_case


class CommandLoadingTest(sdk_test_base.SdkBase):
  """Test the calliope command loader."""

  def _TestResourcesModule(self):
    mod = CommandLoadingTest.__module__
    mod = '.'.join(mod.split('.')[:-1])
    return mod + '.testdata.test_data'

  def SetUp(self):
    self.source_data = """\
    foo:
      bar:
        a: b
        c: d
      baz:
        e: f
        g: h

    list:
      - k: l
      - m: n
    list2:
      - o: p
      - q: r
    """
    self.answers = {'x': {'a': 'b', 'c': 'd'},
                    'y': 'b',
                    's': [{'a': 'override', 'c': 'd', 'i': 'j'},
                          {'i': 'j'}],
                    't': [{'a': 'b', 'c': 'd', 'e': 'f', 'g': 'h'},
                          {'i': 'j'}],
                    'u': [{'k': 'l'},
                          {'m': 'n'},
                          {'i': 'j'}],
                    'v': [{'k': 'l'},
                          {'m': 'n'},
                          {'o': 'p'},
                          {'q': 'r'},
                          {'i': 'j'}]}

  def testCommonSubstitutions(self):
    self.Touch(self.temp_path, '__init__.yaml', contents=self.source_data)
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
    x: !COMMON foo.bar
    y: !COMMON foo.bar.a

    s:
      - _COMMON_: foo.bar
        i: j
        a: override
      - i: j

    t:
      - _COMMON_: foo.bar,foo.baz
      - i: j

    u:
      - _COMMON_list
      - i: j

    v:
      - _COMMON_list,list2
      - i: j
    """)
    data = command_loading.CreateYamlLoader(main_file).load(
        pkg_resources.GetResourceFromFile(main_file))
    self.assertEqual(data, self.answers)

  def testRefSubstitutions(self):
    self.Touch(self.temp_path, '__init__.yaml', contents=self.source_data)
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
    x: !REF "{mod}:foo.bar"
    y: !REF "{mod}:foo.bar.a"

    s:
      - _REF_: "{mod}:foo.bar"
        i: j
        a: override
      - i: j

    t:
      - _REF_: "{mod}:foo.bar,{mod}:foo.baz"
      - i: j

    u:
      - "_REF_{mod}:list"
      - i: j

    v:
      - "_REF_{mod}:list,{mod}:list2"
      - i: j
    """.format(mod=self._TestResourcesModule()))
    data = command_loading.CreateYamlLoader(main_file).load(
        pkg_resources.GetResourceFromFile(main_file))
    self.assertEqual(data, self.answers)

  def testMissingCommon(self):
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
    x: !COMMON foo.bar
    """)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'references \[common command\] data but it does not exist'):
      command_loading.CreateYamlLoader(main_file).load(
          pkg_resources.GetResourceFromFile(main_file))

  def testMissingAttributeInCommon(self):
    self.Touch(self.temp_path, '__init__.yaml', contents=self.source_data)
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
    x: !COMMON asdf.asdf
    """)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'references \[common command\] data attribute \[asdf\] in path '
        r'\[asdf.asdf\] but it does not exist.'):
      command_loading.CreateYamlLoader(main_file).load(
          pkg_resources.GetResourceFromFile(main_file))

  def testMissingRef(self):
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
        x: !REF asdf
        """)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Invalid Yaml reference: \[asdf\].'):
      command_loading.CreateYamlLoader(main_file).load(
          pkg_resources.GetResourceFromFile(main_file))

  def testMissingRefFile(self):
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
        x: !REF a:foo
        """)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Failed to load Yaml reference file \[.*a\.yaml\]'):
      command_loading.CreateYamlLoader(main_file).load(
          pkg_resources.GetResourceFromFile(main_file))

  def testMissingRefAttribute(self):
    main_file = self.Touch(self.temp_path, 'main.yaml', contents="""\
        x: !REF {mod}:asdf.asdf
        """.format(mod=self._TestResourcesModule()))
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'references \[.*test_data\.yaml\] data attribute \[asdf\] in path \['
        r'asdf.asdf\] but it does not exist.'):
      command_loading.CreateYamlLoader(main_file).load(
          pkg_resources.GetResourceFromFile(main_file))


if __name__ == '__main__':
  test_case.main()
