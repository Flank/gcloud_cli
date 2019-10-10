# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Unit tests for the core.util.scaled_integer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import scaled_integer
from tests.lib import parameterized
from tests.lib.parameterized_line_no import LineNo as T


class ExceptionalParameterizedTestBase(parameterized.TestCase):
  """Parameterized test case runner with exception handling."""

  def RunTestCase(self, fun, arg, expected_value, kwargs):

    def _Name(e):
      try:
        return e.__name__
      except AttributeError:
        return e.__class__.__name__

    expected_exception = kwargs.pop('exception', None)
    actual_exception = None
    try:
      actual_value = fun(arg, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
      actual_exception = e
    if _Name(expected_exception) != _Name(actual_exception):
      if expected_exception and actual_exception:
        self.fail('{} exception expected, got {}({}).'.format(
            _Name(expected_exception),
            _Name(actual_exception),
            actual_exception))
      elif expected_exception:
        self.fail('{} exception expected.'.format(_Name(expected_exception)))
      else:
        self.fail('{}({}) exception not expected.'.format(
            _Name(actual_exception),
            actual_exception))
    if expected_exception:
      return None
    self.assertEqual(expected_value, actual_value)
    return actual_value


class ParseFormatIntegerTest(ExceptionalParameterizedTestBase):
  """string => Parse => Format round trip tests."""

  @parameterized.named_parameters(
      # string value pretty kwargs

      T(None, None, None, exception=TypeError),
      T('', None, None, exception=ValueError),
      T('1GB1KB', None, None, exception=ValueError),
      T('1TB1KiB', None, None, exception=ValueError),
      T('1kilobyte', None, None, exception=ValueError),
      T('1 KB', None, None, exception=ValueError),
      T('1   KB', None, None, exception=ValueError),
      T('10', 10000, '10kb/s', type_abbr='b/s', default_unit='Kb/s',
        exception=ValueError),
      T('10', 10000, '10kb/s', type_abbr='b/s', default_unit='Kbs',
        exception=ValueError),

      T('0', 0, '0B'),
      T('0', 0, '0B', type_abbr='B'),
      T('0', 0, '0', type_abbr=''),
      T('1', 1, '1B'),
      T('1', 1, '1B', default_unit=''),
      T('1', 1, '1B', default_unit=None),
      T('1', 1000, '1kB', default_unit='K'),
      T('4000', 4000000, '4MB', default_unit='K'),
      T('7168', 7340032, '7MiB', default_unit='Ki'),

      T('1k', 1000, '1kB'),
      T('1kb', 1000, '1kB'),
      T('1kB', 1000, '1kB'),
      T('1ki', 1024, '1kiB'),
      T('1kib', 1024, '1kiB'),
      T('1kiB', 1024, '1kiB'),
      T('1K', 1000, '1kB'),
      T('1Kb', 1000, '1kB'),
      T('1KB', 1000, '1kB'),
      T('1Ki', 1024, '1kiB'),
      T('1Kib', 1024, '1kiB'),
      T('1KiB', 1024, '1kiB'),

      T('1kb/s', 1000, '1kb/s', type_abbr='b/s'),
      T('1kib', 1024, '1kib/s', type_abbr='b/s'),
      T('1kib/', 1024, '1kib/s', type_abbr='b/s'),
      T('1ki', 1024, '1kib/s', type_abbr='b/s'),
      T('1Mb', 1000000, '1MB'),
      T('1000000', 1000000, '1MB'),
      T('1MiB', 1048576, '1MiB'),
      T('1048576', 1048576, '1MiB'),
      T('1GB', 1000000000, '1GB'),
      T('1000000000', 1000000000, '1GB'),
      T('1GiB', 1073741824, '1GiB'),
      T('1073741824', 1073741824, '1GiB'),

      T('1B', 1, '1B'),
      T('0B', 0, '0B'),
      T('000B', 0, '0B'),

      T('0KB', 0, '0B'),
      T('1KB', 1000, '1kB'),
      T('25KB', 25000, '25kB'),
      T('100KB', 100000, '100kB'),

      T('0KiB', 0, '0B'),
      T('1KiB', 1024, '1kiB'),
      T('25KiB', 25600, '25kiB'),
      T('100KiB', 102400, '100kiB'),

      T('0MB', 0, '0B'),
      T('1MB', 1000000, '1MB'),
      T('25MB', 25000000, '25MB'),
      T('100MB', 100000000, '100MB'),

      T('0MiB', 0, '0B'),
      T('1MiB', 1048576, '1MiB'),
      T('25MiB', 26214400, '25MiB'),
      T('100MiB', 104857600, '100MiB'),

      T('0GB', 0, '0B'),
      T('1GB', 1000000000, '1GB'),
      T('25GB', 25000000000, '25GB'),
      T('100GB', 100000000000, '100GB'),

      T('0GiB', 0, '0B'),
      T('1GiB', 1073741824, '1GiB'),
      T('25GiB', 26843545600, '25GiB'),
      T('100GiB', 107374182400, '100GiB'),

      T('0TB', 0, '0B'),
      T('1TB', 1000000000000, '1TB'),
      T('25TB', 25000000000000, '25TB'),
      T('100TB', 100000000000000, '100TB'),

      T('0TiB', 0, '0B'),
      T('1TiB', 1099511627776, '1TiB'),
      T('25TiB', 27487790694400, '25TiB'),
      T('100TiB', 109951162777600, '100TiB'),

      T('0PB', 0, '0B'),
      T('1PB', 1000000000000000, '1PB'),
      T('25PB', 25000000000000000, '25PB'),
      T('100PB', 100000000000000000, '100PB'),

      T('0PiB', 0, '0B'),
      T('1PiB', 1125899906842624, '1PiB'),
      T('25PiB', 28147497671065600, '25PiB'),
      T('100PiB', 112589990684262400, '100PiB'),

      T('1B', 1, '1B'),
      T('1k', 1000, '1kB'),
      T('1Mi', 1048576, '1MiB'),

      T('1GB', 1000000000, '1GB'),
      T('1gb', 1000000000, '1GB'),
      T('1GiB', 1073741824, '1GiB'),
      T('1gIb', 1073741824, '1GiB'),
      T('50GB', 50000000000, '50GB'),
      T('55GiB', 59055800320, '55GiB'),
      T('100GB', 100000000000, '100GB'),
      T('100GiB', 107374182400, '100GiB'),

      T('10', 10000, '10kb/s', type_abbr='b/s', default_unit='k'),
      T('20k', 20000, '20kb/s', type_abbr='b/s', default_unit='k'),
      T('30Mb', 30000000, '30Mb/s', type_abbr='b/s', default_unit='k'),
      T('40Gbs', 40000000000, '40Gb/s', type_abbr='b/s', default_unit='k'),
      T('50Gib/', 53687091200, '50Gib/s', type_abbr='b/s', default_unit='k'),
      T('60Pb', 60000000000000000, '60Pb/s', type_abbr='b/s', default_unit='k'),

  )
  def testParseFormatInteger(
      self, string, expected_value, expected_format, kwargs=None):
    if kwargs is None:
      kwargs = {}
    actual_value = self.RunTestCase(
        scaled_integer.ParseInteger, string, expected_value, kwargs)
    if actual_value is None:
      return
    kwargs.pop('default_unit', None)
    actual_format = scaled_integer.FormatInteger(actual_value, **kwargs)
    self.assertEqual(expected_format, actual_format)

  @parameterized.named_parameters(
      # string value pretty kwargs

      T(None, None, None, exception=TypeError),
      T('', None, None, exception=ValueError),
      T('1GB1KB', None, None, exception=ValueError),
      T('1TB1KiB', None, None, exception=ValueError),
      T('1kilobyte', None, None, exception=ValueError),
      T('1 KB', None, None, exception=ValueError),
      T('1   KB', None, None, exception=ValueError),
      T('10', 10240, '10', type_abbr='b/s', default_unit='Kb/s',
        exception=ValueError),
      T('10', 10240, '10', type_abbr='b/s', default_unit='Kbs',
        exception=ValueError),

      T('0', 0, '0B'),
      T('0', 0, '0B', type_abbr='B'),
      T('0', 0, '0', type_abbr=''),
      T('1', 1, '1B'),
      T('1', 1024, '1kiB', default_unit='K'),
      T('4000', 4096000, '4000kiB', default_unit='K'),
      T('7168', 7340032, '7MiB', default_unit='Ki'),

      T('1k', 1024, '1kiB'),
      T('1kb', 1024, '1kiB'),
      T('1kB', 1024, '1kiB'),
      T('1ki', 1024, '1kiB'),
      T('1kib', 1024, '1kiB'),
      T('1kiB', 1024, '1kiB'),
      T('1K', 1024, '1kiB'),
      T('1Kb', 1024, '1kiB'),
      T('1KB', 1024, '1kiB'),
      T('1Ki', 1024, '1kiB'),
      T('1Kib', 1024, '1kiB'),
      T('1KiB', 1024, '1kiB'),

      T('1kb/s', 1024, '1kib/s', type_abbr='b/s'),
      T('1kib', 1024, '1kib/s', type_abbr='b/s'),
      T('1kib/', 1024, '1kib/s', type_abbr='b/s'),
      T('1ki', 1024, '1kib/s', type_abbr='b/s'),
      T('1Mb', 1048576, '1MiB'),
      T('1000000', 1000000, '1MB'),
      T('1MiB', 1048576, '1MiB'),
      T('1048576', 1048576, '1MiB'),
      T('1GB', 1073741824, '1GiB'),
      T('1000000000', 1000000000, '1GB'),
      T('1GiB', 1073741824, '1GiB'),
      T('1073741824', 1073741824, '1GiB'),

      T('1B', 1, '1B'),
      T('0B', 0, '0B'),
      T('000B', 0, '0B'),

      T('0KB', 0, '0B'),
      T('1KB', 1024, '1kiB'),
      T('25KB', 25600, '25kiB'),
      T('100KB', 102400, '100kiB'),

      T('0KiB', 0, '0B'),
      T('1KiB', 1024, '1kiB'),
      T('25KiB', 25600, '25kiB'),
      T('100KiB', 102400, '100kiB'),

      T('0MB', 0, '0B'),
      T('1MB', 1048576, '1MiB'),
      T('25MB', 26214400, '25MiB'),
      T('100MB', 104857600, '100MiB'),

      T('0MiB', 0, '0B'),
      T('1MiB', 1048576, '1MiB'),
      T('25MiB', 26214400, '25MiB'),
      T('100MiB', 104857600, '100MiB'),

      T('0GB', 0, '0B'),
      T('1GB', 1073741824, '1GiB'),
      T('25GB', 26843545600, '25GiB'),
      T('100GB', 107374182400, '100GiB'),

      T('0GiB', 0, '0B'),
      T('1GiB', 1073741824, '1GiB'),
      T('25GiB', 26843545600, '25GiB'),
      T('100GiB', 107374182400, '100GiB'),

      T('0TB', 0, '0B'),
      T('1TB', 1099511627776, '1TiB'),
      T('25TB', 27487790694400, '25TiB'),
      T('100TB', 109951162777600, '100TiB'),

      T('0TiB', 0, '0B'),
      T('1TiB', 1099511627776, '1TiB'),
      T('25TiB', 27487790694400, '25TiB'),
      T('100TiB', 109951162777600, '100TiB'),

      T('0PB', 0, '0B'),
      T('1PB', 1125899906842624, '1PiB'),
      T('25PB', 28147497671065600, '25PiB'),
      T('100PB', 112589990684262400, '100PiB'),

      T('0PiB', 0, '0B'),
      T('1PiB', 1125899906842624, '1PiB'),
      T('25PiB', 28147497671065600, '25PiB'),
      T('100PiB', 112589990684262400, '100PiB'),

      T('1B', 1, '1B'),
      T('1k', 1024, '1kiB'),
      T('1Mi', 1048576, '1MiB'),

      T('1GB', 1073741824, '1GiB'),
      T('1gb', 1073741824, '1GiB'),
      T('1GiB', 1073741824, '1GiB'),
      T('1gIb', 1073741824, '1GiB'),
      T('50GB', 53687091200, '50GiB'),
      T('55GiB', 59055800320, '55GiB'),
      T('100GB', 107374182400, '100GiB'),
      T('100GiB', 107374182400, '100GiB'),

      T('10', 10240, '10kib/s', type_abbr='b/s', default_unit='k'),
      T('20k', 20480, '20kib/s', type_abbr='b/s', default_unit='k'),
      T('30Mb', 31457280, '30Mib/s', type_abbr='b/s', default_unit='k'),
      T('40Gbs', 42949672960, '40Gib/s', type_abbr='b/s', default_unit='k'),
      T('50Gib/', 53687091200, '50Gib/s', type_abbr='b/s', default_unit='k'),
      T('60P', 67553994410557440, '60Pib/s', type_abbr='b/s', default_unit='k'),

  )
  def testParseFormatBinaryInteger(
      self, string, expected_value, expected_format, kwargs=None):
    if kwargs is None:
      kwargs = {}
    actual_value = self.RunTestCase(
        scaled_integer.ParseBinaryInteger, string, expected_value, kwargs)
    if actual_value is None:
      return
    kwargs.pop('default_unit', None)
    actual_format = scaled_integer.FormatInteger(actual_value, **kwargs)
    self.assertEqual(expected_format, actual_format)


class GetUnitSizeTest(ExceptionalParameterizedTestBase):
  """GetUnitSize and GetBinaryUnitSize tests."""

  @parameterized.named_parameters(
      # unit size

      T(None, 1),
      T('', 1),
      T('B', 1),
      T('kb', 1000),
      T('kib', 1024),
      T('kb/s', 1000, type_abbr='b/s'),
      T('kib/s', 1024, type_abbr='b/s'),
      T('Kb/s', 1000, type_abbr='b/s'),
      T('Kib/s', 1024, type_abbr='b/s'),
      T('m', 1000000),
      T('mi', 1048576),
      T('GB', 1000000000),
      T('GiB', 1073741824),
  )
  def testGetUnitSize(self, unit, expected_size, kwargs=None):
    if kwargs is None:
      kwargs = {}
    self.RunTestCase(scaled_integer.GetUnitSize, unit, expected_size, kwargs)

  @parameterized.named_parameters(
      # unit size

      T(None, 1),
      T('', 1),
      T('B', 1),
      T('kb', 1024),
      T('kib', 1024),
      T('kb/s', 1024, type_abbr='b/s'),
      T('kib/s', 1024, type_abbr='b/s'),
      T('Kb/s', 1024, type_abbr='b/s'),
      T('Kib/s', 1024, type_abbr='b/s'),
      T('m', 1048576),
      T('mi', 1048576),
      T('GB', 1073741824),
      T('GiB', 1073741824),
  )
  def testGetBinaryUnitSize(self, unit, expected_size, kwargs=None):
    if kwargs is None:
      kwargs = {}
    self.RunTestCase(scaled_integer.GetBinaryUnitSize, unit, expected_size,
                     kwargs)
