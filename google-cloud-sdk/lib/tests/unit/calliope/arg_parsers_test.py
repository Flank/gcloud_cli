# -*- coding: utf-8 -*- #

# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for the arg_parsers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import collections
import datetime
import os
import re

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import display_info
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case
from tests.lib.calliope import util

import six


STRICT_DEPRECATION_FORMAT = (
    "The '--' argument must be specified between gcloud specific "
    "args on the left and {dest} on the right."
    )


def StrictDeprecationMessage(dest):
  return STRICT_DEPRECATION_FORMAT.format(dest=dest)


class BoundedTypeTest(sdk_test_base.SdkBase):
  """Unit tests for _BoundedType-derived parser."""

  def SetUp(self):
    self.int_parser = arg_parsers.BoundedInt(0, 1000)
    self.float_parser = arg_parsers.BoundedFloat(0.0, 1000.0)

  def testCorrectInputs(self):
    self.assertEqual(self.int_parser('123'), 123)
    self.assertAlmostEqual(self.float_parser('123.456'), 123.456)

  def testUnderLowerBound(self):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.int_parser('-1')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.float_parser('-0.1')

  def testOverUpperBound(self):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.int_parser('1001')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.float_parser('1000.1')

  def testUnlimited(self):
    unlimited_int_parser = arg_parsers.BoundedInt(0, 1, unlimited=True)
    self.assertTrue(unlimited_int_parser('unlimited') is None)
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.int_parser('unlimited')


class RegexpValidatorTest(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    # This is a contrived example; you would normally use int()
    self._only_digits_type = arg_parsers.RegexpValidator(
        r'[0-9]+', 'A foo consists of one or more digits.')

  def testRegexpMatches(self):
    for value in ['0', '12', '99999']:
      self.assertEqual(self._only_digits_type(value), value)

  def testRegexpNotMatches(self):
    for value in ['a', '12a', '?', '']:
      with self.assertRaisesRegex(
          arg_parsers.ArgumentTypeError,
          re.escape(('Bad value [{0}]: A foo consists of one or more digits'
                     '').format(value))):
        self._only_digits_type(value)


class CustomFunctionValidatorTest(test_case.TestCase):

  def _EvenType(self):
    # Validator function. try-catch block omitted to test exceptions.
    is_even = lambda value: int(value) % 2 == 0
    return arg_parsers.CustomFunctionValidator(is_even, 'This is not even!')

  def _CustomIntType(self):
    # Validator function. try-catch block omitted to test exceptions.
    validate = lambda n: n in (1, 3)
    return arg_parsers.CustomFunctionValidator(
        validate,
        '1 or 3 must it be.',
        parser=arg_parsers.BoundedInt(1, 3))

  def testFunctionReturnsTrue(self):
    arg_type = self._EvenType()
    for value in ['0', '14', '2568']:
      self.assertEqual(arg_type(value), value)

  def testFunctionDoesNotReturnTrue(self):
    arg_type = self._EvenType()
    for value in ['3', '13', '3457']:
      with self.assertRaisesRegex(
          arg_parsers.ArgumentTypeError,
          re.escape('Bad value [{0}]: This is not even!'.format(value))):
        arg_type(value)

  def testChainedParserValidValue(self):
    arg_type = self._CustomIntType()
    for value in ['1', '3']:
      self.assertEqual(arg_type(value), int(value))

  def testChainedParserInValidValue(self):
    arg_type = self._CustomIntType()
    for value in ['-13', '0', '2', '3457']:
      with self.assertRaisesRegex(
          arg_parsers.ArgumentTypeError,
          re.escape('Bad value [{0}]: 1 or 3 must it be.'.format(value))):
        arg_type(value)


class DisplayInfoTest(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()

  def testNoDisplayInfo(self):
    self.parser.parse_args([])
    self.assertEqual(None, self.parser.display_info.format)
    self.assertEqual(None, self.parser.display_info.filter)
    self.assertEqual({}, self.parser.display_info.transforms)
    self.assertEqual({}, self.parser.display_info.aliases)

  def testDisplayInfo(self):
    self.parser.display_info.AddFormat('yaml')
    self.parser.display_info.AddFilter('foo.bar=baz')
    self.parser.display_info.AddAliases({'foo': 'bar'})
    self.parser.display_info.AddTransforms({'xfoo': 'xbar'})
    self.parser.parse_args([])
    self.assertEqual('yaml', self.parser.display_info.format)
    self.assertEqual('foo.bar=baz', self.parser.display_info.filter)
    self.assertEqual('bar', self.parser.display_info.aliases['foo'])
    self.assertEqual('xbar', self.parser.display_info.transforms['xfoo'])

  def testDisplayInfoMultipleAddPrecedence(self):
    self.parser.display_info.AddFormat('table(bot)')
    self.parser.display_info.AddFilter('thing=1')
    self.parser.display_info.AddAliases({'ALL': 'bot', 'BOT': 'Bot'})
    self.parser.display_info.AddTransforms({'XALL': 'xbot', 'XBOT': 'XBot'})
    self.parser.display_info.AddFormat('table(mid)')
    self.parser.display_info.AddFilter('thing=2')
    self.parser.display_info.AddAliases({'ALL': 'mid', 'MID': 'Mid'})
    self.parser.display_info.AddTransforms({'XALL': 'xmid', 'XMID': 'XMid'})
    self.parser.display_info.AddFormat('table(top)')
    self.parser.display_info.AddFilter('thing=3')
    self.parser.display_info.AddAliases({'ALL': 'top', 'TOP': 'Top'})
    self.parser.display_info.AddTransforms({'XALL': 'xtop', 'XTOP': 'XTop'})
    self.parser.parse_args([])
    self.assertEqual('table(top)', self.parser.display_info.format)
    self.assertEqual('thing=3', self.parser.display_info.filter)
    self.assertEqual('top', self.parser.display_info.aliases['ALL'])
    self.assertEqual('Bot', self.parser.display_info.aliases['BOT'])
    self.assertEqual('Mid', self.parser.display_info.aliases['MID'])
    self.assertEqual('Top', self.parser.display_info.aliases['TOP'])
    self.assertEqual('xtop', self.parser.display_info.transforms['XALL'])
    self.assertEqual('XBot', self.parser.display_info.transforms['XBOT'])
    self.assertEqual('XMid', self.parser.display_info.transforms['XMID'])
    self.assertEqual('XTop', self.parser.display_info.transforms['XTOP'])

  def testDisplayInfoAddUpdatePrecedence(self):
    self.parser.display_info.AddFormat('table(mid)')
    self.parser.display_info.AddFilter('thing=1')
    self.parser.display_info.AddAliases({'ALL': 'mid', 'MID': 'Mid'})
    self.parser.display_info.AddTransforms({'XALL': 'xmid', 'XMID': 'XMid'})
    di = display_info.DisplayInfo()
    di.AddFormat('table(bot)')
    di.AddFilter('thing=2')
    di.AddAliases({'ALL': 'bot', 'BOT': 'Bot'})
    di.AddTransforms({'XALL': 'xbot', 'XBOT': 'XBot'})
    self.parser.display_info.AddLowerDisplayInfo(di)
    self.parser.display_info.AddFormat('table(top)')
    self.parser.display_info.AddFilter('thing=3')
    self.parser.display_info.AddAliases({'ALL': 'top', 'TOP': 'Top'})
    self.parser.display_info.AddTransforms({'XALL': 'xtop', 'XTOP': 'XTop'})
    self.parser.parse_args([])
    self.assertEqual('table(top)', self.parser.display_info.format)
    self.assertEqual('thing=3', self.parser.display_info.filter)
    self.assertEqual('top', self.parser.display_info.aliases['ALL'])
    self.assertEqual('Bot', self.parser.display_info.aliases['BOT'])
    self.assertEqual('Mid', self.parser.display_info.aliases['MID'])
    self.assertEqual('Top', self.parser.display_info.aliases['TOP'])
    self.assertEqual('xtop', self.parser.display_info.transforms['XALL'])
    self.assertEqual('XBot', self.parser.display_info.transforms['XBOT'])
    self.assertEqual('XMid', self.parser.display_info.transforms['XMID'])
    self.assertEqual('XTop', self.parser.display_info.transforms['XTOP'])


class DurationTest(subtests.Base):
  """Unit tests for the Duration() parser."""

  def RunSubTest(self, duration, **kwargs):
    parser = arg_parsers.Duration(**kwargs)
    return parser(duration)

  def testDurationWithSimpleInput(self):
    self.Run(None, None)
    self.Run(100, '100')
    self.Run(0, '0s')
    self.Run(0, '0d')
    self.Run(1, '1s')
    self.Run(2, '2s')
    self.Run(6, '6000ms')
    self.Run(22, '22s')
    self.Run(60, '1m')
    self.Run(120, '2m')
    self.Run(600, '10m')
    self.Run(6000, '100m')
    self.Run(86400, '1d')
    self.Run(172800, '2d')

    self.Run(15778463, '0.5y')
    self.Run(1296000, 'p0.5m')
    self.Run(43200, '0.5d')
    ## Regression test for b/118404992.
    self.Run(216, '0.06h')
    self.Run(30, '0.5m')
    self.Run(0, '0.5s')

    self.Run(61, '1m1s')
    self.Run(61, '1s1m')
    self.Run(3601, '1h1s')
    self.Run(3601, '1s1h')

    self.Run(1, '1s', upper_bound='1s1h')
    self.Run(60, '1m', upper_bound='1h1s')
    self.Run(60, '1m', lower_bound='59s', upper_bound='1m1s')

  def testDurationWithParsedUnitInput(self):
    self.Run(100000, '100', parsed_unit='ms')
    self.Run(100, '100ms', parsed_unit='ms')
    self.Run(100000000, '100', parsed_unit='us')
    self.Run(100000, '100ms', parsed_unit='us')
    self.Run(0, '0s', parsed_unit='ms')
    self.Run(0, '0d', parsed_unit='us')
    self.Run(60000, '1m', parsed_unit='ms')
    self.Run(60000000, '1m', parsed_unit='us')

  def testMalformedInput(self):
    self.Run(None, '1x', exception=arg_parsers.ArgumentTypeError(
        "Failed to parse duration: Unknown character 'X' in duration"))
    self.Run(None, '1s', lower_bound='1x',
             exception=arg_parsers.ArgumentTypeError(
                 "Failed to parse duration: Unknown character 'X' in duration"))
    self.Run(None, '1s', upper_bound='1x',
             exception=arg_parsers.ArgumentTypeError(
                 "Failed to parse duration: Unknown character 'X' in duration"))
    self.Run(None, '1s', lower_bound='1s1h',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', lower_bound='1h1s',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1sec', exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', lower_bound='1sec',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', upper_bound='1sec',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1second', exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', lower_bound='1second',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', upper_bound='1second',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1 s', exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', lower_bound='1 s',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', upper_bound='1 s',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1   s', exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', lower_bound='1   s',
             exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '1s', upper_bound='1   s',
             exception=arg_parsers.ArgumentTypeError)

    self.Run(10, '10s', lower_bound='10s', upper_bound='1m')
    self.Run(11, '11s', lower_bound='10s', upper_bound='1m')
    self.Run(15, '15s', lower_bound='10s', upper_bound='1m')
    self.Run(60, '1m', lower_bound='10s', upper_bound='1m')
    self.Run(60, '60s', lower_bound='10s', upper_bound='1m')

    self.Run(None, '0d', lower_bound='10s', upper_bound='1m',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be greater than or equal to 10s; received: 0d'))
    self.Run(None, '1d', lower_bound='10s', upper_bound='1m',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 1m; received: 1d'))
    self.Run(None, '100d', lower_bound='10s', upper_bound='1m',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 1m; received: 100d'))
    self.Run(None, '9s', lower_bound='10s', upper_bound='1m',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be greater than or equal to 10s; received: 9s'))
    self.Run(None, '61s', lower_bound='10s', upper_bound='1m',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 1m; received: 61s'))
    self.Run(None, '2m', lower_bound='10s', upper_bound='1m',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 1m; received: 2m'))


class GetBinarySizePerUnit(subtests.Base):
  """Unit tests for the GetBinarySizePerUnit()."""

  def RunSubTest(self, suffix, **kwargs):
    return arg_parsers.GetBinarySizePerUnit(suffix, **kwargs)

  def testGetBinarySizePerUnit(self):
    self.Run(None, None, exception=ValueError)
    self.Run(1, 'B')
    self.Run(1, '')
    self.Run(1024, 'kb')
    self.Run(1024, 'kb/s', type_abbr='b/s')
    self.Run(1024, 'Kb/s', type_abbr='b/s')
    self.Run(1048576, 'm')
    self.Run(1073741824, 'GB')


class DiskSizeTest(subtests.Base):
  """Unit tests for the DiskSize() parser."""

  def RunSubTest(self, value, **kwargs):
    parser = arg_parsers.BinarySize(**kwargs)
    return parser(value)

  def testDiskSizeWithSimpleInput(self):
    self.Run(None, None)
    self.Run(1, '1B')
    self.Run(0, '0B')
    self.Run(0, '000B')

    self.Run(0, '0KB')
    self.Run(1024, '1KB')
    self.Run(25600, '25KB')
    self.Run(102400, '100KB')

    self.Run(0, '0KiB')
    self.Run(1024, '1KiB')
    self.Run(25600, '25KiB')
    self.Run(102400, '100KiB')

    self.Run(0, '0MB')
    self.Run(1048576, '1MB')
    self.Run(26214400, '25MB')
    self.Run(104857600, '100MB')

    self.Run(0, '0MiB')
    self.Run(1048576, '1MiB')
    self.Run(26214400, '25MiB')
    self.Run(104857600, '100MiB')

    self.Run(0, '0GB')
    self.Run(1073741824, '1GB')
    self.Run(26843545600, '25GB')
    self.Run(107374182400, '100GB')

    self.Run(0, '0GiB')
    self.Run(1073741824, '1GiB')
    self.Run(26843545600, '25GiB')
    self.Run(107374182400, '100GiB')

    self.Run(0, '0TB')
    self.Run(1099511627776, '1TB')
    self.Run(27487790694400, '25TB')
    self.Run(109951162777600, '100TB')

    self.Run(0, '0TiB')
    self.Run(1099511627776, '1TiB')
    self.Run(27487790694400, '25TiB')
    self.Run(109951162777600, '100TiB')

    self.Run(0, '0PB')
    self.Run(1125899906842624, '1PB')
    self.Run(28147497671065600, '25PB')
    self.Run(112589990684262400, '100PB')

    self.Run(0, '0PiB')
    self.Run(1125899906842624, '1PiB')
    self.Run(28147497671065600, '25PiB')
    self.Run(112589990684262400, '100PiB')

  def testTypeAbbr(self):
    self.Run(1, '1B')
    self.Run(1024, '1k')
    self.Run(1048576, '1Mi')

    self.Run(10240, '10', type_abbr='b/s', default_unit='Kb/s')
    self.Run(10240, '10', type_abbr='b/s', default_unit='Kbs')
    self.Run(10240, '10', type_abbr='b/s', default_unit='k')
    self.Run(20480, '20k', type_abbr='b/s', default_unit='k')
    self.Run(31457280, '30Mb', type_abbr='b/s', default_unit='k')
    self.Run(42949672960, '40Gbs', type_abbr='b/s', default_unit='k')
    self.Run(53687091200, '50Gib/', type_abbr='b/s', default_unit='k')
    self.Run(67553994410557440, '60Pb/s', type_abbr='b/s', default_unit='k')

  def testMalformedInput(self):
    self.Run(None, '1GB1KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1GB1KB'))
    self.Run(None, '1GB1KB', lower_bound='1GB1KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1GB1KB'))
    self.Run(None, '1GB1KB', upper_bound='1GB1KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1GB1KB'))
    self.Run(None, '1TB1KiB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1TB1KiB'))
    self.Run(None, '1TB1KiB', lower_bound='1TB1KiB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1TB1KiB'))
    self.Run(None, '1TB1KiB', upper_bound='1TB1KiB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1TB1KiB'))
    self.Run(None, '1kilobyte',
             exception=arg_parsers.ArgumentTypeError(
                 'unit must be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, '
                 'PB, PiB; received: kilobyte'))
    self.Run(None, '1kilobyte', lower_bound='1kilobyte',
             exception=arg_parsers.ArgumentTypeError(
                 'unit must be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, '
                 'PB, PiB; received: kilobyte'))
    self.Run(None, '1kilobyte', upper_bound='1kilobyte',
             exception=arg_parsers.ArgumentTypeError(
                 'unit must be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, '
                 'PB, PiB; received: kilobyte'))
    self.Run(None, '1 KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1 KB'))
    self.Run(None, '1 KB', lower_bound='1 KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1 KB'))
    self.Run(None, '1 KB', upper_bound='1 KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1 KB'))
    self.Run(None, '1   KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1   KB'))
    self.Run(None, '1   KB', lower_bound='1   KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1   KB'))
    self.Run(None, '1   KB', upper_bound='1   KB',
             exception=arg_parsers.ArgumentTypeError(
                 'given value must be of the form INTEGER[UNIT] where units '
                 'can be one of B, KB, KiB, MB, MiB, GB, GiB, TB, TiB, PB, '
                 'PiB; received: 1   KB'))

    self.Run(1073741824, '1GB', lower_bound='1GB', upper_bound='100GB')
    self.Run(1073741824, '1gb', lower_bound='1GB', upper_bound='100GB')
    self.Run(1073741824, '1GiB', lower_bound='1GB', upper_bound='100GB')
    self.Run(1073741824, '1gIb', lower_bound='1GB', upper_bound='100GB')
    self.Run(53687091200, '50GB', lower_bound='1GB', upper_bound='100GB')
    self.Run(59055800320, '55GiB', lower_bound='1GB', upper_bound='100GB')
    self.Run(107374182400, '100GB', lower_bound='1GB', upper_bound='100GB')
    self.Run(107374182400, '100GiB', lower_bound='1GB', upper_bound='100GB')

    self.Run(None, '0GB', lower_bound='1GB', upper_bound='100GB',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be greater than or equal to 1GB; received: 0GB'))
    self.Run(None, '1KiB', lower_bound='1GB', upper_bound='100GB',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be greater than or equal to 1GB; received: 1KiB'))
    self.Run(None, '100TiB', lower_bound='1GB', upper_bound='100GB',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 100GB; received: 100TiB'))
    self.Run(None, '1PB', lower_bound='1GB', upper_bound='100GB',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 100GB; received: 1PB'))
    self.Run(None, '100KB', lower_bound='1GB', upper_bound='100GB',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be greater than or equal to 1GB; received: 100KB'))
    self.Run(None, '101GB', lower_bound='1GB', upper_bound='100GB',
             exception=arg_parsers.ArgumentTypeError(
                 'value must be less than or equal to 100GB; received: 101GB'))


class RangeTests(test_case.TestCase):

  def testSingle(self):
    self.assertEqual(
        arg_parsers.Range(25, 25),
        arg_parsers.Range.Parse('25'))

  def testRange(self):

    self.assertEqual(
        arg_parsers.Range(25, 100),
        arg_parsers.Range.Parse('25-100'))

  def testSingleZero(self):
    self.assertEqual(
        arg_parsers.Range(0, 0),
        arg_parsers.Range.Parse('0'))

  def testSingleStr(self):
    self.assertEqual('25', six.text_type(arg_parsers.Range(25, 25)))

  def testRangeStr(self):
    self.assertEqual('25-100', six.text_type(arg_parsers.Range(25, 100)))

  def testSingleNegative(self):
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        r'Expected a non-negative integer value or a range of such values '
        r'instead of "-25"'):
      arg_parsers.Range.Parse('-25')

  def testBadString(self):
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        r'Expected a non-negative integer value or a range of such values '
        r'instead of "xyz"'):
      arg_parsers.Range.Parse('xyz')

  def testInvertedRange(self):
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        r'Expected range start 25 smaller or equal to range end 15 in "25-15"'):
      arg_parsers.Range.Parse('25-15')

  def testRangeCombine(self):
    self.assertEqual(
        arg_parsers.Range(25, 200),
        arg_parsers.Range(25, 100).Combine(arg_parsers.Range(50, 200)))
    self.assertEqual(
        arg_parsers.Range(25, 200),
        arg_parsers.Range(50, 200).Combine(arg_parsers.Range(25, 100)))
    self.assertEqual(
        arg_parsers.Range(25, 200),
        arg_parsers.Range(25, 100).Combine(arg_parsers.Range(101, 200)))
    with self.assertRaises(arg_parsers.Error):
      arg_parsers.Range(25, 100).Combine(arg_parsers.Range(102, 200))

  def testSort(self):
    self.assertEqual(
        [arg_parsers.Range(25, 100),
         arg_parsers.Range(50, 70),
         arg_parsers.Range(50, 71),
         arg_parsers.Range(101, 101)],
        sorted([
            arg_parsers.Range(101, 101),
            arg_parsers.Range(50, 71),
            arg_parsers.Range(25, 100),
            arg_parsers.Range(50, 70)]))


class HostPortTest(subtests.Base):
  """Unit tests for the host&port parser."""

  def RunSubTest(self, value, **kwargs):
    hp = arg_parsers.HostPort.Parse(value, **kwargs)
    return hp.host, hp.port

  def testHostPortParse(self):
    self.Run((None, None), '')
    self.Run((None, None), ':')
    self.Run(('localhost', None), 'localhost')
    self.Run((None, '8000'), ':8000')
    self.Run(('localhost', '8000'), 'localhost:8000')
    self.Run(('1.2.3.4', '567'), '1.2.3.4:567')
    self.Run(('1.2.3.4', None), '1.2.3.4')
    self.Run(('ουτοπία.δπθ.gr', None), 'ουτοπία.δπθ.gr')
    self.Run(('ουτοπία.δπθ.gr', '422'), 'ουτοπία.δπθ.gr:422')
    self.Run(('foo-bar.com', '8000'), 'foo-bar.com:8000')

    self.Run(None, '1:2:3',
             exception=arg_parsers.ArgumentTypeError(
                 'Failed to parse host and port. Expected format \n\n'
                 '  IPv4_ADDRESS_OR_HOSTNAME:PORT\n\n'
                 '(where :PORT is optional).; received: 1:2:3'))

    self.Run(('2001:db8::1', None), '[2001:db8::1]', ipv6_enabled=True)
    self.Run(('2001:db8::1', None), '[2001:db8::1]:', ipv6_enabled=True)
    self.Run(('2001:db8::1', '42'), '[2001:db8::1]:42', ipv6_enabled=True)

    self.Run(None, '1:2:3', ipv6_enabled=True,
             exception=arg_parsers.ArgumentTypeError(
                 'Failed to parse host and port. Expected format \n\n'
                 '  IPv4_ADDRESS_OR_HOSTNAME:PORT\n\nor\n\n'
                 '  [IPv6_ADDRESS]:PORT\n\n'
                 '(where :PORT is optional).; received: 1:2:3'))
    self.Run(None, '[2001:db8::1]123', ipv6_enabled=True,
             exception=arg_parsers.ArgumentTypeError(
                 'Failed to parse host and port. Expected format \n\n'
                 '  IPv4_ADDRESS_OR_HOSTNAME:PORT\n\nor\n\n'
                 '  [IPv6_ADDRESS]:PORT\n\n'
                 '(where :PORT is optional).; received: [2001:db8::1]123'))
    self.Run(None, '[2001:db8::1', ipv6_enabled=True,
             exception=arg_parsers.ArgumentTypeError(
                 'Failed to parse host and port. Expected format \n\n'
                 '  IPv4_ADDRESS_OR_HOSTNAME:PORT\n\nor\n\n'
                 '  [IPv6_ADDRESS]:PORT\n\n'
                 '(where :PORT is optional).; received: [2001:db8::1'))


class DayTest(sdk_test_base.SdkBase):

  def testParse(self):
    self.assertEqual(arg_parsers.Day.Parse(''), None)
    self.assertEqual(arg_parsers.Day.Parse('2000-01-02'),
                     datetime.date(2000, 0o1, 0o2))

    with self.assertRaises(arg_parsers.ArgumentTypeError):
      arg_parsers.Day.Parse('asdf')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      arg_parsers.Day.Parse('2000')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      arg_parsers.Day.Parse('2000-01-02-03')


class DatetimeFormatTest(subtests.Base):

  def RunSubTest(self, subject, fmt='%Y-%m-%dT%H:%M:%S.%6f'):
    return times.FormatDateTime(
        arg_parsers.Datetime.Parse(subject),
        fmt=fmt)

  def testParse(self):
    self.assertEqual(arg_parsers.Datetime.Parse(''), None)
    # ISO formats
    self.Run('2015-05-31T11:22:33.000000',
             '2015-05-31 11:22:33')
    self.Run('2015-05-31T11:22:33.000044',
             '2015-05-31 11:22:33.000044')
    self.Run('2015-05-31T11:22:33.000044',
             '2015-05-31 11:22:33.000044')
    # RFC3339 formats
    self.Run('2015-05-31T11:22:33.000000',
             '2015-05-31 11:22:33Z')
    self.Run('2015-05-31T11:22:33.000044',
             '2015-05-31 11:22:33.000044Z')
    # TZ formats
    self.Run('2015-05-31T11:22:33.000000-0700',
             '2015-05-31T11:22:33-0700',
             '%Y-%m-%dT%H:%M:%S.%6f%z')
    # Partial date/time
    self.Run('2015-05-31',
             '2015-05-31',
             '%Y-%m-%d')
    self.Run('2015-05-31T11:22:33',
             '2015-05-31T11:22:33',
             '%Y-%m-%dT%H:%M:%S')
    # Errors
    self.Run(None, 'hello', exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '2016-13-13', exception=arg_parsers.ArgumentTypeError)
    self.Run(None, '2016-11-33', exception=arg_parsers.ArgumentTypeError)


class DatetimeDateTimeTest(subtests.Base):

  def RunSubTest(self, subject):
    return arg_parsers.Datetime.Parse(subject)

  def testParse(self):
    # ISO formats
    self.Run(datetime.datetime(2015, 5, 31, 11, 22, 33, 0, times.LOCAL),
             '2015-05-31 11:22:33')
    self.Run(datetime.datetime(2015, 5, 31, 11, 22, 33, 44, times.LOCAL),
             '2015-05-31 11:22:33.000044')
    self.Run(datetime.datetime(2015, 5, 31, 11, 22, 33, 44, times.LOCAL),
             '2015-05-31T11:22:33.000044')
    # RFC3339 formats
    self.Run(datetime.datetime(2015, 5, 31, 11, 22, 33, 0, times.UTC),
             '2015-05-31 11:22:33Z')
    self.Run(datetime.datetime(2015, 5, 31, 11, 22, 33, 44, times.UTC),
             '2015-05-31 11:22:33.000044Z')
    # TZ formats
    self.Run(datetime.datetime(2015, 5, 31, 11, 22, 33, 0,
                               times.TzOffset(-7 * 60)),
             '2015-05-31T11:22:33-0700')
    # Partial date/time
    self.Run(datetime.datetime(2015, 0o5, 31, 0, 0, 0, 0, times.LOCAL),
             '2015-05-31')
    self.Run(datetime.datetime(2015, 0o5, 31, 11, 22, 33, 0, times.LOCAL),
             '2015-05-31T11:22:33')


class DayOfWeekTest(sdk_test_base.SdkBase):

  def testParse(self):
    self.assertEqual(arg_parsers.DayOfWeek.Parse(''), None)
    self.assertEqual(arg_parsers.DayOfWeek.Parse('SUN'), 'SUN')
    self.assertEqual(arg_parsers.DayOfWeek.Parse('mon'), 'MON')
    self.assertEqual(arg_parsers.DayOfWeek.Parse('Tue'), 'TUE')
    self.assertEqual(arg_parsers.DayOfWeek.Parse('Wednesday'), 'WED')

    with self.assertRaises(arg_parsers.ArgumentTypeError):
      arg_parsers.DayOfWeek.Parse('hello')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      arg_parsers.DayOfWeek.Parse('1')


class ArgDictTest(subtests.Base):

  def RunSubTest(self, value, **kwargs):
    return arg_parsers.ArgDict(**kwargs)(value)

  def testArgDict(self):
    self.Run({'x': 'y'}, 'x=y')
    self.Run({'x': 'y', 'z': 'w'}, 'x=y,z=w')
    self.Run({'x': 1, 'z': 2}, 'x=1,z=2', value_type=int)
    self.Run({'x': 1, 'z': 2}, 'x=1,z=2', value_type=int)
    self.Run({'x': 1, 'z': 'w'}, 'x=1,z=w', value_type=int,
             exception=arg_parsers.ArgumentTypeError('Invalid value [w]'))
    self.Run({1: 'one', 2: 'two'}, '1=one,2=two', key_type=int)
    self.Run({1: 'one', 'z': 'two'}, '1=one,z=two', key_type=int,
             exception=arg_parsers.ArgumentTypeError('Invalid key [z]'))

    # No name.
    self.Run(None, '=1', exception=arg_parsers.ArgumentTypeError)

    # No operator
    self.Run(None, 'x,y', exception=arg_parsers.ArgumentTypeError)

  def testArgDictOrdering(self):
    self.Run(collections.OrderedDict([('x', 'y')]), 'x=y')
    self.Run(collections.OrderedDict([('x', 'y'), ('a', 'b')]), 'x=y,a=b')
    self.Run(collections.OrderedDict([('a', 'b'), ('x', 'y')]), 'a=b,x=y')

  def testArgDictAltDelim(self):
    self.Run({'x': 'y', 'z': 'w'}, 'x=y,z=w')
    self.Run({'v': 'w,x', 'y': 'z'}, '^:^v=w,x:y=z')
    self.Run({'t\nu': 'v\nw'}, 't\nu=v\nw')
    self.Run({'bar': 'baz^baz', 'baz': 'bar,bar'},
             '^foo^bar=baz^bazfoobaz=bar,bar')

  def testArgDictSpec(self):
    self.Run({'x': 'y'}, 'x=y')
    self.Run({'x': 'y'}, 'x=y', spec={'x': str})
    self.Run({'x': 'y', 'z': 'w'}, 'x=y,z=w', spec={'x': str, 'z': str})
    self.Run({'x': 1, 'z': 2}, 'x=1,z=2', spec={'x': int, 'z': int})
    self.Run({'x': 1, 'z': None}, 'x=1,z', spec={'x': int, 'z': None},
             allow_key_only=True)

    self.Run(None, '=1', spec={'x': str},
             exception=arg_parsers.ArgumentTypeError('Invalid flag value [=1]'))
    self.Run(None, 'x=1,y', spec={'x': str, 'y': str},
             exception=arg_parsers.ArgumentTypeError(
                 'Bad syntax for dict arg: [y]. Please see `gcloud topic '
                 'flags-file` or `gcloud topic escaping` for information on '
                 'providing list or dictionary flag values with special '
                 'characters.'))
    self.Run(None, 'x=1,z=2', spec={'x': int, 'z': None},
             allow_key_only=True,
             exception=arg_parsers.ArgumentTypeError(
                 'Key [z] does not take a value'))
    self.Run(None, 'x=1,z,q=42', spec={'x': int, 'z': None},
             allow_key_only=True,
             exception=arg_parsers.ArgumentTypeError(
                 'valid keys are [x, z]; received: q'))
    self.Run(None, 'x=1,z', spec={'x': int, 'z': None},
             allow_key_only=False,
             exception=arg_parsers.ArgumentTypeError(
                 'Bad syntax for dict arg: [z]. Please see `gcloud topic '
                 'flags-file` or `gcloud topic escaping` for information on '
                 'providing list or dictionary flag values with special '
                 'characters.'))
    self.Run(None, 'x=1,z=a', spec={'x': int, 'z': None},
             allow_key_only=False,
             exception=arg_parsers.ArgumentTypeError(
                 'Key [z] does not take a value'))

  def testArgDictRequiredKeys(self):
    self.Run({'x': 'y'}, 'x=y', required_keys=['x'])
    self.Run(None, 'x=y', required_keys=['x', 'z'],
             exception=arg_parsers.ArgumentTypeError(
                 'Key [z] required in dict arg but not provided'))

  def testArgDictOperators(self):
    operators = {
        '=': None,
        ':': lambda x: int(x) if x.isdigit() else x,
    }

    # Valid input.
    self.Run({'x': '1', 'y': 'z'}, 'x=1,y=z', operators=operators)
    self.Run({'x': '1', 'y': 'z'}, 'x=1,y:z', operators=operators)
    self.Run({'x': 1, 'y': 'z'}, 'x:1,y=z', operators=operators)
    self.Run({'x': 1, 'y': 'z'}, 'x:1,y:z', operators=operators)

    # No operator.
    self.Run(None, 'x@1,y:z', operators=operators,
             exception=arg_parsers.ArgumentTypeError)

  def testArgDictOperatorsInvalid(self):
    operators = {
        '=': None,
        '::': lambda x: int(x) if x.isdigit() else x,
    }
    self.Run(None, None, operators=operators,
             exception=arg_parsers.ArgumentTypeError(
                 'Operator [::] must be one character.'))


class ArgDictSpecUsageTest(subtests.Base):

  def RunSubTest(self, **kwargs):
    return arg_parsers.ArgDict(**kwargs).GetUsageMsg(False, 'AFLAG')

  def testArgDictSpecUsage(self):
    self.Run('[x=X]', spec={'x': str})
    self.Run('[x=X],[z=Z]', spec={'x': str, 'z': str})
    self.Run('[x=X],[z=Z]', spec={'x': int, 'z': int})
    self.Run('[z],[x=X]', spec={'x': int, 'z': None},
             exception=arg_parsers.ArgumentTypeError(
                 'Key [z] specified in spec without a function but '
                 'allow_key_only is set to False'))


class ArgListTest(subtests.Base):

  def RunSubTest(self, value, **kwargs):
    return arg_parsers.ArgList(**kwargs)(value)

  def testArgList(self):
    self.Run([], '')
    self.Run(['x'], 'x')
    self.Run(['x', 'y'], 'x,y')
    self.Run([1, 2], '1,2', element_type=int)
    self.Run([1, 2], '1, 2', element_type=int)  # yeah, python.
    self.Run(['x', 'y'], 'x,y', min_length=1, max_length=2)
    self.Run(None, 'x,y,z', min_length=1, max_length=2,
             exception=arg_parsers.ArgumentTypeError('too many args'))
    self.Run(None, 'x', min_length=2,
             exception=arg_parsers.ArgumentTypeError('not enough args'))

    # Alternate delimiters.
    self.Run(['a', 'b', 'c'], '^,^a,b,c')
    self.Run(['^a', 'b', 'c'], '^,^^a,b,c')
    self.Run(['^a', 'b', 'c'], '^a,b,c')
    self.Run(['a,', ',c'], '^b^a,b,c')
    self.Run(['foo', 'baz'], '^bar^foobarbaz')
    self.Run([], '^foo^')
    self.Run(None, '^^',
             exception=arg_parsers.ArgumentTypeError(
                 'Invalid delimeter. Please see `gcloud topic flags-file` or '
                 '`gcloud topic escaping` for information on providing list or '
                 'dictionary flag values with special characters.'))
    self.Run(None, '^^foo',
             exception=arg_parsers.ArgumentTypeError(
                 'Invalid delimeter. Please see `gcloud topic flags-file` or '
                 '`gcloud topic escaping` for information on providing list or '
                 'dictionary flag values with special characters.'))

    # Custom delimiters.
    self.Run(['foo;baz'], 'foo;baz', custom_delim_char=None)
    self.Run(['foo', 'baz'], 'foo;baz', custom_delim_char=';')


# We need to break this out separately because parameterized and subtests don't
# work well together.
class ArgListParameterizedTest(parameterized.TestCase):

  @parameterized.parameters(
      # Standard case
      (0, None, '[FOO,...]'),
      # Just a min length
      (1, None, 'FOO,[FOO,...]'),
      (2, None, 'FOO,FOO,[FOO,...]'),
      (3, None, 'FOO,FOO,FOO,[FOO,...]'),
      # Just a max length
      (0, 1, '[FOO]'),
      (0, 2, '[FOO,[FOO]]'),
      (0, 3, '[FOO,...]'),
      # Both a min and max length
      (1, 3, 'FOO,[FOO,[FOO]]'),
      (1, 4, 'FOO,[FOO,...]'),
      (2, 3, 'FOO,FOO,[FOO]'),
      (3, 3, 'FOO,FOO,FOO'),
  )
  def testArgListUsage(self, min_length, max_length, expected):
    arg_list = arg_parsers.ArgList(min_length=min_length, max_length=max_length)
    self.assertEqual(arg_list.GetUsageMsg(False, 'FOO'), expected)

  @parameterized.parameters(
      (0, None, '[REALLY_REALLY_LONG_METAVAR,...]'),
      (1, None, 'REALLY_REALLY_LONG_METAVAR,[...]'),
      (2, None, 'REALLY_REALLY_LONG_METAVAR,...,[...]'),
      (3, None, 'REALLY_REALLY_LONG_METAVAR,...,[...]'),
      (0, 3, '[REALLY_REALLY_LONG_METAVAR,...]'),
      (1, 3, 'REALLY_REALLY_LONG_METAVAR,[...]'),
      (2, 3, 'REALLY_REALLY_LONG_METAVAR,...,[...]'),
      (3, 3, 'REALLY_REALLY_LONG_METAVAR,...,[...]'),
  )
  def testArgListUsage_LongMetavar(self, min_length, max_length, expected):
    arg_list = arg_parsers.ArgList(min_length=min_length, max_length=max_length)
    self.assertEqual(arg_list.GetUsageMsg(False, 'REALLY_REALLY_LONG_METAVAR'),
                     expected)


class ArgListDefaultDelimiterTest(parameterized.TestCase):

  class _AtDelimitedArgList(arg_parsers.ArgList):
    DEFAULT_DELIM_CHAR = '@'

  @parameterized.parameters(
      # Standard case
      (0, None, None, '[FOO@...]'),
      # Just a min length
      (1, None, None, 'FOO@[FOO@...]'),
      (2, None, None, 'FOO@FOO@[FOO@...]'),
      (3, None, None, 'FOO@FOO@FOO@[FOO@...]'),
      # Just a max length
      (0, 1, None, '[FOO]'),
      (0, 2, None, '[FOO@[FOO]]'),
      (0, 3, None, '[FOO@...]'),
      # Both a min and max length
      (1, 3, None, 'FOO@[FOO@[FOO]]'),
      (1, 4, None, 'FOO@[FOO@...]'),
      (2, 3, None, 'FOO@FOO@[FOO]'),
      (3, 3, None, 'FOO@FOO@FOO'),
      # Custom delimiter char
      (0, None, ';', '[FOO;...]'),
      (2, 3, ';', 'FOO;FOO;[FOO]'),
  )
  def testArgListUsage(self, min_length, max_length,
                       custom_delim_char, expected):
    arg_list = self._AtDelimitedArgList(
        min_length=min_length, max_length=max_length,
        custom_delim_char=custom_delim_char)
    self.assertEqual(arg_list.GetUsageMsg(False, 'FOO'), expected)

  @parameterized.parameters(
      (0, None, '[REALLY_REALLY_LONG_METAVAR@...]'),
      (1, None, 'REALLY_REALLY_LONG_METAVAR@[...]'),
      (2, None, 'REALLY_REALLY_LONG_METAVAR@...@[...]'),
      (3, None, 'REALLY_REALLY_LONG_METAVAR@...@[...]'),
      (0, 3, '[REALLY_REALLY_LONG_METAVAR@...]'),
      (1, 3, 'REALLY_REALLY_LONG_METAVAR@[...]'),
      (2, 3, 'REALLY_REALLY_LONG_METAVAR@...@[...]'),
      (3, 3, 'REALLY_REALLY_LONG_METAVAR@...@[...]'),
  )
  def testArgListUsage_LongMetavar(self, min_length, max_length, expected):
    arg_list = self._AtDelimitedArgList(
        min_length=min_length, max_length=max_length)
    self.assertEqual(
        arg_list.GetUsageMsg(False, 'REALLY_REALLY_LONG_METAVAR'), expected)


class ArgListTokenizeTest(subtests.Base):

  def RunSubTest(self, value, **kwargs):
    return arg_parsers._TokenizeQuotedList(value, **kwargs)

  def testArgList(self):
    self.Run([], '')
    self.Run(['x'], 'x')
    self.Run(['x', 'y', 'z'], 'x,y,z')
    self.Run(['x'], 'x,')
    self.Run(['x', '', 'y'], 'x,,y')
    self.Run([''], ',')

    # Alternate delimiter.
    self.Run(['x', 'y', 'z'], 'x,y,z', delim=',')
    self.Run(['x', 'y', 'z'], 'x,y,z,', delim=',')
    self.Run(['x,y,z,'], 'x,y,z,', delim=':')
    self.Run(['v^w,x', 'y', 'z'], 'v^w,x:y:z:', delim=':')
    self.Run(['u,v^w:x', 'y', 'z'], 'u,v^w:xFOOyFOOz', delim='FOO')
    self.Run(['u,v^w:x', 'y', 'z'], 'u,v^w:xFOOyFOOzFOO', delim='FOO')


class ArgCommandsTest(util.WithTestTool,
                      cli_test_base.CliTestBase,
                      sdk_test_base.WithOutputCapture):

  def testList(self):
    self.cli.Execute(['dict-list', '--list=1,2,3'])
    self.AssertOutputContains("list: ['1', '2', '3']")

  def testListNoEquals(self):
    self.cli.Execute(['dict-list', '--list', '1,2,3'])
    self.AssertOutputContains("list: ['1', '2', '3']")

  def testRepeatedList(self):
    self.cli.Execute(['dict-list', '--repeated-list=a,b,c'])
    self.AssertOutputContains("list: [['a', 'b', 'c']]")
    self.cli.Execute(
        ['dict-list', '--repeated-list=1,2,3', '--repeated-list=a,b,c'])
    self.AssertOutputContains("list: [['1', '2', '3'], ['a', 'b', 'c']]")

  def testDict(self):
    self.cli.Execute(['dict-list', '--dict=1=2'])
    self.AssertOutputContains("dict: {'1': '2'}")

  def testDictNoEquals(self):
    self.cli.Execute(['dict-list', '--dict', '1=2'])
    self.AssertOutputContains("dict: {'1': '2'}")

  def testRepeatedDict(self):
    self.cli.Execute(['dict-list', '--repeated-dict=1=2'])
    self.AssertOutputContains("dict: [{'1': '2'}]")
    self.cli.Execute(
        ['dict-list', '--repeated-dict=a=b', '--repeated-dict=1=2'])
    self.AssertOutputContains("dict: [{'a': 'b'}, {'1': '2'}]")

  def testIntList(self):
    self.cli.Execute(['dict-list', '--int-list', '1,2'])
    self.AssertOutputContains('int-list: [1, 2]')

  def testChoiceListError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --choice-list: x must be one of [a, b, c]'):
      self.cli.Execute(['dict-list', '--choice-list', 'x,y,z'])

  def testChoiceList(self):
    self.cli.Execute(['dict-list', '--choice-list', 'a,b'])
    self.AssertOutputContains("choice-list: ['a', 'b']")

  def testArgListEmpty(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --list: expected one argument'):
      self.cli.Execute(['dict-list', '--list'])

    # Command should not have run.
    self.AssertOutputNotContains('list: []')

  def testArgListUpdateAction(self):
    self.cli.Execute(['dict-list',
                      '--repeated-list-update', 'v1'])
    self.AssertOutputContains("repeated-list-update: ['v1']")
    self.cli.Execute(['dict-list',
                      '--repeated-list-update', 'v1,v2',
                      '--repeated-list-update', 'v3,v4'])
    self.AssertOutputContains(
        "repeated-list-update: ['v1', 'v2', 'v3', 'v4']")

  def testArgListUpdateActionDuplicateException(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --repeated-list-update: "v2" cannot be specified multiple '
        'times'):
      self.cli.Execute(['dict-list',
                        '--repeated-list-update', 'v1,v2',
                        '--repeated-list-update', 'v2,v3'])

  def testArgListUpdateActionDuplicateOkay(self):
    self.cli.Execute(['dict-list',
                      '--repeated-list-update-with-append', 'v1,v2',
                      '--repeated-list-update-with-append', 'v2,v3'])
    self.AssertOutputContains(
        "repeated-list-update-with-append: ['v1', 'v2', 'v3']")

  def testArgDictUpdateAction(self):
    self.cli.Execute(['dict-list',
                      '--repeated-dict-update', 'key=value'])
    self.AssertOutputContains("repeated-dict-update: {'key': 'value'}")
    self.cli.Execute(['dict-list',
                      '--repeated-dict-update', 'key1=value1',
                      '--repeated-dict-update', 'key2=value2'])
    self.AssertOutputContains(
        "repeated-dict-update: {'key1': 'value1', 'key2': 'value2'}")

  def testArgDictUpdateActionOrdering(self):
    self.cli.Execute(['dict-list',
                      '--repeated-dict-update', 'key=value'])
    self.AssertOutputContains("repeated-dict-update: {'key': 'value'}")
    self.cli.Execute(['dict-list',
                      '--repeated-dict-update', 'key1=value1',
                      '--repeated-dict-update', 'key2=value2'])
    self.AssertOutputContains(
        "repeated-dict-update: {'key1': 'value1', 'key2': 'value2'}")
    self.cli.Execute(['dict-list',
                      '--repeated-dict-update', 'key2=value2',
                      '--repeated-dict-update', 'key1=value1'])
    self.AssertOutputContains(
        "repeated-dict-update: {'key2': 'value2', 'key1': 'value1'}")

  def testArgDictUpdateActionDuplicateException(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --repeated-dict-update: "key" cannot be specified multiple '
        'times; received: value1, value2'):
      self.cli.Execute(['dict-list',
                        '--repeated-dict-update', 'key=value1',
                        '--repeated-dict-update', 'key=value2'])

  def testArgDictUpdateActionDuplicateOkay(self):
    self.cli.Execute(['dict-list',
                      '--repeated-dict-update-with-append', 'key=value1',
                      '--repeated-dict-update-with-append', 'key=value2'])
    self.AssertOutputContains(
        "repeated-dict-update-with-append: {'key': ['value1', 'value2']}")

  def testImplementationArgsPositionalEmpty(self):
    result = self.cli.Execute(['implementation-args', 'positional'])
    self.assertEqual(None, result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsFlagPositionalEmpty(self):
    result = self.cli.Execute(['implementation-args', '--flag', 'positional'])
    self.assertEqual(None, result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalFlagEmpty(self):
    result = self.cli.Execute(['implementation-args', 'positional', '--flag'])
    self.assertEqual(None, result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalDashDash(self):
    result = self.cli.Execute(['implementation-args', 'positional', '--'])
    self.assertEqual([], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsFlagPositionalDashDash(self):
    result = self.cli.Execute(
        ['implementation-args', '--flag', 'positional', '--'])
    self.assertEqual([], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalFlagDashDash(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--'])
    self.assertEqual([], result)  # Explicit empty REMAINDER args
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsFlagPositionalOperand(self):
    result = self.cli.Execute(
        ['implementation-args', '--flag', 'positional', '--', 'operand'])
    self.assertEqual(['operand'], result)

  def testImplementationArgsPositionalFlagOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--', 'operand'])
    self.assertEqual(['operand'], result)

  def testImplementationArgsPositionalDashDashOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--', 'operand'])
    self.assertEqual(['operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsFlagPositionalDashDashOperand(self):
    result = self.cli.Execute(
        ['implementation-args', '--flag', 'positional', '--', 'operand'])
    self.assertEqual(['operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalFlagDashDashOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--', 'operand'])
    self.assertEqual(['operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalDashDashOptionOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--', '--v', 'operand'])
    self.assertEqual(['--v', 'operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsFlagPositionalDashDashOptionOperand(self):
    result = self.cli.Execute(
        ['implementation-args', '--flag', 'positional', '--', '--v', 'operand'])
    self.assertEqual(['--v', 'operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalFlagDashDashOptionOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--', '--v', 'operand'])
    self.assertEqual(['--v', 'operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalDashDashOptionDashDashOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--', '--v', '--', 'operand'])
    self.assertEqual(['--v', '--', 'operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsFlagPositionalDashDashOptionDashDashOperand(self):
    result = self.cli.Execute(
        ['implementation-args', '--flag', 'positional', '--', '--v', '--',
         'operand'])
    self.assertEqual(['--v', '--', 'operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalFlagDashDashOptionDashDashOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--', '--v', '--',
         'operand'])
    self.assertEqual(['--v', '--', 'operand'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalFlagOptionOperand(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--', '--unknown-flag',
         'operand'])
    self.assertEqual(['--unknown-flag', 'operand'], result)

  def testImplementationArgsPositionalFlagOperandOption(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--flag', '--', 'operand',
         '--unknown-flag'])
    self.assertEqual(['operand', '--unknown-flag'], result)

  def testImplementationArgsPositionalDashDashDashDash(self):
    result = self.cli.Execute(['implementation-args', 'positional', '--', '--'])
    self.assertEqual(['--'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsPositionalDashDashOperandDashDash(self):
    result = self.cli.Execute(
        ['implementation-args', 'positional', '--', 'operand', '--'])
    self.assertEqual(['operand', '--'], result)
    self.AssertErrNotContains('WARNING')

  def testImplementationArgsSwallowsPositionals(self):
    result = self.cli.Execute(
        ['implementation-args', '--flag', 'positional', '--',
         'unknown-positional', '--unknown-flag'])
    self.assertEqual(['unknown-positional', '--unknown-flag'], result)

  def testImplementationArgsTypo(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments:\n  --vrbosity (did you mean '--verbosity'?)"
        "\n  positional"):
      self.cli.Execute(
          ['implementation-args', '--vrbosity', 'debug', 'positional', '--flag',
           '--', 'unknown-positional', '--unknown-flag'])
    self.AssertErrContains("--vrbosity (did you mean '--verbosity'?)")

  def testImplementationArgsPositionalEmptyStrict(self):
    result = self.cli.Execute(['beta', 'implementation-args', 'positional'])
    self.assertEqual(None, result)

  def testImplementationArgsFlagPositionalEmptyStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', '--flag', 'positional'])
    self.assertEqual(None, result)

  def testImplementationArgsPositionalFlagEmptyStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--flag'])
    self.assertEqual(None, result)

  def testImplementationArgsPositionalDashDashStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--'])
    self.assertEqual([], result)  # Explicit empty REMAINDER args

  def testImplementationArgsFlagPositionalDashDashStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', '--flag', 'positional', '--'])
    self.assertEqual([], result)  # Explicit empty REMAINDER args

  def testImplementationArgsPositionalFlagDashDashStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--flag', '--'])
    self.assertEqual([], result)  # Explicit empty REMAINDER args

  def testImplementationArgsPositionalOperandStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: operand'):
      self.cli.Execute(
          ['beta', 'implementation-args', 'positional', 'operand'])

  def testImplementationArgsFlagPositionalOperandStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: operand'):
      self.cli.Execute(
          ['beta', 'implementation-args', '--flag', 'positional', 'operand'])

  def testImplementationArgsPositionalFlagOperandStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: operand'):
      self.cli.Execute(
          ['beta', 'implementation-args', 'positional', '--flag', 'operand'])

  def testImplementationArgsPositionalDashDashOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--', 'operand'])
    self.assertEqual(['operand'], result)

  def testImplementationArgsFlagPositionalDashDashOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', '--flag', 'positional', '--',
         'operand'])
    self.assertEqual(['operand'], result)

  def testImplementationArgsPositionalFlagDashDashOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--flag', '--',
         'operand'])
    self.assertEqual(['operand'], result)

  def testImplementationArgsPositionalDashDashOptionOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--', '--v', 'operand'])
    self.assertEqual(['--v', 'operand'], result)

  def testImplementationArgsFlagPositionalDashDashOptionOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', '--flag', 'positional', '--', '--v',
         'operand'])
    self.assertEqual(['--v', 'operand'], result)

  def testImplementationArgsPositionalFlagDashDashOptionOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--flag', '--', '--v',
         'operand'])
    self.assertEqual(['--v', 'operand'], result)

  def testImplementationArgsPositionalFlagBeforeFlagAfter(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--flag', '--', '--v',
         '--flag', 'operand'])
    self.assertEqual(['--v', '--flag', 'operand'], result)

  def testImplementationArgsPositionalDashDashOptionDashDashOperandStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--', '--v', '--',
         'operand'])
    self.assertEqual(['--v', '--', 'operand'], result)

  def testImplementationArgsFlagPositionalDashDashOptionDashDashOperandStrict(
      self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', '--flag', 'positional', '--', '--v',
         '--', 'operand'])
    self.assertEqual(['--v', '--', 'operand'], result)

  def testImplementationArgsPositionalFlagDashDashOptionDashDashOperandStrict(
      self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--flag', '--', '--v',
         '--', 'operand'])
    self.assertEqual(['--v', '--', 'operand'], result)

  def testImplementationArgsPositionalFlagOptionOperandStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments:\n  --unknown-flag (did you mean '--no-flag'?)"
        "\n  operand"):
      self.cli.Execute(
          ['beta', 'implementation-args', 'positional', '--flag',
           '--unknown-flag', 'operand'])

  def testImplementationArgsPositionalFlagOperandOptionStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments:\n  operand\n  --unknown-flag (did you mean "
        "'--no-flag'?)"):
      self.cli.Execute(
          ['beta', 'implementation-args', 'positional', '--flag', 'operand',
           '--unknown-flag'])

  def testImplementationArgsPositionalDashDashDashDashStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--', '--'])
    self.assertEqual(['--'], result)

  def testImplementationArgsPositionalDashDashOperandDashDashStrict(self):
    result = self.cli.Execute(
        ['beta', 'implementation-args', 'positional', '--', 'operand', '--'])
    self.assertEqual(['operand', '--'], result)

  def testImplementationArgsNoDashDashStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --unknown-flag (did you mean '--no-flag'?)"):
      self.cli.Execute(
          ['beta', 'implementation-args', 'positional', '--flag',
           '--unknown-flag'])

  def testImplementationArgsSwallowsPositionalsStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments:\n  unknown-positional\n  --unknown-flag "
        "(did you mean '--no-flag'?)"):
      self.cli.Execute(
          ['beta', 'implementation-args', '--flag', 'positional',
           'unknown-positional', '--unknown-flag'])

  def testImplementationArgsTypoStrict(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments:\n  --vrbosity (did you mean '--verbosity'?)"
        "\n  positional\n  unknown-positional\n  --unknown-flag "
        "(did you mean '--no-flag'?)"):
      self.cli.Execute([
          'beta', 'implementation-args', '--vrbosity', 'debug',
          'positional', '--flag', 'unknown-positional',
          '--unknown-flag'])

  def testRemainderWithFlags(self):
    result = self.cli.Execute(
        ['sdk2', 'remainder-with-flags', '--foo', 'bar', 'positional'])
    self.assertEqual(None, result)
    self.AssertErrNotContains('WARNING')

  def testRemainderWithFlagsOrdering(self):
    result = self.cli.Execute(
        ['sdk2', 'remainder-with-flags', 'positional', '--foo', 'bar'])
    self.assertEqual(None, result)
    self.AssertErrNotContains('WARNING')

  def testRemainderWithFlagsRemainder(self):
    result = self.cli.Execute(
        ['sdk2', 'remainder-with-flags', '--foo', 'bar', 'positional',
         '--', 'some', '--other', 'stuff'])
    self.assertEqual(['some', '--other', 'stuff'], result)

  def testRemainderWithFlagsDashDashRemainder(self):
    result = self.cli.Execute(
        ['sdk2', 'remainder-with-flags', '--foo', 'bar', 'positional', '--',
         'some', '--other', 'stuff'])
    self.assertEqual(['some', '--other', 'stuff'], result)
    self.AssertErrNotContains('WARNING')

  def testRemainderWithFlagsRemainderDashDashRemainder(self):
    result = self.cli.Execute(
        ['sdk2', 'remainder-with-flags', '--foo', 'bar', 'positional',
         '--', 'some', '--', '--other', 'stuff'])
    self.assertEqual(['some', '--', '--other', 'stuff'], result)

  def testRemainderActionDetailedHelp(self):
    action = arg_parsers.RemainderAction(
        option_strings=None, dest='remainder', metavar='REMAINDER',
        nargs=argparse.REMAINDER, help='Stuff to pass through.',
        example='command foo --bar -- stuff --after dashes')
    expected = (
        'Stuff to pass through.\n+\n{deprecation_msg} '
        'Example:\n\ncommand foo --bar -- stuff --after dashes'
    ).format(deprecation_msg=StrictDeprecationMessage('REMAINDER'))

    self.assertEqual(expected, action.help)

  def testRemainderActionParseKnownArgs(self):
    action = arg_parsers.RemainderAction(
        option_strings=None, dest='remainder', metavar='REMAINDER',
        nargs=argparse.REMAINDER)
    namespace = argparse.Namespace()
    args = ['foo', '--bar', 'Ṳᾔḯ¢◎ⅾℯ', '--', 'stuff', '--after', 'dashes']
    namespace, args = action.ParseKnownArgs(args, namespace)
    self.assertEqual(namespace.remainder, ['stuff', '--after', 'dashes'])
    self.assertEqual(args, ['foo', '--bar', 'Ṳᾔḯ¢◎ⅾℯ'])
    self.AssertErrNotContains('WARNING')

  def testRemainderActionParseRemainingArgs(self):
    action = arg_parsers.RemainderAction(
        option_strings=None, dest='remainder', metavar='REMAINDER',
        nargs=argparse.REMAINDER)
    remaining_args = ['foo', '--bar', 'baz']
    args_after_dash = ['what', 'came', '--after', 'the', 'dash']
    original_args = [
        'foo', '--verbosity', 'debug', '--bar', 'baz', '--', 'what', 'came',
        '--after', 'the', 'dash']
    namespace = argparse.Namespace(remainder=args_after_dash)
    with self.AssertRaisesExceptionMatches(
        Exception,
        "unrecognized args: --bar baz\nThe '--' "
        'argument must be specified between gcloud specific args on the left '
        'and REMAINDER on the right.'):
      action.ParseRemainingArgs(remaining_args, namespace, original_args)

  def testRemainderActionParseRemainingArgsUnicode(self):
    action = arg_parsers.RemainderAction(
        option_strings=None, dest='remainder', metavar='REMAINDER',
        nargs=argparse.REMAINDER)
    remaining_args = ['foo', 'Ṳᾔḯ¢◎ⅾℯ']
    args_after_dash = ['what', 'came', '--after', 'the', 'dash', 'Ṳᾔḯ¢◎ⅾℯ']
    original_args = [
        'foo', '--verbosity', 'debug', 'Ṳᾔḯ¢◎ⅾℯ' '--',
        'what', 'came', '--after', 'the', 'dash', 'Ṳᾔḯ¢◎ⅾℯ']
    namespace = argparse.Namespace(remainder=args_after_dash)
    try:
      action.ParseRemainingArgs(remaining_args, namespace, original_args)
    except argparse.ArgumentError as e:
      # Sorry, self.assertRaisesRegex doesn't handle unicode :(
      # It uses str(e) instead of unicode(e)
      expected = (
          'unrecognized args: Ṳᾔḯ¢◎ⅾℯ\n'
          "The '--' argument must be specified between gcloud specific args "
          'on the left and REMAINDER on the right.')
      self.assertEqual(expected, six.text_type(e))
    else:
      self.fail('Should have raised an argparse.ArgumentError exception.')

  def testStoreOnceCorrect(self):
    self.cli.Execute(['dict-list', '--store-once', 'a=1,b=2,c=3'])
    self.AssertOutputContains("store-once: {'a': '1', 'b': '2', 'c': '3'}")

  def testStoreOnceIncorrect(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --store-once: "store_once" argument cannot be specified '
        'multiple times'):
      self.cli.Execute(['dict-list',
                        '--store-once', 'a=1,b=2,c=3',
                        '--store-once', 'd=1'])

  def testIntArgError(self):
    with self.AssertRaisesArgumentErrorMatches(
        "--number-with-choices: Invalid choice: '5'."):
      self.cli.Execute(['sdk11', 'sdk', 'optional-flags',
                        '--number-with-choices=5'])
    self.AssertErrContains('--number-with-choices: Invalid choice: \'5\'.')

  def testUnicodeArgError(self):
    with self.AssertRaisesArgumentError():
      self.cli.Execute(['sdk11', 'sdk', 'optional-flags', '--pirates=1234'])
    self.AssertErrContains('--pirates: Invalid choice: \'\\u26201234\'.')

  def testUnicodeArg(self):
    self.cli.Execute(['sdk11', 'sdk', 'optional-flags', '--pirates=123'])


def SimpleCompleter(prefix, unused_parsed_args, **unused_kwargs):
  choices = ['foot', 'shoe', 'foobar', 'shield', 'first']
  return [choice for choice in choices if choice.startswith(prefix)]


class HandleNoArgActionTest(util.WithTestTool, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    group = self.parser.add_argument_group(mutex=True)
    group.add_argument('--no-foo', action='store_true', help='Auxilio aliis.')
    group.add_argument(
        '--foo',
        nargs='?',
        action=arg_parsers.HandleNoArgAction('no_foo', 'this is deprecated'),
        help='Auxilio aliis.')

  def testNoFlags(self):
    ns = self.parser.parse_args([])
    self.assertEqual(ns.foo, None)
    self.assertEqual(ns.no_foo, False)
    self.AssertErrNotContains('this is deprecated')

  def testNoArg(self):
    ns = self.parser.parse_args(['--foo'])
    self.assertEqual(ns.foo, None)
    self.assertEqual(ns.no_foo, True)
    self.AssertErrContains('this is deprecated')

  def testEmptyString(self):
    ns = self.parser.parse_args(['--foo='])
    self.assertEqual(ns.foo, '')
    self.assertEqual(ns.no_foo, False)
    self.AssertErrNotContains('this is deprecated')

  def testRealArgument(self):
    ns = self.parser.parse_args(['--foo=bar'])
    self.assertEqual(ns.foo, 'bar')
    self.assertEqual(ns.no_foo, False)
    self.AssertErrNotContains('this is deprecated')


class DeprecationActionTest(util.WithTestTool, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.warning = 'Custom Test Warning.'

  def testInvertedFlag(self):
    self.parser.add_argument(
        '--bool-flag',
        action=actions.DeprecationAction(
            'bool-flag',
            warn=self.warning,
            action='store_true'),
        help='Auxilio aliis.')
    args = self.parser.parse_args(['--no-bool-flag'])
    self.AssertErrContains(self.warning)
    self.assertEqual(args.bool_flag, False)

  def testFlag(self):
    self.parser.add_argument(
        '--bool-flag',
        action=actions.DeprecationAction(
            'bool-flag',
            warn=self.warning,
            action='store_true'),
        help='Auxilio aliis.')
    args = self.parser.parse_args(['--bool-flag'])
    self.AssertErrContains(self.warning)
    self.assertEqual(args.bool_flag, True)

  def testInvertedUsingArgParseActionFlag(self):
    store_true_cls = actions.GetArgparseBuiltInAction('store_true')
    self.parser.add_argument(
        '--bool-flag',
        action=actions.DeprecationAction(
            'bool-flag',
            warn=self.warning,
            action=store_true_cls),
        help='Auxilio aliis.')
    args = self.parser.parse_args(['--no-bool-flag'])
    self.AssertErrContains(self.warning)
    self.assertEqual(args.bool_flag, False)

  def testUsingArgParseActionFlag(self):
    store_true_cls = actions.GetArgparseBuiltInAction('store_true')
    self.parser.add_argument(
        '--bool-flag',
        action=actions.DeprecationAction(
            'bool-flag',
            warn=self.warning,
            action=store_true_cls),
        help='Auxilio aliis.')
    args = self.parser.parse_args(['--bool-flag'])
    self.AssertErrContains(self.warning)
    self.assertEqual(args.bool_flag, True)

  def testHiddenDeprecatedFlag(self):
    self.parser.add_argument(
        '--foo',
        action=actions.DeprecationAction('--foo'),
        hidden=True,
        help='Auxilio aliis.')
    with self.assertRaises(SystemExit):
      self.parser.parse_args(['-h'])
    self.AssertOutputNotContains('--foo')


class MutexInvertedTest(util.WithTestTool, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    group = self.parser.add_argument_group(mutex=True)
    group.add_argument('--foo', action='store_true', help='Auxilio aliis.')
    group.add_argument('--bar', action='store_true', help='Auxilio aliis.')

  def testMutexInvertedDefault(self):
    args = self.parser.parse_args([])
    self.assertEqual(args.foo, False)
    self.assertEqual(args.bar, False)

  def testMutexInvertedFoo(self):
    args = self.parser.parse_args(['--foo'])
    self.assertEqual(args.foo, True)
    self.assertEqual(args.bar, False)

  def testMutexInvertedBar(self):
    args = self.parser.parse_args(['--bar'])
    self.assertEqual(args.foo, False)
    self.assertEqual(args.bar, True)

  def testMutexInvertedNoFoo(self):
    args = self.parser.parse_args(['--no-foo'])
    self.assertEqual(args.foo, False)
    self.assertEqual(args.bar, False)

  def testMutexInvertedNoFooBar(self):
    with self.assertRaises(SystemExit):
      self.parser.parse_args(['--no-foo', '--bar'])
    self.AssertErrContains(
        'argument --bar: At most one of --bar | --foo may be specified.')

  def testMutexInvertedFooNoFooNoBar(self):
    with self.assertRaises(SystemExit):
      self.parser.parse_args(['--no-foo', '--no-bar'])
    self.AssertErrContains(
        'argument --bar: At most one of --bar | --foo may be specified.')


class MultiCompleterTest(util.WithTestTool, sdk_test_base.WithOutputCapture):

  def testFirstArg(self):
    fun = arg_parsers.GetMultiCompleter(SimpleCompleter)
    matches = fun('fo', None)
    self.assertEqual(['foot', 'foobar'], matches)

  def testSecondArg(self):
    fun = arg_parsers.GetMultiCompleter(SimpleCompleter)
    matches = fun('fo,s', None)
    self.assertEqual(['fo,shoe', 'fo,shield'], matches)

  def testThirdArg(self):
    fun = arg_parsers.GetMultiCompleter(SimpleCompleter)
    matches = fun('fo,s,fi', None)
    self.assertEqual(['fo,s,first'], matches)

  def testEmptySuffix(self):
    fun = arg_parsers.GetMultiCompleter(SimpleCompleter)
    matches = fun('fo,s,', None)
    lst = ['foot', 'shoe', 'foobar', 'shield', 'first']
    self.assertEqual(['fo,s,' + item for item in lst], matches)

  def testEmptyPrefix(self):
    fun = arg_parsers.GetMultiCompleter(SimpleCompleter)
    matches = fun(',s', None)
    self.assertEqual([',shoe', ',shield'], matches)

  def testEmptyPrefixAndSuffix(self):
    fun = arg_parsers.GetMultiCompleter(SimpleCompleter)
    matches = fun(',', None)
    lst = ['foot', 'shoe', 'foobar', 'shield', 'first']
    self.assertEqual([',' + item for item in lst], matches)


class FileContentsTest(sdk_test_base.SdkBase, test_case.WithInput):

  def FileTest(self, data, binary=False):
    filename = os.path.join(self.temp_path, 'test.txt')
    with open(filename, 'w') as f:
      f.write(data)
    fun = arg_parsers.FileContents(binary=binary)
    expected_data = data
    if binary:
      expected_data = expected_data.encode('utf-8')
    self.assertEqual(expected_data, fun(filename))

  def StdinTest(self, lines, binary=True):
    # Each line has an implicit '\n' added by WriteInput.
    self.WriteInput(*lines)
    fun = arg_parsers.FileContents(binary=binary)
    expected_data = '\n'.join(lines) + '\n'
    if binary:
      expected_data = expected_data.encode('utf-8')
    self.assertEqual(expected_data, fun('-'))

  def testReadFileBytes(self):
    self.FileTest('abcdefg' * 100, binary=True)

  def testReadStdinBytes(self):
    self.StdinTest(['abcdefg'] * 100, binary=True)

  def testReadFile(self):
    self.FileTest('abcdefg' * 100)

  def testReadStdin(self):
    self.StdinTest(['abcdefg'] * 100)

  def testFileMissing(self):
    filename = os.path.join(self.temp_path, 'FileMissing.txt')
    fun = arg_parsers.FileContents()
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      fun(filename)


class StoreFilePathAndContentsTest(sdk_test_base.SdkBase, test_case.WithInput):

  def SetUp(self):
    self.parser = util.ArgumentParser()

  def ParseFileAndTest(self, data, binary=False):
    filename = self.Touch(self.temp_path,
                          'test.txt', contents=data, makedirs=True,)

    self.parser.add_argument(
        '--file-arg',
        action=arg_parsers.StoreFilePathAndContentsAction(binary=binary),
        help='Auxilio aliis.')
    ns = self.parser.parse_args(['--file-arg={}'.format(filename)])
    expected_data = data
    expected_path = filename
    if binary and isinstance(expected_data, six.string_types):
      expected_data = str(expected_data).encode('utf-8')
    self.assertEqual(expected_data, ns.file_arg)
    self.assertEqual(expected_path, ns.file_arg_path)

  def StdinTest(self, lines, binary=True):
    # Each line has an implicit '\n' added by WriteInput.
    self.WriteInput(*lines)
    self.parser.add_argument(
        '--file-arg',
        action=arg_parsers.StoreFilePathAndContentsAction(binary=binary),
        help='Auxilio aliis.')
    ns = self.parser.parse_args(['--file-arg=-'])
    expected_data = '\n'.join(lines) + '\n'
    expected_path = '-'
    if binary and isinstance(expected_data, six.string_types):
      expected_data = str(expected_data).encode('utf-8')
    self.assertEqual(expected_data, ns.file_arg)
    self.assertEqual(expected_path, ns.file_arg_path)

  def testReadFileBytes(self):
    self.ParseFileAndTest('abcdefg' * 100, binary=True)

  def testReadStdinBytes(self):
    self.ParseFileAndTest(b'abcdefg' * 100, binary=True)

  def testReadFile(self):
    self.ParseFileAndTest('abcdefg' * 100)

  def testReadStdin(self):
    self.StdinTest(['abcdefg'] * 100)

  def testFileMissing(self):
    filename = os.path.join(self.temp_path, 'FileMissing.txt')
    self.parser.add_argument(
        '--other-file-arg',
        action=arg_parsers.StoreFilePathAndContentsAction(),
        help='Auxilio aliis.')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.parser.parse_args(['--other-file-arg={}'.format(filename)])


class YAMLFileContentsTest(sdk_test_base.SdkBase, test_case.WithInput,
                           parameterized.TestCase):

  def YamlFileTest(self, data, ext='yaml', validator=None):
    filename = self.Touch(self.temp_path,
                          'test.{}'.format(ext), contents=data, makedirs=True)
    fun = arg_parsers.YAMLFileContents(validator=validator)
    expected_data = yaml.load(data)
    self.assertEqual(expected_data, fun(filename))

  def StdinTest(self, lines, validator=None):
    self.WriteInput(*lines)
    fun = arg_parsers.YAMLFileContents(validator=validator)
    expected_data = yaml.load('\n'.join(lines))
    self.assertEqual(expected_data, fun('-'))

  def testReadFile(self):
    yaml_data = """
    version: 1
    dataItem: Foo
    arrayItem:
    - val1
    - val2
    objectItem:
     prop1: bar
     prop2: baz
    """
    self.YamlFileTest(yaml_data)

    json_data = ("{'version': 1, "
                 "'dataItem': 'Foo', 'arrayItem': ['val1', 'val2'], "
                 "'objectItem': {'prop1': 'bar', 'prop2': 'baz'}}")
    self.YamlFileTest(json_data, ext='json')

  def testReadFileWithValidation(self):
    data = """
    version: 1
    dataItem: Foo
    arrayItem:
    - val1
    - val2
    objectItem:
     prop1: bar
     prop2: baz
    """
    is_valid = lambda x: x['dataItem'] == 'Foo'
    self.YamlFileTest(data, validator=is_valid)

  def testReadFileWithFailedValidation(self):
    data = """
    version: 1
    dataItem: Foo
    arrayItem:
    - val1
    - val2
    objectItem:
     prop1: bar
     prop2: baz
    """
    is_valid = lambda x: len(['arrayItem']) == 3
    with self.assertRaises(ValueError):
      self.YamlFileTest(data, validator=is_valid)

  def testReadNonYamlFile(self):
    data = 'ABCDefgHIJ123'
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.YamlFileTest(data)

  @parameterized.parameters(([
      'version: 1', 'dataItem: Foo', 'arrayItem:', '- val1', '- val1',
      'objectItem:', ' prop1: bar', ' prop2: baz'
  ],), ([("{'version': 1, 'dataItem': 'Foo', 'arrayItem': ['val1', 'val2'], "
          "'objectItem': {'prop1': 'bar', 'prop2': 'baz'}}")],))
  def testReadStdin(self, lines):
    self.StdinTest(lines)

  def testReadStdinWithValidation(self):
    lines = [
        'version: 1', 'dataItem: Foo', 'arrayItem:', '- val1', '- val1',
        'objectItem:', ' prop1: bar', ' prop2: baz'
    ]
    is_valid = lambda x: x['dataItem'] == 'Foo'
    self.StdinTest(lines, validator=is_valid)

  def testReadStdinFailedValidation(self):
    lines = [
        'version: 1', 'dataItem: Foo', 'arrayItem:', '- val1', '- val1',
        'objectItem:', ' prop1: bar', ' prop2: baz'
    ]
    is_valid = lambda x: len(['arrayItem']) == 3
    with self.assertRaises(ValueError):
      self.StdinTest(lines, validator=is_valid)

  def testReadNonYamlStdin(self):
    lines = ['ABCDefgHIJ123']
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.StdinTest(lines)

  def testFileMissing(self):
    filename = os.path.join(self.temp_path, 'FileMissing.json')
    fun = arg_parsers.YAMLFileContents()
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      fun(filename)


class ArgBooleanTest(subtests.Base, parameterized.TestCase):

  def RunSubTest(self, value, **kwargs):
    return arg_parsers.ArgBoolean(**kwargs)(value)

  @parameterized.named_parameters(
      ('Default',
       {},
       ['true', 'TrUe', 'YES', 'yEs'],
       ['false', 'FaLsE', 'NO', 'nO'],
       ['foo', 'bar', '0', '1']
      ),
      ('CaseSensitive',
       {'case_sensitive': True},
       ['true', 'yes'],
       ['false', 'no'],
       ['TrUe', 'YES', 'yEs', 'FaLsE', 'NO', 'nO']
      ),
      ('CustomBoolies',
       {'truthy_strings': ['da'], 'falsey_strings': ['ja']},
       ['DA', 'da'],
       ['Ja', 'jA'],
       ['true', 'yes', 'false', 'no', 'foobear']
      ),
  )
  def testDefaultArg(self, arg_parser_args, truthies, falsies, raisies):
    arg = arg_parsers.ArgBoolean(**arg_parser_args)
    for truthy in truthies:
      self.assertTrue(
          arg(truthy),
          msg='Expected ArgBoolean to return True for {!r}'.format(truthy))
    for falsey in falsies:
      self.assertFalse(
          arg(falsey),
          msg='Expected ArgBoolean to return True for {!r}'.format(falsey))
    for raisey in raisies:
      with self.assertRaises(arg_parsers.ArgumentTypeError):
        arg(raisey)

if __name__ == '__main__':
  test_case.main()
