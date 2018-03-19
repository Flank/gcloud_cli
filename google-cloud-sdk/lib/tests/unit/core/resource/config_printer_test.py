# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit tests for the config_printer module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import platforms
from tests.lib.core.resource import resource_printer_test_base


_ENV_RESOURCE = {
    'Søɨŧɇnłɏ': 'quote',
    'quote': "ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",
}

_ENV_RESOURCE_WITH_LISTS = {
    'core': {
        'items': [
            {'abc': 'XYZ'},
            {'xyz': 123},
        ],
        'anon': [123, 'abc', 'pdq', 'xyz'],
    },
}


class ConfigPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf8')

  def SetRunningOnWindows(self, val):
    self.StartObjectPatch(
        platforms.OperatingSystem, 'IsWindows').return_value = val

  def Printer(self, fmt='config'):
    self._printer = resource_printer.Printer(fmt)
    return self._printer

  def testEmpty(self):
    printer = self.Printer()
    printer.Finish()
    self.AssertOutputEquals('')

  def testSingleResource(self):
    resource = {
        'core': {
            'name_1': 'value_1',
            'name_2': None,
            'name_3': 0,
        },
    }
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals("""\
[core]
name_1 = value_1
name_2 (unset)
name_3 = 0
""")

  def testSingleResourceWIthTitle(self):
    resource = {
        'core': {
            'name_1': 'value_1',
            'name_2': None,
            'name_3': 0,
        },
    }
    printer = self.Printer('config[title="Config Data\n"]')
    printer.AddRecord(resource)
    self.AssertOutputEquals("""\
Config Data

[core]
name_1 = value_1
name_2 (unset)
name_3 = 0
""")

  def testMultipleResource(self):
    resource = {
        'core': {
            'name_1': 'value_1',
            'name_2': None,
            'name_3': 0,
        },
        'test': {
            'test_1': 'value_1',
            'test_2': None,
            'test_3': 0,
        },
        'undefined': {
            'undefined_1': None,
            'undefined_2': None,
            'undefined_3': None,
        },
    }
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals("""\
[core]
name_1 = value_1
name_2 (unset)
name_3 = 0
[test]
test_1 = value_1
test_2 (unset)
test_3 = 0
[undefined]
undefined_1 (unset)
undefined_2 (unset)
undefined_3 (unset)
""")

  def testMultipleResourceUnicodeNoUndefined(self):
    resource = {
        'Ṁöë': {
            'quote': ".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW",
            'name_2': None,
            'Søɨŧɇnłɏ!': 0,
        },
        'Larry': {
            'quote': "ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",
            'test_2': None,
            'Søɨŧɇnłɏ!': 1,
        },
        'Shemp': {
            'quote': 'Hey, Ṁöë! Hey, Larry!',
            'test_2': None,
            'Søɨŧɇnłɏ!': 2,
        },
        'Curly': {
            'quote': 'Søɨŧɇnłɏ!',
            'test_2': None,
            'Søɨŧɇnłɏ!': 3,
        },
        'undefined': {
            'quote': None,
            'undefined_2': None,
            'Søɨŧɇnłɏ!': None,
        },
    }
    printer = self.Printer('config[no-undefined]')
    printer.AddRecord(resource)
    self.AssertOutputEquals("""\
[Curly]
Søɨŧɇnłɏ! = 3
quote = Søɨŧɇnłɏ!
[Larry]
Søɨŧɇnłɏ! = 1
quote = ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
[Shemp]
Søɨŧɇnłɏ! = 2
quote = Hey, Ṁöë! Hey, Larry!
[Ṁöë]
Søɨŧɇnłɏ! = 0
quote = .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
""")

  def testNestedResource(self):
    resource = {
        'core': {
            'name_1': 'value_1',
            'name_2': None,
            'name_3': 0,
            'test': {
                'test_1': 'value_1',
                'test_2': None,
                'test_3': 0,
                'undefined': {
                    'undefined_1': None,
                    'undefined_2': None,
                    'undefined_3': None,
                },
            },
            'anon': [123, 'abc', 'pdq', 'xyz'],
        },
    }
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals("""\
[core]
name_1 = value_1
name_2 (unset)
name_3 = 0
[core.anon]
0 = 123
1 = abc
2 = pdq
3 = xyz
[core.test]
test_1 = value_1
test_2 (unset)
test_3 = 0
[core.test.undefined]
undefined_1 (unset)
undefined_2 (unset)
undefined_3 (unset)
""")

  def testNestedResourceEmptySection(self):
    resource = {
        'core': {
            'name_1': 'value_1',
            'name_2': None,
            'name_3': 0,
            'test': {
                'undefined': {
                    'undefined_1': None,
                    'undefined_2': None,
                    'undefined_3': None,
                },
            },
            'anon': [123, 'abc', 'pdq', 'xyz'],
        },
    }
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals("""\
[core]
name_1 = value_1
name_2 (unset)
name_3 = 0
[core.anon]
0 = 123
1 = abc
2 = pdq
3 = xyz
[core.test.undefined]
undefined_1 (unset)
undefined_2 (unset)
undefined_3 (unset)
""")

  def testNoneResource(self):
    resource = None
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals('')

  def testScalarResource(self):
    resource = 'abc'
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals('')

  def testListResource(self):
    resource = [123, 'abc', 'pdq', 'xyz']
    printer = self.Printer()
    printer.AddRecord(resource)
    self.AssertOutputEquals('')

  def testExportAttribute(self):
    self.SetRunningOnWindows(False)
    printer = self.Printer('config[export]')
    printer.AddRecord(_ENV_RESOURCE)
    self.AssertOutputEquals("""\
export Søɨŧɇnłɏ=quote
export quote='ι ∂ι∂η'"'"'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'"'"'т ѕαу ησ.'
""")

  def testExportAttributeWindows(self):
    self.SetRunningOnWindows(True)
    printer = self.Printer('config[export]')
    printer.AddRecord(_ENV_RESOURCE)
    self.AssertOutputEquals("""\
set Søɨŧɇnłɏ=quote
set quote='ι ∂ι∂η'"'"'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'"'"'т ѕαу ησ.'
""")

  def testExportWithListValues(self):
    self.SetRunningOnWindows(False)
    printer = self.Printer('config[export]')
    printer.AddRecord(_ENV_RESOURCE_WITH_LISTS)
    self.AssertOutputEquals("""\
export core_anon_I0=123
export core_anon_I1=abc
export core_anon_I2=pdq
export core_anon_I3=xyz
export core_items_abc=XYZ
export core_items_xyz=123
""")

  def testExportWithListValuesWindows(self):
    self.SetRunningOnWindows(True)
    printer = self.Printer('config[export]')
    printer.AddRecord(_ENV_RESOURCE_WITH_LISTS)
    self.AssertOutputEquals("""\
set core_anon_I0=123
set core_anon_I1=abc
set core_anon_I2=pdq
set core_anon_I3=xyz
set core_items_abc=XYZ
set core_items_xyz=123
""")

  def testUnsetAttribute(self):
    self.SetRunningOnWindows(False)
    printer = self.Printer('config[unset]')
    printer.AddRecord(_ENV_RESOURCE)
    self.AssertOutputEquals("""\
unset Søɨŧɇnłɏ
unset quote
""")

  def testUnsetAttributeWindows(self):
    self.SetRunningOnWindows(True)
    printer = self.Printer('config[unset]')
    printer.AddRecord(_ENV_RESOURCE)
    self.AssertOutputEquals("""\
set Søɨŧɇnłɏ=
set quote=
""")

  def testUnsetWithListValues(self):
    self.SetRunningOnWindows(False)
    printer = self.Printer('config[unset]')
    printer.AddRecord(_ENV_RESOURCE_WITH_LISTS)
    self.AssertOutputEquals("""\
unset core_anon_I0
unset core_anon_I1
unset core_anon_I2
unset core_anon_I3
unset core_items_abc
unset core_items_xyz
""")

  def testUnsetWithListValuesWindows(self):
    self.SetRunningOnWindows(True)
    printer = self.Printer('config[unset]')
    printer.AddRecord(_ENV_RESOURCE_WITH_LISTS)
    self.AssertOutputEquals("""\
set core_anon_I0=
set core_anon_I1=
set core_anon_I2=
set core_anon_I3=
set core_items_abc=
set core_items_xyz=
""")


if __name__ == '__main__':
  resource_printer_test_base.main()
