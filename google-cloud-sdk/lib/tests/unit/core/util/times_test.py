# -*- coding: utf-8 -*-
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

"""Tests for googlecloudsdk.core.util.times."""

import datetime

from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import subtests
from tests.lib import test_case


FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'


class TimeZoneTest(test_case.TestCase):

  def testLOCALTimeZoneTest(self):
    self.assertIsNotNone(times.LOCAL)

  def testTUCTimeZoneTest(self):
    self.assertIsNotNone(times.UTC)
    self.assertEqual(datetime.timedelta(0, 0), times.UTC.utcoffset(None))

  def testTzOffset0000(self):
    tzinfo = times.TzOffset(0)
    self.assertEqual(datetime.timedelta(0, 0), tzinfo.utcoffset(None))

  def testTzOffset0700West(self):
    tzinfo = times.TzOffset(-7 * 60)
    self.assertEqual(datetime.timedelta(0, -7 * 60 * 60),
                     tzinfo.utcoffset(None))

  def testTzOffset0100East(self):
    tzinfo = times.TzOffset(1 * 60)
    self.assertEqual(datetime.timedelta(0, 1 * 60 * 60), tzinfo.utcoffset(None))

  def testGetTimeZoneSame(self):
    tz1 = times.GetTimeZone('UTC')
    self.assertIsNotNone(tz1)
    tz2 = times.GetTimeZone('UTC')
    self.assertIsNotNone(tz2)
    self.assertTrue(tz1 == tz2)

  def testGetTimeZoneDiff(self):
    tz1 = times.GetTimeZone('EST5EDT')
    self.assertIsNotNone(tz1)
    tz2 = times.GetTimeZone('US/Pacific')
    self.assertIsNotNone(tz2)
    tz3 = times.GetTimeZone('EST5EDT')
    self.assertIsNotNone(tz3)
    tz4 = times.GetTimeZone('America/Los_Angeles')
    self.assertIsNotNone(tz4)
    self.assertNotEqual(str(tz1), str(tz2))
    self.assertEqual(str(tz1), str(tz3))
    self.assertEqual(str(tz2), str(tz4))

  def testGetTimeZoneUTCStd(self):
    ts = 1234567890.123456
    tz = times.GetTimeZone('UTC')
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    expected = '2009-02-13T23:31:30.123456+0000'
    actual = times.FormatDateTime(dt, FORMAT)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))

  def testGetTimeZoneUTCDst(self):
    ts = 1244567890.123456
    tz = times.GetTimeZone('UTC')
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    expected = '2009-06-09T17:18:10.123456+0000'
    actual = times.FormatDateTime(dt, FORMAT)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))

  def testGetTimeZoneUTCMaxMicros(self):
    ts = 1244567890.999999
    tz = times.GetTimeZone('UTC')
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    expected = '2009-06-09T17:18:10.999999+0000'
    actual = times.FormatDateTime(dt, FORMAT)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))

  def testGetTimeZoneEST5EDTStd(self):
    ts = 1234567890.123456
    tz = times.GetTimeZone('America/New_York')
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    expected = '2009-02-13T18:31:30.123456-0500'
    actual = times.FormatDateTime(dt, FORMAT)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))

  def testGetTimeZoneEST5EDTDst(self):
    ts = 1244567890.123456
    tz = times.GetTimeZone('America/New_York')
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    expected = '2009-06-09T13:18:10.123456-0400'
    actual = times.FormatDateTime(dt, FORMAT)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))

  def testGetTimeZoneEDTPDT(self):
    ts = 1244567890.123456
    tz_in = times.GetTimeZone('America/New_York')
    tz_out = times.GetTimeZone('US/Pacific')
    dt = times.GetDateTimeFromTimeStamp(ts, tz_in)
    expected = '2009-06-09T10:18:10.123456-0700'
    actual = times.FormatDateTime(dt, FORMAT, tz_out)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))

  def testGetTimeZoneEST5EDTMaxMicros(self):
    ts = 1244567890.999999
    tz = times.GetTimeZone('America/New_York')
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    expected = '2009-06-09T13:18:10.999999-0400'
    actual = times.FormatDateTime(dt, FORMAT)
    self.assertEqual(expected, actual)
    expected = str(ts)
    actual = times.FormatDateTime(dt, '%s')
    self.assertEqual(expected, actual)
    self.assertEqual(ts, times.GetTimeStampFromDateTime(dt))


class TimeZoneWIthNonAsciiNameTest(test_case.TestCase):
  """Tests the non-ascii timezone name code paths for the %Z strftime format."""

  def testFormatTzNameAsciiTzUnaware(self):
    expected = 'ascii'
    ts = 1244567890.999999
    tz = times.TzOffset(60, expected)
    dt = times.GetDateTimeFromTimeStamp(ts)
    actual = times.FormatDateTime(dt, '%Z', tz)
    self.assertEqual(expected, actual)

  def testFormatTzNameAscii(self):
    expected = 'ascii'
    ts = 1244567890.999999
    tz = times.TzOffset(60, expected)
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    actual = times.FormatDateTime(dt, '%Z')
    self.assertEqual(expected, actual)

  def testFormatTzNameIso8859_1Unaware(self):
    expected = u'ÜñîçòÐé'
    ts = 1244567890.999999
    tz = times.TzOffset(60, expected.encode('iso8859-1'))
    dt = times.GetDateTimeFromTimeStamp(ts)
    actual = times.FormatDateTime(dt, '%Z', tz)
    self.assertEqual(expected, actual)

  def testFormatTzNameIso8859_1(self):
    expected = u'ÜñîçòÐé'
    ts = 1244567890.999999
    tz = times.TzOffset(60, expected.encode('iso8859-1'))
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    actual = times.FormatDateTime(dt, '%Z')
    self.assertEqual(expected, actual)

  def testFormatTzNameUtf8Unaware(self):
    expected = u'Ṳᾔḯ¢◎ⅾℯ'
    ts = 1244567890.999999
    tz = times.TzOffset(60, expected.encode('utf8'))
    dt = times.GetDateTimeFromTimeStamp(ts)
    actual = times.FormatDateTime(dt, '%Z', tz)
    self.assertEqual(expected, actual)

  def testFormatTzNameUtf8(self):
    expected = u'Ṳᾔḯ¢◎ⅾℯ'
    ts = 1244567890.999999
    tz = times.TzOffset(60, expected.encode('utf8'))
    dt = times.GetDateTimeFromTimeStamp(ts, tz)
    actual = times.FormatDateTime(dt, '%Z')
    self.assertEqual(expected, actual)


class ParseDateTimeTest(subtests.Base):

  def RunSubTest(self, subject, tz=None, tzinfo=None, fmt=None,
                 parse_fmt=None, timestamp=False):
    if tz:
      tzinfo = times.GetTimeZone(tz)
    if isinstance(subject, (int, long, float)):
      dt = times.GetDateTimeFromTimeStamp(subject, tzinfo=tzinfo)
    else:
      dt = times.ParseDateTime(subject, fmt=parse_fmt, tzinfo=tzinfo)
    if timestamp:
      actual = times.GetTimeStampFromDateTime(dt)
    else:
      actual = times.FormatDateTime(dt, fmt=fmt)
    return actual

  def testParseDateTimeUTC(self):
    self.Run('1970-01-01T00:00:00.000Z', '1970-01-01T00:00:00.000Z')
    self.Run('1970-01-01T00:00:00.000Z', '1970-01-01T00:00:00Z')
    self.Run('1970-01-01T00:00:00.000Z', '1970-01-01T00:00:00-00:00')
    self.Run('1970-01-01T00:00:00.000Z', '1970-01-01T00:00:00+00:00')
    self.Run('1970-01-01T00:00:00.000Z', 'January 1, 1970 UTC')
    self.Run('1970-01-01T00:00:00.000Z', 'January 1, 1970Z')
    self.Run('1970-01-01T01:00:00.000+01:00', '1970-01-01T01:00:00+01:00')
    self.Run('2009-02-13T23:31:30.000Z', '2009-02-13T23:31:30.000Z')
    self.Run('2009-02-13T23:31:30.000Z', '2009-02-13T23:31:30Z')
    self.Run('2009-02-13T23:31:30.000Z', 'February 13, 2009 23:31:30UTC')
    self.Run('2009-02-13T23:31:30.000Z', 'Feb 13, 2009 23:31:30 Z')
    self.Run('2009-02-13T16:31:30.000-07:00', '2009-02-13T16:31:30-07:00')

  def testParseDateTimeUSEastern(self):
    self.Run('1970-01-01T00:00:00.000-05:00', '1970-01-01T00:00:00.000 EST')
    self.Run('1970-01-01T00:00:00.000-05:00', '1970-01-01T00:00:00 EST')
    self.Run('1970-01-01T00:00:00.000-05:00', '1970-01-01T00:00:00-05:00')
    self.Run('1970-01-01T00:00:00.000-05:00', 'January 1, 1970 EST')
    self.Run('1970-01-01T00:00:00.000-05:00', 'January 1, 1970 EDT')
    self.Run('1970-01-01T00:00:00.000-05:00', 'January 1, 1970 US/Eastern')
    self.Run('2009-02-13T23:31:30.000-05:00', '2009-02-13T23:31:30.000 EST')
    self.Run('2009-02-13T23:31:30.000-05:00', '2009-02-13T23:31:30 EST')
    self.Run('2009-02-13T16:31:30.000-05:00', '2009-02-13T16:31:30-05:00')
    self.Run('2009-02-13T16:31:30.000-05:00', 'February 13, 2009 16:31:30 EST')
    self.Run('2009-02-13T16:31:30.000-05:00', 'February 13, 2009 16:31:30 EDT')

  def testParseDateTimeUSPacific(self):
    self.Run('1970-01-01T00:00:00.000-08:00', '1970-01-01T00:00:00.000 PST')
    self.Run('1970-01-01T00:00:00.000-08:00', '1970-01-01T00:00:00 PST')
    self.Run('1970-01-01T00:00:00.000-08:00', '1970-01-01T00:00:00-08:00')
    self.Run('1970-01-01T00:00:00.000-08:00', 'January 1, 1970 PST')
    self.Run('1970-01-01T00:00:00.000-08:00', 'January 1, 1970 PDT')
    self.Run('2009-02-13T23:31:30.000-08:00', '2009-02-13T23:31:30.000 PST')
    self.Run('2009-02-13T23:31:30.000-08:00', '2009-02-13T23:31:30 PST')
    self.Run('2009-02-13T16:31:30.000-08:00', '2009-02-13T16:31:30-08:00')

  def testParseDateTimeUnixDateVariousZones(self):
    self.Run('2016-03-01T15:46:49.000-04:00', 'Tue Mar  1 15:46:49 AST 2016')
    self.Run('2016-03-01T15:46:49.000-05:00', 'Tue Mar  1 15:46:49 EST 2016')
    self.Run('2016-03-01T15:46:49.000-06:00', 'Tue Mar  1 15:46:49 CST 2016')
    self.Run('2016-03-01T15:46:49.000-07:00', 'Tue Mar  1 15:46:49 MST 2016')
    self.Run('2016-03-01T15:46:49.000-08:00', 'Tue Mar  1 15:46:49 PST 2016')
    self.Run('2016-03-01T15:46:49.000-10:00', 'Tue Mar  1 15:46:49 HST 2016')

    self.Run('2016-04-01T15:46:49.000-03:00', 'Fri Apr  1 15:46:49 AST 2016')
    self.Run('2016-04-01T15:46:49.000-04:00', 'Fri Apr  1 15:46:49 EST 2016')
    self.Run('2016-04-01T15:46:49.000-05:00', 'Fri Apr  1 15:46:49 CST 2016')
    self.Run('2016-04-01T15:46:49.000-07:00', 'Fri Apr  1 15:46:49 MST 2016')
    self.Run('2016-04-01T15:46:49.000-07:00', 'Fri Apr  1 15:46:49 PST 2016')
    self.Run('2016-04-01T15:46:49.000-10:00', 'Fri Apr  1 15:46:49 HST 2016')

    self.Run('2016-04-01T00:00:00.000-03:00', 'Fri Apr  1 2016 AST')
    self.Run('2016-04-01T00:00:00.000-04:00', 'Fri Apr  1 2016 EST')
    self.Run('2016-04-01T00:00:00.000-05:00', 'Fri Apr  1 2016 CST')
    self.Run('2016-04-01T00:00:00.000-07:00', 'Fri Apr  1 2016 MST')
    self.Run('2016-04-01T00:00:00.000-07:00', 'Fri Apr  1 2016 PST')
    self.Run('2016-04-01T00:00:00.000-10:00', 'Fri Apr  1 2016 HST')

  def testParseDateTimeUnixDateVariousIsSpaceCombinations(self):
    self.Run('2016-04-01T15:46:00.000-04:00', 'Fri  Apr  1  15:46  EST  2016')
    self.Run('2016-04-01T15:46:00.000-04:00', 'Fri\nApr\n1\n15:46\nEST\n2016')
    self.Run('2016-04-01T15:46:00.000-04:00', 'Fri\rApr\r1\r15:46\rEST\r2016')
    self.Run('2016-04-01T15:46:00.000-04:00', 'Fri\tApr\t1\t15:46\tEST\t2016')

  def testGetTimeStampFromDateTime(self):
    self.Run(0, '1970-01-01T00:00:00.000Z', timestamp=True)
    self.Run(0, '1970-01-01T00:00:00Z', timestamp=True)
    self.Run(0, '1970-01-01T00:00:00-00:00', timestamp=True)
    self.Run(0, '1970-01-01T00:00:00+00:00', timestamp=True)
    self.Run(0, '1970-01-01T01:00:00+01:00', timestamp=True)
    self.Run(1234567890, '2009-02-13T23:31:30.000Z', timestamp=True)
    self.Run(1234567890, '2009-02-13T23:31:30Z', timestamp=True)
    self.Run(1234567890, '2009-02-13T16:31:30-07:00', timestamp=True)

  def testGetDateTimeFromTimeStamp(self):
    self.Run('1970-01-01T00:00:00.000Z', 0, tz='UTC')
    self.Run('1970-01-01T00:00:00.000Z', 0, tz='UTC')
    self.Run('1970-01-01T00:00:00.000Z', 0, tz='UTC')
    self.Run('1970-01-01T00:00:00.000Z', 0, tz='UTC')
    self.Run('1970-01-01T01:00:00.000+01:00', 0, tz='UTC+01:00')
    self.Run('2009-02-13T23:31:30.000Z', 1234567890, tz='UTC')
    self.Run('2009-02-13T16:31:30.000-07:00', 1234567890, tz='UTC-07:00')

  def testMicorosecond(self):
    self.Run(0.000001, '1970-01-01T00:00:00.000001Z', timestamp=True)
    self.Run(0.000010, '1970-01-01T00:00:00.00001Z', timestamp=True)
    self.Run(0.000100, '1970-01-01T00:00:00.0001Z', timestamp=True)
    self.Run(0.001000, '1970-01-01T00:00:00.001Z', timestamp=True)
    self.Run(0.010000, '1970-01-01T00:00:00.01Z', timestamp=True)
    self.Run(0.100000, '1970-01-01T00:00:00.1Z', timestamp=True)

  def testParseDateTimeVariations(self):
    self.Run('2009-02-13T16:31:30.000-07:00', '2009-02-13T16:31:30-07')
    self.Run('2009-02-13T16:31:30.000-07:00', '2009-02-13 16:31:30-07')
    self.Run('2009-02-13T16:31:30.000-07:00', '2009-02-13T16:31:30-7')
    self.Run('2009-02-13T16:31:30.000-07:00', '2009-02-13 16:31:30-7')
    self.Run('2009-02-13T16:31:00.000-07:00', '2009-02-13T16:31-7')
    self.Run('2009-02-13T16:31:00.000-07:00', '2009-02-13 16:31-7')
    self.Run('2009-02-13T23:31:00.000Z', '2009-02-13T23:31Z')
    self.Run('2009-02-13T23:31:00.000Z', '2009-02-13 23:31Z')

  def testParseDateTimeExceptions(self):
    self.Run(None, '1776-07-04T12:00:00', exception=times.DateTimeValueError)
    self.Run(None, '0000-00-00T00:00:00', exception=times.DateTimeSyntaxError)
    self.Run(None, '0000-00-00T00:00:00', fmt='%Y-%m-%dT%H:%M:%S',
             exception=times.DateTimeSyntaxError)
    self.Run(None, '2009-00-13T16:31:30', exception=times.DateTimeSyntaxError)
    self.Run(None, '2009-02-33T16:31-0700', exception=times.DateTimeSyntaxError)
    self.Run(None, '2009-02-13T24:31-0700', exception=times.DateTimeSyntaxError)
    self.Run(None, '2009-02-13T16:61-0700', exception=times.DateTimeSyntaxError)
    self.Run(None, '2009-02-13T16:31-2400', exception=times.DateTimeValueError)
    self.Run(None, '2006-02-29 01:23:45 EST',
             exception=times.DateTimeSyntaxError)
    self.Run(None, '0000-00-00T00:00:00', exception=times.DateTimeSyntaxError)
    self.Run(None, '0000-00-00T00:00:00', fmt='%Y-%m-%dT%H:%M:%S',
             exception=times.DateTimeSyntaxError)
    self.Run(None, '99999999', exception=times.DateTimeSyntaxError)
    self.Run(None, '99999999', fmt='%Y-%m-%d',
             exception=times.DateTimeSyntaxError)

  def testFormatDateTimeFractionExtensions(self):
    self.Run('000000', '2016-03-02T08:26:46.000000-05:00', fmt='%f')
    self.Run('000000', '2016-03-02T08:26:46.000000-05:00', fmt='%9f')
    self.Run('000', '2016-03-02T08:26:46.000000-05:00', fmt='%3f')

    self.Run('332093', '2016-03-02T08:26:46.332093-05:00', fmt='%f')
    self.Run('332093', '2016-03-02T08:26:46.332093-05:00', fmt='%9f')
    self.Run('332', '2016-03-02T08:26:46.332093-05:00', fmt='%3f')

  def testFormatDateTimeZoneOffsetExtensions(self):
    self.Run('+0000', '2016-03-02T08:26:46Z', fmt='%z')
    self.Run('Z', '2016-03-02T08:26:46Z', fmt='%Ez')
    self.Run('+00:00', '2016-03-02T08:26:46Z', fmt='%Oz')

    self.Run('+0000', '2016-03-02T08:26:46 UTC', fmt='%z')
    self.Run('Z', '2016-03-02T08:26:46 UTC', fmt='%Ez')
    self.Run('+00:00', '2016-03-02T08:26:46 UTC', fmt='%Oz')

    self.Run('+0000', '2016-03-02T08:26:46-0000', fmt='%z')
    self.Run('Z', '2016-03-02T08:26:46+0000', fmt='%Ez')
    self.Run('+00:00', '2016-03-02T08:26:46+0000', fmt='%Oz')

    self.Run('+0000', '2016-03-02T08:26:46-00:00', fmt='%z')
    self.Run('Z', '2016-03-02T08:26:46+00:00', fmt='%Ez')
    self.Run('+00:00', '2016-03-02T08:26:46+00:00', fmt='%Oz')

    self.Run('+0000', '2016-03-02T08:26:46+00:00', fmt='%z')
    self.Run('Z', '2016-03-02T08:26:46+00:00', fmt='%Ez')
    self.Run('+00:00', '2016-03-02T08:26:46+00:00', fmt='%Oz')

    self.Run('-0500', '2016-03-02T08:26:46-05:00', fmt='%z')
    self.Run('-05:00', '2016-03-02T08:26:46-05:00', fmt='%Ez')
    self.Run('-05:00', '2016-03-02T08:26:46-05:00', fmt='%Oz')

  def testFormatDateTimeAllExtensions(self):
    self.Run('[1-0500]', '2016-03-02T08:26:46.123-05:00', fmt='[%1f%z]')
    self.Run('[12-05:00]', '2016-03-02T08:26:46.123-05:00', fmt='[%2f%Ez]')
    self.Run('[1230-05:00]', '2016-03-02T08:26:46.123-05:00', fmt='[%4f%Oz]')

  def testDateTimeDstBoundariesESTInString(self):
    self.Run('2005-01-28T01:23:45.000-05:00', '2005-01-28T01:23:45 EST')
    self.Run('2006-02-28T01:23:45.000-05:00', '2006-02-28T01:23:45 EST')
    self.Run('2007-03-28T01:23:45.000-04:00', '2007-03-28T01:23:45 EST')
    self.Run('2008-04-28T01:23:45.000-04:00', '2008-04-28T01:23:45 EST')
    self.Run('2009-05-28T01:23:45.000-04:00', '2009-05-28T01:23:45 EST')
    self.Run('2010-06-28T01:23:45.000-04:00', '2010-06-28T01:23:45 EST')
    self.Run('2011-07-28T01:23:45.000-04:00', '2011-07-28T01:23:45 EST')
    self.Run('2012-08-28T01:23:45.000-04:00', '2012-08-28T01:23:45 EST')
    self.Run('2013-09-28T01:23:45.000-04:00', '2013-09-28T01:23:45 EST')
    self.Run('2014-10-28T01:23:45.000-04:00', '2014-10-28T01:23:45 EST')
    self.Run('2015-11-28T01:23:45.000-05:00', '2015-11-28T01:23:45 EST')
    self.Run('2016-12-28T01:23:45.000-05:00', '2016-12-28T01:23:45 EST')

  def testDateTimeDstBoundariesPSTInTzInfo(self):
    z = times.GetTimeZone('US/Pacific')
    self.Run('2005-01-28T01:23:45.000-08:00', '2005-01-28T01:23:45', tzinfo=z)
    self.Run('2006-02-28T01:23:45.000-08:00', '2006-02-28T01:23:45', tzinfo=z)
    self.Run('2007-03-28T01:23:45.000-07:00', '2007-03-28T01:23:45', tzinfo=z)
    self.Run('2008-04-28T01:23:45.000-07:00', '2008-04-28T01:23:45', tzinfo=z)
    self.Run('2009-05-28T01:23:45.000-07:00', '2009-05-28T01:23:45', tzinfo=z)
    self.Run('2010-06-28T01:23:45.000-07:00', '2010-06-28T01:23:45', tzinfo=z)
    self.Run('2011-07-28T01:23:45.000-07:00', '2011-07-28T01:23:45', tzinfo=z)
    self.Run('2012-08-28T01:23:45.000-07:00', '2012-08-28T01:23:45', tzinfo=z)
    self.Run('2013-09-28T01:23:45.000-07:00', '2013-09-28T01:23:45', tzinfo=z)
    self.Run('2014-10-28T01:23:45.000-07:00', '2014-10-28T01:23:45', tzinfo=z)
    self.Run('2015-11-28T01:23:45.000-08:00', '2015-11-28T01:23:45', tzinfo=z)
    self.Run('2016-12-28T01:23:45.000-08:00', '2016-12-28T01:23:45', tzinfo=z)

  def testDateTimeDstBoundariesMESTInString(self):
    self.Run('2016-01-28T01:23:45.000+01:00', '2016-01-28T01:23:45 MEST')
    self.Run('2016-02-28T01:23:45.000+01:00', '2016-02-28T01:23:45 MEST')
    self.Run('2016-03-28T01:23:45.000+02:00', '2016-03-28T01:23:45 MEST')
    self.Run('2016-04-28T01:23:45.000+02:00', '2016-04-28T01:23:45 MEST')
    self.Run('2016-05-28T01:23:45.000+02:00', '2016-05-28T01:23:45 MEST')
    self.Run('2016-06-28T01:23:45.000+02:00', '2016-06-28T01:23:45 MEST')
    self.Run('2016-07-28T01:23:45.000+02:00', '2016-07-28T01:23:45 MEST')
    self.Run('2016-08-28T01:23:45.000+02:00', '2016-08-28T01:23:45 MEST')
    self.Run('2016-09-28T01:23:45.000+02:00', '2016-09-28T01:23:45 MEST')
    self.Run('2016-10-28T01:23:45.000+02:00', '2016-10-28T01:23:45 MEST')
    self.Run('2016-11-28T01:23:45.000+01:00', '2016-11-28T01:23:45 MEST')
    self.Run('2016-12-28T01:23:45.000+01:00', '2016-12-28T01:23:45 MEST')

  def testDateTimeDstBoundariesMESTInTzInfo(self):
    z = times.GetTimeZone('MEST')
    self.Run('2016-01-28T01:23:45.000+01:00', '2016-01-28T01:23:45', tzinfo=z)
    self.Run('2016-02-28T01:23:45.000+01:00', '2016-02-28T01:23:45', tzinfo=z)
    self.Run('2016-03-28T01:23:45.000+02:00', '2016-03-28T01:23:45', tzinfo=z)
    self.Run('2016-04-28T01:23:45.000+02:00', '2016-04-28T01:23:45', tzinfo=z)
    self.Run('2016-05-28T01:23:45.000+02:00', '2016-05-28T01:23:45', tzinfo=z)
    self.Run('2016-06-28T01:23:45.000+02:00', '2016-06-28T01:23:45', tzinfo=z)
    self.Run('2016-07-28T01:23:45.000+02:00', '2016-07-28T01:23:45', tzinfo=z)
    self.Run('2016-08-28T01:23:45.000+02:00', '2016-08-28T01:23:45', tzinfo=z)
    self.Run('2016-09-28T01:23:45.000+02:00', '2016-09-28T01:23:45', tzinfo=z)
    self.Run('2016-10-28T01:23:45.000+02:00', '2016-10-28T01:23:45', tzinfo=z)
    self.Run('2016-11-28T01:23:45.000+01:00', '2016-11-28T01:23:45', tzinfo=z)
    self.Run('2016-12-28T01:23:45.000+01:00', '2016-12-28T01:23:45', tzinfo=z)

  def testDateTimeRelativeDuration(self):
    self.StartObjectPatch(times, 'Now', return_value=times.ParseDateTime(
        '2009-06-09T13:18:10.123456-0400'))

    self.Run('2009-06-16T13:18:10.123-04:00', '+p7d')
    self.Run('2009-06-02T13:18:10.123-04:00', '-p7d')
    self.Run('2009-06-10T05:18:10.123-04:00', '+p16h')
    self.Run('2009-06-08T21:18:10.123-04:00', '-p16h')
    self.Run('2009-06-11T01:18:10.123-04:00', '+p36h')
    self.Run('2009-06-08T01:18:10.123-04:00', '-p36h')
    self.Run('2009-06-12T13:18:10.123-04:00', '+p72h')
    self.Run('2009-06-06T13:18:10.123-04:00', '-p72h')

  def testDateTimeParseFmtESTInTzInfo(self):
    z = times.GetTimeZone('EST')
    self.Run('2016-01-28T00:00:00.000-05:00', '2016-01-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-02-28T00:00:00.000-05:00', '2016-02-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-03-28T00:00:00.000-04:00', '2016-03-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-04-28T00:00:00.000-04:00', '2016-04-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-05-28T00:00:00.000-04:00', '2016-05-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-06-28T00:00:00.000-04:00', '2016-06-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-07-28T00:00:00.000-04:00', '2016-07-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-08-28T00:00:00.000-04:00', '2016-08-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-09-28T00:00:00.000-04:00', '2016-09-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-10-28T00:00:00.000-04:00', '2016-10-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-11-28T00:00:00.000-05:00', '2016-11-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)
    self.Run('2016-12-28T00:00:00.000-05:00', '2016-12-28',
             parse_fmt='%Y-%m-%d', tzinfo=z)

  def testDateTimeDefaults(self):
    self.StartObjectPatch(times, 'Now', return_value=times.ParseDateTime(
        '2003-09-25T10:49:41.519Z'))
    z = times.GetTimeZone('EDT')

    self.Run('2003-09-25T10:49:41.519Z', '2003-09-25T10:49:41.519Z', tzinfo=z)
    self.Run('2003-09-25T10:49:41.000Z', '2003-09-25T10:49:41Z', tzinfo=z)
    self.Run('2003-09-25T10:49:41.500Z', '2003-09-25T10:49:41.5-0000', tzinfo=z)
    self.Run('2003-09-25T10:49:41.500-03:00', '2003-09-25T10:49:41.5-03:00',
             tzinfo=z)
    self.Run('2003-09-25T10:49:41.500+03:00', '2003-09-25T10:49:41.5+0300',
             tzinfo=z)
    self.Run('2003-09-25T10:49:41.000-04:00', '2003-09-25T10:49:41', tzinfo=z)
    self.Run('2003-09-25T10:49:00.000-04:00', '2003-09-25T10:49', tzinfo=z)
    self.Run('2003-09-25T10:00:00.000-04:00', '2003-09-25T10', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003-09-25', tzinfo=z)
    self.Run('2003-09-25T10:49:41.000-03:00', 'Thu, 25 Sep 2003 10:49:41 -0300',
             tzinfo=z)
    self.Run('2003-09-25T10:36:28.000-04:00', 'Thu Sep 25 10:36:28 EDT 2003',
             tzinfo=z)
    self.Run('2003-09-25T10:36:28.000-04:00', '2003 10:36:28 EDT 25 Sep Thu',
             tzinfo=z)
    self.Run('2003-09-25T10:36:28.000-04:00', 'Thu Sep 25 10:36:28 2003',
             tzinfo=z)
    self.Run('2003-09-25T10:36:28.000-04:00', 'Thu Sep 25 10:36:28', tzinfo=z)
    self.Run('2003-09-25T10:36:28.000-04:00', 'Thu Sep 10:36:28', tzinfo=z)
    self.Run('2003-09-25T10:36:28.000-04:00', 'Thu 10:36:28', tzinfo=z)
    self.Run('2003-09-25T10:36:00.000-04:00', 'Thu 10:36', tzinfo=z)
    self.Run('2003-09-25T10:36:00.000-04:00', '10:36', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', 'Thu Sep 25 2003', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', 'Sep 25 2003', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', 'Sep 2003', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', 'Sep', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003', tzinfo=z)
    self.Run('2003-09-25T10:49:41.500-03:00', '20030925T104941.5-0300',
             tzinfo=z)
    self.Run('2003-09-25T10:49:41.000-03:00', '20030925T104941-0300', tzinfo=z)
    self.Run('2003-09-25T10:49:41.000-04:00', '20030925T104941', tzinfo=z)
    self.Run('2003-09-25T10:49:00.000-04:00', '20030925T1049', tzinfo=z)
    self.Run('2003-09-25T10:00:00.000-04:00', '20030925T10', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '20030925', tzinfo=z)
    self.Run('2003-09-25T10:49:41.000-04:00', '20030925T104941', tzinfo=z)
    self.Run('2003-09-25T10:49:41.000-04:00', '20030925104941', tzinfo=z)
    self.Run('2003-09-25T10:49:00.000-04:00', '20030925T1049', tzinfo=z)
    self.Run('2003-09-25T10:49:00.000-04:00', '200309251049', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003-09-25', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003-Sep-25', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '25-Sep-2003', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', 'Sep-25-2003', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '09-25-2003', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003.Sep.25', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003/09/25', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003 Sep 25', tzinfo=z)
    self.Run('2003-09-25T00:00:00.000-04:00', '2003 09 25', tzinfo=z)
    self.Run('2002-07-22T06:44:34.819Z', '-P1Y2M3DT4H5M6.7S', tzinfo=z)
    self.Run('2004-11-28T14:54:48.219Z', '+p1y2m3dT4h5m6.7s', tzinfo=z)
    self.Run('2003-09-25T09:39:41.519Z', '-p1h10m', tzinfo=z)


class ConvertDateTimeTest(test_case.TestCase):

  def testDateTimeParseFmtDefaultTzInfo(self):
    t1 = times.ParseDateTime('2016-01-28T00:00:00', '%Y-%m-%dT%H:%M:%S')
    self.assertEqual(t1.tzinfo, times.LOCAL)
    t2 = times.ParseDateTime('2016-01-28T00:00:00')
    self.assertEqual(t2.tzinfo, times.LOCAL)
    self.assertEqual(t1.tzinfo.utcoffset(t1), t2.tzinfo.utcoffset(t2))
    self.assertEqual(t1, t2)

  def testDateTimeRoundTrip(self):
    subject = '2016-02-29T08:46:37.639-05:00'
    dt_in = times.ParseDateTime(subject)
    ts = times.GetTimeStampFromDateTime(dt_in)
    dt_out = times.GetDateTimeFromTimeStamp(ts, tzinfo=dt_in.tzinfo)
    expected = subject
    actual = times.FormatDateTime(dt_out)
    self.assertEqual(expected, actual)

  def testLocalizeDateTime(self):
    subject = '2016-02-29T08:46:37.639-05:00'
    dt_in = times.ParseDateTime(subject)
    tz_out = times.GetTimeZone('US/Pacific')
    dt_out = times.LocalizeDateTime(dt_in, tz_out)
    expected = '2016-02-29T05:46:37.639-08:00'
    actual = times.FormatDateTime(dt_out)
    self.assertEqual(expected, actual)

  def testLocalizeDateTimeUnaware(self):
    self.StartObjectPatch(times, 'LOCAL', new=times.GetTimeZone('US/Eastern'))
    dt_in = datetime.datetime(2016, 12, 21, 8, 46, 37, 639000, tzinfo=None)
    tz_out = times.GetTimeZone('US/Pacific')
    dt_out = times.LocalizeDateTime(dt_in, tz_out)
    expected = '2016-12-21T08:46:37.639-08:00'
    actual = times.FormatDateTime(dt_out)
    self.assertEqual(expected, actual)

  def testLocalizeDateTimeUnawareDST(self):
    """Same test as previous, but with DST in effect."""
    self.StartObjectPatch(times, 'LOCAL', new=times.GetTimeZone('US/Eastern'))
    dt_in = datetime.datetime(2016, 6, 21, 8, 46, 37, 639000, tzinfo=None)
    tz_out = times.GetTimeZone('US/Pacific')
    dt_out = times.LocalizeDateTime(dt_in, tz_out)
    expected = '2016-06-21T08:46:37.639-07:00'
    actual = times.FormatDateTime(dt_out)
    self.assertEqual(expected, actual)

  def testLocalizeDateTimeLocal(self):
    self.StartObjectPatch(times, 'LOCAL', new=times.GetTimeZone('US/Eastern'))
    dt_in = datetime.datetime(2016, 12, 21, 8, 46, 37, 639000,
                              tzinfo=times.LOCAL)
    tz_out = times.GetTimeZone('US/Pacific')
    dt_out = times.LocalizeDateTime(dt_in, tz_out)
    expected = '2016-12-21T05:46:37.639-08:00'
    actual = times.FormatDateTime(dt_out)
    self.assertEqual(expected, actual)

  def testLocalizeDateTimeLocalDST(self):
    """Same test as previous, but with DST in effect."""
    self.StartObjectPatch(times, 'LOCAL', new=times.GetTimeZone('US/Eastern'))
    dt_in = datetime.datetime(2016, 6, 21, 8, 46, 37, 639000,
                              tzinfo=times.LOCAL)
    tz_out = times.GetTimeZone('US/Pacific')
    dt_out = times.LocalizeDateTime(dt_in, tz_out)
    expected = '2016-06-21T05:46:37.639-07:00'
    actual = times.FormatDateTime(dt_out)
    self.assertEqual(expected, actual)

  def testParseDateDurationDefaultTzInfo(self):
    def fake_now(tzinfo=None):
      return datetime.datetime(2017, 4, 5, 15, 9, 1, 999000, tzinfo)
    self.StartObjectPatch(times, 'Now', side_effect=fake_now)

    t1 = times.ParseDateTime('-PT10M', tzinfo=times.LOCAL)
    self.assertEqual(t1.tzinfo, times.LOCAL)
    t2 = times.ParseDateTime('-PT10M')
    self.assertEqual(t1, t2)


class NowTest(test_case.TestCase):

  def testNowUTC(self):
    now = times.Now(times.UTC)
    actual = times.FormatDateTime(now, '%z')
    self.assertEqual('+0000', actual)
    actual = times.FormatDateTime(now, '%Ez')
    self.assertEqual('Z', actual)
    actual = times.FormatDateTime(now, '%Oz')
    self.assertEqual('+00:00', actual)

  def testNowEST(self):
    tz = times.GetTimeZone('US/Eastern')
    now = times.Now(tz)
    actual = times.FormatDateTime(now, '%z')
    self.assertTrue(actual == '-0400' or actual == '-0500')
    actual = times.FormatDateTime(now, '%Ez')
    self.assertTrue(actual == '-04:00' or actual == '-05:00')
    actual = times.FormatDateTime(now, '%Oz')
    self.assertTrue(actual == '-04:00' or actual == '-05:00')


class DurationTest(subtests.Base):

  def RunSubTest(self, subject, end=None, relative=None, parts=3, precision=3,
                 calendar=False, fmt=None):
    if end and relative:
      duration = times.ParseDuration(subject)
      delta = times.ParseDateTime(end) - times.ParseDateTime(relative)
      duration.AddTimeDelta(delta, calendar=calendar)
      actual = times.FormatDuration(
          duration, parts=parts, precision=precision)
    else:
      if end:
        duration = times.GetDurationFromTimeDelta(
            times.ParseDateTime(end) - times.ParseDateTime(subject),
            calendar=calendar)
      else:
        duration = times.ParseDuration(subject)
      if relative:
        dt = times.GetDateTimePlusDuration(
            times.ParseDateTime(relative), duration)
        actual = times.FormatDateTime(dt, fmt=fmt)
      else:
        actual = times.FormatDuration(
            duration, parts=parts, precision=precision)
    return actual

  def testParseDurationFormatDuration(self):
    self.Run('P0', 'P0')
    self.Run('P0', '-P0')
    self.Run('P0', '+P0')
    self.Run('P1Y2M3D', 'P1Y2M3DT4H5M6S')
    self.Run('P1Y2M3D', '+P1Y2M3DT4H5M6S')
    self.Run('-P1Y2M3D', '-P1Y2M3DT4H5M6S')
    self.Run('P1Y2M3D', 'P1Y2M3DT4H5M6.7S')
    self.Run('P1Y2M3D', '+P1Y2M3DT4H5M6.7S')
    self.Run('-P1Y2M3D', '-P1Y2M3DT4H5M6.7S')
    self.Run('P1Y2M3D', 'p1y2m3dt4h5m6.7s')
    self.Run('-P1Y2M3D', '-p1y2m3dt4h5m6.7s')
    self.Run('PT1S', 'P1S')
    self.Run('-PT1S', '-P1S')
    self.Run('PT1M30S', 'PT1.5M')
    self.Run('-PT1M30S', '-PT1.5M')
    self.Run('PT1H30M', 'PT1.5H')
    self.Run('-PT1H30M', '-PT1.5H')
    self.Run('P1M15D', 'P1.5M')
    self.Run('-P1M15D', '-P1.5M')
    self.Run('P365D', 'P365D')
    self.Run('-P365D', '-P365D')
    self.Run('PT1S', 'PT1S')
    self.Run('PT0.001S', 'PT0.001S')
    self.Run('P2Y183D', 'P2.5Y')
    self.Run('P2Y183D', 'P2,5Y')
    self.Run('P1DT6H', 'P1.25D')
    self.Run('P14D', 'P2W')

    # Lenient variants.

    self.Run('P0', 'P0')
    self.Run('P0', '0s')
    self.Run('P0', 'T0s')
    self.Run('PT1M5S', '1m5s')
    self.Run('PT3H2M1.5S', '3h2m1.5s')

  def testParseDurationFormatDurationWithAllParts(self):
    self.Run('P0', 'P0', parts=0)
    self.Run('P0', '-P0', parts=0)
    self.Run('P0', '+P0', parts=0)
    self.Run('P1Y2M3DT4H5M6S', 'P1Y2M3DT4H5M6S', parts=0)
    self.Run('P1Y2M3DT4H5M6S', '+P1Y2M3DT4H5M6S', parts=0)
    self.Run('-P1Y2M3DT4H5M6S', '-P1Y2M3DT4H5M6S', parts=0)
    self.Run('P1Y2M3DT4H5M6.7S', 'P1Y2M3DT4H5M6.7S', parts=0)
    self.Run('P1Y2M3DT4H5M6.7S', '+P1Y2M3DT4H5M6.7S', parts=0)
    self.Run('-P1Y2M3DT4H5M6.7S', '-P1Y2M3DT4H5M6.7S', parts=0)
    self.Run('P1Y2M3DT4H5M6.7S', 'p1y2m3dt4h5m6.7s', parts=0)
    self.Run('-P1Y2M3DT4H5M6.7S', '-p1y2m3dt4h5m6.7s', parts=0)
    self.Run('PT1S', 'P1S', parts=0)
    self.Run('-PT1S', '-P1S', parts=0)
    self.Run('PT1M30S', 'PT1.5M', parts=0)
    self.Run('-PT1M30S', '-PT1.5M', parts=0)
    self.Run('PT1H30M', 'PT1.5H', parts=0)
    self.Run('-PT1H30M', '-PT1.5H', parts=0)
    self.Run('P1M15D', 'P1.5M', parts=0)
    self.Run('-P1M15D', '-P1.5M', parts=0)
    self.Run('P365D', 'P365D', parts=0)
    self.Run('-P365D', '-P365D', parts=0)
    self.Run('PT1S', 'PT1S', parts=0)
    self.Run('PT0.001S', 'PT0.001S', parts=0)

  def testParseDurationFormatDurationWithParts(self):
    self.Run('P1Y7M3DT13H5M6.7S', 'P1Y7M3DT13H5M6.7S', parts=0)
    self.Run('P1Y7M3DT13H5M6.7S', 'P1Y7M3DT13H5M6.7S', parts=7)
    self.Run('P1Y7M3DT13H5M6.7S', 'P1Y7M3DT13H5M6.7S', parts=6)
    self.Run('P1Y7M3DT13H5M', 'P1Y7M3DT13H5M6.7S', parts=5)
    self.Run('P1Y7M3DT13H', 'P1Y7M3DT13H5M6.7S', parts=4)
    self.Run('P1Y7M4D', 'P1Y7M3DT13H5M6.7S', parts=3)
    self.Run('P1Y7M', 'P1Y7M3DT13H5M6.7S', parts=2)
    self.Run('P2Y', 'P1Y7M3DT13H5M6.7S', parts=1)

    self.Run('P7M3DT13H5M6.7S', 'P7M3DT13H5M6.7S', parts=0)
    self.Run('P7M3DT13H5M6.7S', 'P7M3DT13H5M6.7S', parts=7)
    self.Run('P7M3DT13H5M6.7S', 'P7M3DT13H5M6.7S', parts=6)
    self.Run('P7M3DT13H5M6.7S', 'P7M3DT13H5M6.7S', parts=5)
    self.Run('P7M3DT13H5M', 'P7M3DT13H5M6.7S', parts=4)
    self.Run('P7M3DT13H', 'P7M3DT13H5M6.7S', parts=3)
    self.Run('P7M4D', 'P7M3DT13H5M6.7S', parts=2)
    self.Run('P7M', 'P7M3DT13H5M6.7S', parts=1)

    self.Run('P3DT13H5M6.7S', 'P3DT13H5M6.7S', parts=0)
    self.Run('P3DT13H5M6.7S', 'P3DT13H5M6.7S', parts=7)
    self.Run('P3DT13H5M6.7S', 'P3DT13H5M6.7S', parts=6)
    self.Run('P3DT13H5M6.7S', 'P3DT13H5M6.7S', parts=5)
    self.Run('P3DT13H5M6.7S', 'P3DT13H5M6.7S', parts=4)
    self.Run('P3DT13H5M', 'P3DT13H5M6.7S', parts=3)
    self.Run('P3DT13H', 'P3DT13H5M6.7S', parts=2)
    self.Run('P4D', 'P3DT13H5M6.7S', parts=1)

    self.Run('PT13H5M6.7S', 'PT13H5M6.7S', parts=0)
    self.Run('PT13H5M6.7S', 'PT13H5M6.7S', parts=7)
    self.Run('PT13H5M6.7S', 'PT13H5M6.7S', parts=6)
    self.Run('PT13H5M6.7S', 'PT13H5M6.7S', parts=5)
    self.Run('PT13H5M6.7S', 'PT13H5M6.7S', parts=4)
    self.Run('PT13H5M6.7S', 'PT13H5M6.7S', parts=3)
    self.Run('PT13H5M', 'PT13H5M6.7S', parts=2)
    self.Run('PT13H', 'PT13H5M6.7S', parts=1)

    self.Run('PT5M6.7S', 'PT5M6.7S', parts=0)
    self.Run('PT5M6.7S', 'PT5M6.7S', parts=7)
    self.Run('PT5M6.7S', 'PT5M6.7S', parts=6)
    self.Run('PT5M6.7S', 'PT5M6.7S', parts=5)
    self.Run('PT5M6.7S', 'PT5M6.7S', parts=4)
    self.Run('PT5M6.7S', 'PT5M6.7S', parts=3)
    self.Run('PT5M6.7S', 'PT5M6.7S', parts=2)
    self.Run('PT5M', 'PT5M6.7S', parts=1)

    self.Run('PT6.7S', 'PT6.7S', parts=0)
    self.Run('PT6.7S', 'PT6.7S', parts=7)
    self.Run('PT6.7S', 'PT6.7S', parts=6)
    self.Run('PT6.7S', 'PT6.7S', parts=5)
    self.Run('PT6.7S', 'PT6.7S', parts=4)
    self.Run('PT6.7S', 'PT6.7S', parts=3)
    self.Run('PT6.7S', 'PT6.7S', parts=2)
    self.Run('PT6.7S', 'PT6.7S', parts=1)

    self.Run('PT0.7S', 'PT0.7S', parts=0)
    self.Run('PT0.7S', 'PT0.7S', parts=7)
    self.Run('PT0.7S', 'PT0.7S', parts=6)
    self.Run('PT0.7S', 'PT0.7S', parts=5)
    self.Run('PT0.7S', 'PT0.7S', parts=4)
    self.Run('PT0.7S', 'PT0.7S', parts=3)
    self.Run('PT0.7S', 'PT0.7S', parts=2)
    self.Run('PT0.7S', 'PT0.7S', parts=1)

  def testParseDurationFormatDurationWithPartsAndPrecision(self):
    self.Run('P1Y7M3DT13H5M7S', 'P1Y7M3DT13H5M6.7S', parts=0, precision=0)
    self.Run('P1Y7M3DT13H5M7S', 'P1Y7M3DT13H5M6.7S', parts=7, precision=0)
    self.Run('P1Y7M3DT13H5M7S', 'P1Y7M3DT13H5M6.7S', parts=6, precision=0)
    self.Run('P1Y7M3DT13H5M', 'P1Y7M3DT13H5M6.7S', parts=5, precision=0)
    self.Run('P1Y7M3DT13H', 'P1Y7M3DT13H5M6.7S', parts=4, precision=0)
    self.Run('P1Y7M4D', 'P1Y7M3DT13H5M6.7S', parts=3, precision=0)
    self.Run('P1Y7M', 'P1Y7M3DT13H5M6.7S', parts=2, precision=0)
    self.Run('P2Y', 'P1Y7M3DT13H5M6.7S', parts=1, precision=0)

    self.Run('P7M3DT13H5M7S', 'P7M3DT13H5M6.7S', parts=0, precision=0)
    self.Run('P7M3DT13H5M7S', 'P7M3DT13H5M6.7S', parts=7, precision=0)
    self.Run('P7M3DT13H5M7S', 'P7M3DT13H5M6.7S', parts=6, precision=0)
    self.Run('P7M3DT13H5M7S', 'P7M3DT13H5M6.7S', parts=5, precision=0)
    self.Run('P7M3DT13H5M', 'P7M3DT13H5M6.7S', parts=4, precision=0)
    self.Run('P7M3DT13H', 'P7M3DT13H5M6.7S', parts=3, precision=0)
    self.Run('P7M4D', 'P7M3DT13H5M6.7S', parts=2, precision=0)
    self.Run('P7M', 'P7M3DT13H5M6.7S', parts=1, precision=0)

    self.Run('P3DT13H5M7S', 'P3DT13H5M6.7S', parts=0, precision=0)
    self.Run('P3DT13H5M7S', 'P3DT13H5M6.7S', parts=7, precision=0)
    self.Run('P3DT13H5M7S', 'P3DT13H5M6.7S', parts=6, precision=0)
    self.Run('P3DT13H5M7S', 'P3DT13H5M6.7S', parts=5, precision=0)
    self.Run('P3DT13H5M7S', 'P3DT13H5M6.7S', parts=4, precision=0)
    self.Run('P3DT13H5M', 'P3DT13H5M6.7S', parts=3, precision=0)
    self.Run('P3DT13H', 'P3DT13H5M6.7S', parts=2, precision=0)
    self.Run('P4D', 'P3DT13H5M6.7S', parts=1, precision=0)

    self.Run('PT13H5M7S', 'PT13H5M6.7S', parts=0, precision=0)
    self.Run('PT13H5M7S', 'PT13H5M6.7S', parts=7, precision=0)
    self.Run('PT13H5M7S', 'PT13H5M6.7S', parts=6, precision=0)
    self.Run('PT13H5M7S', 'PT13H5M6.7S', parts=5, precision=0)
    self.Run('PT13H5M7S', 'PT13H5M6.7S', parts=4, precision=0)
    self.Run('PT13H5M7S', 'PT13H5M6.7S', parts=3, precision=0)
    self.Run('PT13H5M', 'PT13H5M6.7S', parts=2, precision=0)
    self.Run('PT13H', 'PT13H5M6.7S', parts=1, precision=0)

    self.Run('PT5M7S', 'PT5M6.7S', parts=0, precision=0)
    self.Run('PT5M7S', 'PT5M6.7S', parts=7, precision=0)
    self.Run('PT5M7S', 'PT5M6.7S', parts=6, precision=0)
    self.Run('PT5M7S', 'PT5M6.7S', parts=5, precision=0)
    self.Run('PT5M7S', 'PT5M6.7S', parts=4, precision=0)
    self.Run('PT5M7S', 'PT5M6.7S', parts=3, precision=0)
    self.Run('PT5M7S', 'PT5M6.7S', parts=2, precision=0)
    self.Run('PT6M', 'PT5M46.7S', parts=1, precision=0)

    self.Run('PT7S', 'PT6.7S', parts=0, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=7, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=6, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=5, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=4, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=3, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=2, precision=0)
    self.Run('PT7S', 'PT6.7S', parts=1, precision=0)

    self.Run('PT1S', 'PT0.7S', parts=0, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=7, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=6, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=5, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=4, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=3, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=2, precision=0)
    self.Run('PT1S', 'PT0.7S', parts=1, precision=0)

  def testTimeDeltaFormatDuration(self):
    self.Run('P0',
             '2016-01-19T10:51:11.000000Z',
             end='2016-01-19T10:51:11.000000Z')
    self.Run('PT8H0.941S',
             '2016-01-19T10:51:11.000000Z',
             end='2016-01-19T10:51:11.941000-0800')
    self.Run('-PT8H0.941S',
             '2016-01-19T10:51:11.941000-0800',
             end='2016-01-19T10:51:11.000000Z')
    self.Run('PT1.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T10:51:13.000149-00:00')
    self.Run('PT0.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T10:51:12.000149Z')
    self.Run('PT2M3.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T10:53:15.000149Z')
    self.Run('PT4H2M0.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T14:53:12.000149Z')
    self.Run('PT28H2M0.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-20T14:53:12.000149Z')
    self.Run('PT5884H2M0.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-09-20T14:53:12.000149Z')
    self.Run('PT23404H2M0.059S',
             '2014-01-19T10:51:11.941000Z',
             end='2016-09-20T14:53:12.000149Z')
    self.Run('PT648H',
             '2016-02-01T00:00:00Z',
             end='2016-02-28T00:00:00Z')
    self.Run('PT672H',
             '2016-02-01T00:00:00Z',
             end='2016-02-29T00:00:00Z')
    self.Run('PT696H',
             '2016-02-01T00:00:00Z',
             end='2016-03-01T00:00:00Z')
    self.Run('PT648H',
             '2015-02-01T00:00:00Z',
             end='2015-02-28T00:00:00Z')
    self.Run('PT672H',
             '2015-02-01T00:00:00Z',
             end='2015-03-01T00:00:00Z')
    self.Run('PT8784H',
             '2016-02-14T00:00:00Z',
             end='2017-02-14T00:00:00Z')
    self.Run('-PT8784H',
             '2017-02-14T00:00:00Z',
             end='2016-02-14T00:00:00Z')
    self.Run('PT0.11S',
             '2016-11-11T11:11:11.00Z',
             end='2016-11-11T11:11:11.11Z')
    self.Run('-PT0.11S',
             '2016-11-11T11:11:11.11Z',
             end='2016-11-11T11:11:11.00Z')
    self.Run('PT4H2M',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T14:53:12.000149Z',
             precision=0)

  def testTimeDeltaFormatCalendarDuration(self):
    self.Run('P0',
             '2016-01-19T10:51:11.000000Z',
             end='2016-01-19T10:51:11.000000Z',
             calendar=True)
    self.Run('PT8H0.941S',
             '2016-01-19T10:51:11.000000Z',
             end='2016-01-19T10:51:11.941000-0800',
             calendar=True)
    self.Run('-PT8H0.941S',
             '2016-01-19T10:51:11.941000-0800',
             end='2016-01-19T10:51:11.000000Z',
             calendar=True)
    self.Run('PT1.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T10:51:13.000149-00:00',
             calendar=True)
    self.Run('PT0.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T10:51:12.000149Z',
             calendar=True)
    self.Run('PT2M3.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T10:53:15.000149Z',
             calendar=True)
    self.Run('PT4H2M0.059S',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T14:53:12.000149Z',
             calendar=True)
    self.Run('P1DT4H2M',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-20T14:53:12.000149Z',
             calendar=True)
    self.Run('P245DT4H2M',
             '2016-01-19T10:51:11.941000Z',
             end='2016-09-20T14:53:12.000149Z',
             calendar=True)
    self.Run('P2Y244D',
             '2014-01-19T10:51:11.941000Z',
             end='2016-09-20T14:53:12.000149Z',
             calendar=True)
    self.Run('P27D',
             '2016-02-01T00:00:00Z',
             end='2016-02-28T00:00:00Z',
             calendar=True)
    self.Run('P28D',
             '2016-02-01T00:00:00Z',
             end='2016-02-29T00:00:00Z',
             calendar=True)
    self.Run('P29D',
             '2016-02-01T00:00:00Z',
             end='2016-03-01T00:00:00Z',
             calendar=True)
    self.Run('P27D',
             '2015-02-01T00:00:00Z',
             end='2015-02-28T00:00:00Z',
             calendar=True)
    self.Run('P28D',
             '2015-02-01T00:00:00Z',
             end='2015-03-01T00:00:00Z',
             calendar=True)
    self.Run('P1Y',
             '2016-02-14T00:00:00Z',
             end='2017-02-14T00:00:00Z',
             calendar=True)
    self.Run('-P1Y',
             '2017-02-14T00:00:00Z',
             end='2016-02-14T00:00:00Z',
             calendar=True)
    self.Run('PT0.11S',
             '2016-11-11T11:11:11.00Z',
             end='2016-11-11T11:11:11.11Z',
             calendar=True)
    self.Run('-PT0.11S',
             '2016-11-11T11:11:11.11Z',
             end='2016-11-11T11:11:11.00Z',
             calendar=True)
    self.Run('PT4H2M',
             '2016-01-19T10:51:11.941000Z',
             end='2016-01-19T14:53:12.000149Z',
             precision=0,
             calendar=True)

  def testParseDurationAddTimeDeltaFormatDuration(self):
    self.Run('P0',
             'P0',
             relative='2016-01-19T10:51:11.000000Z',
             end='2016-01-19T10:51:11.000000Z')
    self.Run('PT16H0.941S',
             'PT8H0.941S',
             relative='2016-01-19T10:51:11.000000Z',
             end='2016-01-19T10:51:11.941000-0800')
    self.Run('-PT16H0.941S',
             '-PT8H0.941S',
             relative='2016-01-19T10:51:11.941000-0800',
             end='2016-01-19T10:51:11.000000Z')
    self.Run('P245DT6H3M',
             'P123DT2H1M',
             relative='2016-01-19T10:51:11.941000Z',
             end='2016-05-20T14:53:12.000149Z')
    self.Run('P5Y123D',
             'P2Y244D',
             relative='2014-01-19T10:51:11.941000Z',
             end='2016-09-20T14:53:12.000149Z')

  def testParseDurationAddDurationToDateTime(self):
    self.Run('2016-01-19T10:51:11.000Z',
             'P0',
             relative='2016-01-19T10:51:11.000000Z')
    self.Run('2016-01-19T10:51:11.000Z',
             '-P0',
             relative='2016-01-19T10:51:11.000000Z')

    self.Run('2016-01-19T18:51:12.000Z',
             'PT8H1S',
             relative='2016-01-19T10:51:11.000000Z')
    self.Run('2016-01-19T10:51:11.000Z',
             '-PT8H1S',
             relative='2016-01-19T18:51:12.000000Z')

    self.Run('2016-01-21T02:51:10.000Z',
             'P1DT15H59M59S',
             relative='2016-01-19T10:51:11.000000Z')
    self.Run('2016-01-19T10:51:11.000Z',
             '-P1DT15H59M59S',
             relative='2016-01-21T02:51:10.000000Z')

    self.Run('2016-01-19T10:51:12.999Z',
             'PT1.059S',
             relative='2016-01-19T10:51:11.941000Z')
    self.Run('2016-01-19T10:51:11.940Z',
             '-PT1.059S',
             relative='2016-01-19T10:51:12.999000Z')

    self.Run('2016-01-19T10:51:12.000-05:00',
             'PT0.059S',
             relative='2016-01-19T10:51:11.941000 EST')
    self.Run('2016-01-19T10:51:12.940-05:00',
             '-PT0.059S',
             relative='2016-01-19T10:51:12.999000 EST')

    self.Run('2016-01-19T10:53:15.000Z',
             'PT2M3.059S',
             relative='2016-01-19T10:51:11.941000Z')
    self.Run('2016-01-19T10:51:11.941Z',
             '-PT2M3.059S',
             relative='2016-01-19T10:53:15.000000Z')

    self.Run('2016-01-19T14:53:11.941Z',
             'PT4H2M',
             relative='2016-01-19T10:51:11.941000Z')
    self.Run('2016-01-19T10:51:11.941Z',
             '-PT4H2M',
             relative='2016-01-19T14:53:11.941000Z')

    self.Run('2016-01-20T14:53:11.941Z',
             'P1DT4H2M',
             relative='2016-01-19T10:51:11.941000Z')
    self.Run('2016-01-19T10:51:11.941Z',
             '-P1DT4H2M',
             relative='2016-01-20T14:53:11.941000Z')

    self.Run('2016-09-20T14:53:11.941Z',
             'P245DT4H2M',
             relative='2016-01-19T10:51:11.941000Z')
    self.Run('2016-01-19T10:51:11.941Z',
             '-P245DT4H2M',
             relative='2016-09-20T14:53:11.941000Z')

    self.Run('2016-09-20T14:53:11.941Z',
             'P2Y245DT4H2M',
             relative='2014-01-19T10:51:11.941000Z')
    self.Run('2014-01-18T10:51:11.941Z',
             '-P2Y245DT4H2M',
             relative='2016-09-20T14:53:11.941000Z')

    self.Run('2017-03-04T00:00:00.000Z',
             'P8M',
             relative='2016-07-04T00:00:00.000000Z')
    self.Run('2016-07-04T00:00:00.000Z',
             '-P8M',
             relative='2017-03-04T00:00:00.000000Z')

    self.Run('2001-04-17T19:23:17.300Z',
             'P1Y3M5DT7H10M3.3S',
             relative='2000-01-12T12:13:14.000Z')
    self.Run('2000-01-12T12:13:14.000Z',
             '-P1Y3M5DT7H10M3.3S',
             relative='2001-04-17T19:23:17.3Z')

    self.Run('2000-01-01T00:00:00.000Z',
             'P3M',
             relative='1999-10-01T00:00:00.000Z')
    self.Run('1999-10-01T00:00:00.000Z',
             '-P3M',
             relative='2000-01-01T00:00:00.000Z')

    self.Run('2000-01-13T09:00:00.000Z',
             'P33H',
             relative='2000-01-12T00:00:00.000Z')
    self.Run('2000-01-12T00:00:00.000Z',
             '-P33H',
             relative='2000-01-13T09:00:00.000Z')

  def testDurationBoundaries(self):
    self.Run('2016-01-01T00:00:00.000Z',
             'PT1S',
             relative='2015-12-31T23:59:59Z')
    self.Run('2015-12-31T23:59:59.000Z',
             '-PT1S',
             relative='2016-01-01T00:00:00.000Z')

    self.Run('2016-01-01T00:00:00.000Z',
             'PT0.001S',
             relative='2015-12-31T23:59:59.999Z')
    self.Run('2015-12-31T23:59:59.999Z',
             '-PT0.001S',
             relative='2016-01-01T00:00:00.000Z')

    self.Run('2016-02-29T00:00:00.000Z',
             'P1D',
             relative='2016-02-28T00:00:00Z')
    self.Run('2016-02-28T00:00:00.000Z',
             '-P1D',
             relative='2016-02-29T00:00:00Z')

    self.Run('2016-03-01T00:00:00.000Z',
             'P1D',
             relative='2016-02-29T00:00:00.000Z')
    self.Run('2016-02-29T00:00:00.000Z',
             '-P1D',
             relative='2016-03-01T00:00:00Z')

    self.Run('2016-03-05T00:00:00.000Z',
             'P20D',
             relative='2016-02-14T00:00:00Z')
    self.Run('2016-02-14T00:00:00.000Z',
             '-P20D',
             relative='2016-03-05T00:00:00.000Z')

    self.Run('2017-02-14T00:00:00.000Z',
             'P366D',
             relative='2016-02-14T00:00:00Z')
    self.Run('2016-02-14T00:00:00.000Z',
             '-P366D',
             relative='2017-02-14T00:00:00.000Z')

    self.Run('2017-02-14T00:00:00.000Z',
             'P1Y',
             relative='2016-02-14T00:00:00Z')
    self.Run('2016-02-14T00:00:00.000Z',
             '-P1Y',
             relative='2017-02-14T00:00:00.000Z')

    self.Run('2016-02-14T00:00:00.000Z',
             'P365D',
             relative='2015-02-14T00:00:00Z')
    self.Run('2015-02-14T00:00:00.000Z',
             '-P365D',
             relative='2016-02-14T00:00:00.000Z')

    self.Run('2016-02-14T00:00:00.000Z',
             'P1Y',
             relative='2015-02-14T00:00:00Z')
    self.Run('2015-02-14T00:00:00.000Z',
             '-P1Y',
             relative='2016-02-14T00:00:00.000Z')

  def testParseDurationExceptions(self):
    self.Run(None, '+-PT0S', exception=times.DurationSyntaxError)
    self.Run(None, 'P1MT1DT1M', exception=times.DurationSyntaxError)
    self.Run(None, 'P0X', exception=times.DurationSyntaxError)
    self.Run(None, 'PT0X', exception=times.DurationSyntaxError)
    self.Run(None, 'P1', exception=times.DurationSyntaxError)


class DurationForJsonTest(test_case.TestCase, parameterized.TestCase):

  @parameterized.parameters(
      (iso_duration.Duration(seconds=10), '10s'),
      (iso_duration.Duration(hours=1), '3600s'),
      (iso_duration.Duration(seconds=1, microseconds=5), '1.000005s'),
      (iso_duration.Duration(minutes=1, microseconds=123456), '60.123456s'),
  )
  def testFormatDurationForJson(self, duration, expected):
    self.assertEquals(times.FormatDurationForJson(duration), expected)


if __name__ == '__main__':
  test_case.main()
