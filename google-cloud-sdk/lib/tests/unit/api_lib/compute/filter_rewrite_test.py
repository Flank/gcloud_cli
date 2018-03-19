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

"""Unit tests for the compute filter expression rewrite module."""

import re

from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.api_lib.compute import transforms as compute_transforms
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_transform as core_transforms
from tests.lib import subtests
from tests.lib import test_case


class MockDisplayInfo(object):

  def __init__(self, transforms=None, aliases=None):
    self.transforms = transforms
    self.aliases = aliases


class MockArgs(object):

  def __init__(self, args):
    for name, value in args.iteritems():
      setattr(self, name, value)

  def GetDisplayInfo(self):
    symbols = {}
    symbols.update(compute_transforms.GetTransforms())
    symbols.update(core_transforms.GetTransforms())
    return MockDisplayInfo(transforms=symbols)


class FilterMatchComputeConvertTest(subtests.Base):

  def RunSubTest(self, converter, pattern, matches, subject, wordmatch=False):
    # Do the conversion.
    if wordmatch:
      converted = converter(pattern, wordmatch=True)
    else:
      converted = converter(pattern)

    # Verify that the converted pattern matches the subject using the compute
    # backend definition of "match".  NOTICE: The initial and trailing " must be
    # stripped before matching.

    match = re.match('(' + converted[1:-1] + ')', subject)
    if match:
      # This is the entire subject string matches check.
      actual = match.group(1) == subject
    else:
      actual = False
    if matches != actual:
      self.fail('Converted pattern should{sense} match '
                'group=[{group}] subject=[{subject}].'.format(
                    sense='' if matches else ' not',
                    group=match.group(1) if match else None,
                    subject=subject))

    # Finally return the subtest result.
    return converted

  def testConvertEQPatternToFullMatch(self):

    def T(expected, pattern, matches, subject):
      self.Run(expected, filter_rewrite.ConvertEQPatternToFullMatch,
               pattern, matches, subject, depth=2)

    T(r'".*\bname\b.*"', 'name', True, 'name')
    T(r'".*\bname\b.*"', 'name', False, 'nametail')
    T(r'".*\bname\b.*"', 'name', True, 'name-tail')
    T(r'".*\bname\b.*"', 'name', False, 'headname')
    T(r'".*\bname\b.*"', 'name', True, 'head-name')
    T(r'".*\bname\b.*"', 'name', False, 'headnametail')
    T(r'".*\bname\b.*"', 'name', True, 'head-name-tail')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/name/suffix')
    T(r'".*\bname\b.*"', 'name', False, 'prefix/nametail/suffix')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/name-tail/suffix')
    T(r'".*\bname\b.*"', 'name', False, 'prefix/headname/suffix')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/head-name/suffix')
    T(r'".*\bname\b.*"', 'name', False, 'prefix/headnametail/suffix')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/head-name-tail/suffix')

  def testConvertHASPatternToFullMatch(self):

    def T(expected, pattern, matches, subject):
      self.Run(expected, filter_rewrite.ConvertHASPatternToFullMatch,
               pattern, matches, subject, depth=2)

    T(r'".*\bname\b.*"', 'name', True, 'name')
    T(r'".*\bname\b.*"', 'name', False, 'nametail')
    T(r'".*\bname\b.*"', 'name', True, 'name-tail')
    T(r'".*\bname\b.*"', 'name', False, 'headname')
    T(r'".*\bname\b.*"', 'name', True, 'head-name')
    T(r'".*\bname\b.*"', 'name', False, 'headnametail')
    T(r'".*\bname\b.*"', 'name', True, 'head-name-tail')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/name/suffix')
    T(r'".*\bname\b.*"', 'name', False, 'prefix/nametail/suffix')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/name-tail/suffix')
    T(r'".*\bname\b.*"', 'name', False, 'prefix/headname/suffix')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/head-name/suffix')
    T(r'".*\bname\b.*"', 'name', False, 'prefix/headnametail/suffix')
    T(r'".*\bname\b.*"', 'name', True, 'prefix/head-name-tail/suffix')

    T(r'".*\bname.*"', 'name*', True, 'name')
    T(r'".*\bname.*"', 'name*', True, 'nametail')
    T(r'".*\bname.*"', 'name*', True, 'name-tail')
    T(r'".*\bname.*"', 'name*', False, 'headname')
    T(r'".*\bname.*"', 'name*', True, 'head-name')
    T(r'".*\bname.*"', 'name*', False, 'headnametail')
    T(r'".*\bname.*"', 'name*', True, 'head-name-tail')
    T(r'".*\bname.*"', 'name*', True, 'prefix/name/suffix')
    T(r'".*\bname.*"', 'name*', True, 'prefix/nametail/suffix')
    T(r'".*\bname.*"', 'name*', True, 'prefix/name-tail/suffix')
    T(r'".*\bname.*"', 'name*', False, 'prefix/headname/suffix')
    T(r'".*\bname.*"', 'name*', True, 'prefix/head-name/suffix')
    T(r'".*\bname.*"', 'name*', False, 'prefix/headnametail/suffix')
    T(r'".*\bname.*"', 'name*', True, 'prefix/head-name-tail/suffix')

  def testConvertREPatternToFullMatch(self):

    def T(expected, pattern, matches, subject):
      self.Run(expected, filter_rewrite.ConvertREPatternToFullMatch,
               pattern, matches, subject, depth=2)

    T(r'".*(name).*"', 'name', True, 'name')
    T(r'".*(name).*"', 'name', True, 'nametail')
    T(r'".*(name).*"', 'name', True, 'name-tail')
    T(r'".*(name).*"', 'name', True, 'headname')
    T(r'".*(name).*"', 'name', True, 'head-name')
    T(r'".*(name).*"', 'name', True, 'headnametail')
    T(r'".*(name).*"', 'name', True, 'head-name-tail')
    T(r'".*(name).*"', 'name', True, 'prefix/name/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/nametail/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/name-tail/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/headname/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/head-name/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/headnametail/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/head-name-tail/suffix')

    T(r'".*(^name).*"', '^name', True, 'name')
    T(r'".*(^name).*"', '^name', True, 'nametail')
    T(r'".*(^name).*"', '^name', True, 'name-tail')
    T(r'".*(^name).*"', '^name', False, 'headname')
    T(r'".*(^name).*"', '^name', False, 'head-name')
    T(r'".*(^name).*"', '^name', False, 'headnametail')
    T(r'".*(^name).*"', '^name', False, 'head-name-tail')
    T(r'".*(^name).*"', '^name', False, 'prefix/name/suffix')
    T(r'".*(^name).*"', '^name', False, 'prefix/nametail/suffix')
    T(r'".*(^name).*"', '^name', False, 'prefix/name-tail/suffix')
    T(r'".*(^name).*"', '^name', False, 'prefix/headname/suffix')
    T(r'".*(^name).*"', '^name', False, 'prefix/head-name/suffix')
    T(r'".*(^name).*"', '^name', False, 'prefix/headnametail/suffix')
    T(r'".*(^name).*"', '^name', False, 'prefix/head-name-tail/suffix')

    T(r'".*(^name$).*"', '^name$', True, 'name')
    T(r'".*(^name$).*"', '^name$', False, 'nametail')
    T(r'".*(^name$).*"', '^name$', False, 'name-tail')
    T(r'".*(^name$).*"', '^name$', False, 'headname')
    T(r'".*(^name$).*"', '^name$', False, 'head-name')
    T(r'".*(^name$).*"', '^name$', False, 'headnametail')
    T(r'".*(^name$).*"', '^name$', False, 'head-name-tail')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/name/suffix')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/nametail/suffix')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/name-tail/suffix')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/headname/suffix')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/head-name/suffix')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/headnametail/suffix')
    T(r'".*(^name$).*"', '^name$', False, 'prefix/head-name-tail/suffix')

  def testConvertREPatternToFullMatchWIthWordmatch(self):

    def T(expected, pattern, matches, subject):
      self.Run(expected, filter_rewrite.ConvertREPatternToFullMatch,
               pattern, matches, subject, wordmatch=True, depth=2)

    T(r'".*(name).*"', 'name', True, 'name')
    T(r'".*(name).*"', 'name', True, 'nametail')
    T(r'".*(name).*"', 'name', True, 'name-tail')
    T(r'".*(name).*"', 'name', True, 'headname')
    T(r'".*(name).*"', 'name', True, 'head-name')
    T(r'".*(name).*"', 'name', True, 'headnametail')
    T(r'".*(name).*"', 'name', True, 'head-name-tail')
    T(r'".*(name).*"', 'name', True, 'prefix/name/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/nametail/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/name-tail/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/headname/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/head-name/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/headnametail/suffix')
    T(r'".*(name).*"', 'name', True, 'prefix/head-name-tail/suffix')

    T(r'".*(\bname).*"', '^name', True, 'name')
    T(r'".*(\bname).*"', '^name', True, 'nametail')
    T(r'".*(\bname).*"', '^name', True, 'name-tail')
    T(r'".*(\bname).*"', '^name', False, 'headname')
    T(r'".*(\bname).*"', '^name', True, 'head-name')
    T(r'".*(\bname).*"', '^name', False, 'headnametail')
    T(r'".*(\bname).*"', '^name', True, 'head-name-tail')
    T(r'".*(\bname).*"', '^name', True, 'prefix/name/suffix')
    T(r'".*(\bname).*"', '^name', True, 'prefix/nametail/suffix')
    T(r'".*(\bname).*"', '^name', True, 'prefix/name-tail/suffix')
    T(r'".*(\bname).*"', '^name', False, 'prefix/headname/suffix')
    T(r'".*(\bname).*"', '^name', True, 'prefix/head-name/suffix')
    T(r'".*(\bname).*"', '^name', False, 'prefix/headnametail/suffix')
    T(r'".*(\bname).*"', '^name', True, 'prefix/head-name-tail/suffix')

    T(r'".*(\bname\b).*"', '^name$', True, 'name')
    T(r'".*(\bname\b).*"', '^name$', False, 'nametail')
    T(r'".*(\bname\b).*"', '^name$', True, 'name-tail')
    T(r'".*(\bname\b).*"', '^name$', False, 'headname')
    T(r'".*(\bname\b).*"', '^name$', True, 'head-name')
    T(r'".*(\bname\b).*"', '^name$', False, 'headnametail')
    T(r'".*(\bname\b).*"', '^name$', True, 'head-name-tail')
    T(r'".*(\bname\b).*"', '^name$', True, 'prefix/name/suffix')
    T(r'".*(\bname\b).*"', '^name$', False, 'prefix/nametail/suffix')
    T(r'".*(\bname\b).*"', '^name$', True, 'prefix/name-tail/suffix')
    T(r'".*(\bname\b).*"', '^name$', False, 'prefix/headname/suffix')
    T(r'".*(\bname\b).*"', '^name$', True, 'prefix/head-name/suffix')
    T(r'".*(\bname\b).*"', '^name$', False, 'prefix/headnametail/suffix')
    T(r'".*(\bname\b).*"', '^name$', True, 'prefix/head-name-tail/suffix')

    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'name')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', False, 'nametail')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'name-tail')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', False, 'headname')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'head-name')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', False, 'headnametail')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'head-name-tail')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'prefix/name/suffix')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', False, 'prefix/nametail/suffix')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'prefix/name-tail/suffix')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', False, 'prefix/headname/suffix')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'prefix/head-name/suffix')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', False, 'prefix/headnametail/suffix')
    T(r'".*(\bnam[^x]\b).*"', '^nam[^x]$', True, 'prefix/head-name-tail/suffix')

    T(r'".*(\bfoo\^bar\b).*"', r'^foo\^bar$', True, 'foo^bar')
    T(r'".*(\bfoo\$bar\b).*"', r'^foo\$bar$', True, 'foo$bar')
    T(r'".*(\bfoo[$]bar\b).*"', r'^foo[$]bar$', True, 'foo$bar')

    T(r'".*(\bfoo\"bar\b).*"', r'^foo"bar$', True, 'foo"bar')
    T(r'".*(\bfoo[\"]bar\b).*"', r'^foo["]bar$', True, 'foo"bar')

    T(r'".*(\bnam[^]x]\b).*"', '^nam[^]x]$', True, 'name')
    T(r'".*(\bnam[^]e]\b).*"', '^nam[^]e]$', False, 'name')
    T(r'".*(\bnam[]e]\b).*"', '^nam[]e]$', True, 'name')

    T(r'".*(\bna[^xz]e\b).*"', '^na[^xz]e$', True, 'name')
    T(r'".*(\bna[^mx]e\b).*"', '^na[^mx]e$', False, 'name')
    T(r'".*(\bna[^xm]e\b).*"', '^na[^xm]e$', False, 'name')
    T(r'".*(\bna[mx]e\b).*"', '^na[mx]e$', True, 'name')
    T(r'".*(\bna[xm]e\b).*"', '^na[xm]e$', True, 'name')


class ComputeFilterRewriteTest(subtests.Base):

  def RunSubTest(self, expression):
    args = MockArgs({'filter': expression})
    return flags.RewriteFilter(args)

  def testResourceFilterRewriter(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    # args.filter empty or not set.
    T((None, None),
      None)
    T((None, None),
      '')
    T((None, None),
      '  ')

    T((None, 'name eq true'),
      'name=true')
    T((None, 'name eq true'),
      'name=True')
    T((None, 'name eq true'),
      'name=TRUE')
    T((None, 'name ne false'),
      'name!=false')
    T((None, 'name ne false'),
      'name!=False')
    T((None, 'name ne false'),
      'name!=FALSE')

    T((None, r'name eq ".*(foo.*bar).*"'),
      'name~foo.*bar')
    T((None, r'name ne ".*(foo.*bar).*"'),
      '-name~foo.*bar')
    T((None, r'name ne ".*(foo.*bar).*"'),
      'NOT name~foo.*bar')

    T((None, r'name ne ".*(foo.*bar).*"'),
      'name!~foo.*bar')
    T((None, r'name eq ".*(foo.*bar).*"'),
      '-name!~foo.*bar')
    T((None, r'name eq ".*(foo.*bar).*"'),
      'NOT name!~foo.*bar')

    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      'name=foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      '-name=foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      'NOT name=foo*bar')

    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      'name!=foo*bar')
    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      '-name!=foo*bar')
    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      'NOT name!=foo*bar')

    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      'name:foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      '-name:foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      'NOT name:foo*bar')

    T((None, r'name eq ".*(1.2).*"'),
      'name~1.2')
    T((None, r'name ne ".*(1.2).*"'),
      '-name~1.2')
    T((None, r'name ne ".*(1.2).*"'),
      'NOT name~1.2')

    T((None, r'name ne ".*(1.2).*"'),
      'name!~1.2')
    T((None, r'name eq ".*(1.2).*"'),
      '-name!~1.2')
    T((None, r'name eq ".*(1.2).*"'),
      'NOT name!~1.2')

    T((None, 'name eq 1.2'),
      'name=1.2')
    T((None, 'name ne 1.2'),
      '-name=1.2')
    T((None, 'name ne 1.2'),
      'NOT name=1.2')

    T((None, 'name ne 1.2'),
      'name!=1.2')
    T((None, 'name eq 1.2'),
      '-name!=1.2')
    T((None, 'name eq 1.2'),
      'NOT name!=1.2')

    T((None, 'name eq 1.2'),
      'name:1.2')
    T((None, 'name ne 1.2'),
      '-name:1.2')
    T((None, 'name ne 1.2'),
      'NOT name:1.2')

    T((None, r'name eq ".*(123).*"'),
      'name~123')
    T((None, r'name ne ".*(123).*"'),
      '-name~123')
    T((None, r'name ne ".*(123).*"'),
      'NOT name~123')

    T((None, r'name ne ".*(123).*"'),
      'name!~123')
    T((None, r'name eq ".*(123).*"'),
      '-name!~123')
    T((None, r'name eq ".*(123).*"'),
      'NOT name!~123')

    T((None, 'name eq 123'),
      'name=123')
    T((None, 'name ne 123'),
      '-name=123')
    T((None, 'name ne 123'),
      'NOT name=123')

    T((None, 'name ne 123'),
      'name!=123')
    T((None, 'name eq 123'),
      '-name!=123')
    T((None, 'name eq 123'),
      'NOT name!=123')

    T((None, r'name ne ".*\ba\ eq\ b\b.*"'),
      '-name="a eq b"')
    T((None, r'name ne ".*\ba\ eq\ b\b.*"'),
      'NOT name="a eq b"')
    T((None, r'name eq ".*\ba\ eq\ b\b.*"'),
      'NOT -name="a eq b"')

    T((None, r'name ne ".*\ba\ ne\ b\b.*"'),
      '-name="a ne b"')
    T((None, r'name ne ".*\ba\ ne\ b\b.*"'),
      'NOT name="a ne b"')
    T((None, r'name eq ".*\ba\ ne\ b\b.*"'),
      'NOT -name="a ne b"')

    T((None, r'name eq ".*\ba\ eq\ b\b.*"'),
      '-name!="a eq b"')
    T((None, r'name eq ".*\ba\ eq\ b\b.*"'),
      'NOT name!="a eq b"')
    T((None, r'name ne ".*\ba\ eq\ b\b.*"'),
      'NOT -name!="a eq b"')

    T((None, r'name eq ".*\ba\ ne\ b\b.*"'),
      '-name!="a ne b"')
    T((None, r'name eq ".*\ba\ ne\ b\b.*"'),
      'NOT name!="a ne b"')
    T((None, r'name ne ".*\ba\ ne\ b\b.*"'),
      'NOT -name!="a ne b"')

    T((None, 'name eq 123'),
      'name:123')
    T((None, 'name ne 123'),
      '-name:123')
    T((None, 'name ne 123'),
      'NOT name:123')

    # anomaly -- should be (None, ...)
    T(('NOT NOT name=123', 'name eq 123'),
      'NOT NOT name=123')
    T((None, 'name eq 123'),
      'NOT -name=123')

    T((None, r'name eq ".*(foo\*).*"'),
      r'name~foo\*')
    T((None, r'name eq ".*\bfoo\*\b.*"'),
      r'name=foo*')
    T((None, r'name eq ".*\bfoo.*"'),
      r'name:foo*')

    T((None, r'name eq ".*(foo.*\"bar).*"'),
      r'name~foo.*\"bar')
    T((None, r'name eq ".*\bfoo\*\"bar\b.*"'),
      r'name=foo*\"bar')
    T((None, r'name eq ".*\bfoo\*\"bar\b.*"'),
      r'name:foo*\"bar')

    T((None, r'(name eq ".*\bfoo\b.*")(disk eq ".*\bbar\b.*")'),
      'name:foo disk:bar')
    T((None, r'(name ne ".*\bfoo\b.*")(disk eq ".*\bbar\b.*")'),
      'NOT name:foo disk:bar')
    T((None, r'(name eq ".*\bfoo\b.*")(disk ne ".*\bbar\b.*")'),
      'name:foo NOT disk:bar')
    T((None, r'(name ne ".*\bfoo\b.*")(disk ne ".*\bbar\b.*")'),
      'NOT name:foo NOT disk:bar')

    T((None, '(name eq 1.2)(disk eq 9.8)'),
      'name:1.2 disk:9.8')
    T((None, '(name ne 1.2)(disk eq 9.8)'),
      'NOT name:1.2 disk:9.8')
    T((None, '(name eq 1.2)(disk ne 9.8)'),
      'name:1.2 NOT disk:9.8')
    T((None, '(name ne 1.2)(disk ne 9.8)'),
      'NOT name:1.2 NOT disk:9.8')

    T((None, '(name eq 123)(disk eq 987)'),
      'name=123 disk=987')
    T((None, '(name ne 123)(disk eq 987)'),
      'NOT name=123 disk=987')
    T((None, '(name eq 123)(disk ne 987)'),
      'name=123 NOT disk=987')
    T((None, '(name ne 123)(disk ne 987)'),
      'NOT name=123 NOT disk=987')

    # Implicit and explicit AND supported.

    T((None, '(name eq 123)((disk eq 987)(foo eq ".*\\bup\\b.*"))'),
      'name=123 disk=987 foo=up')
    T((None, '(name eq 123)((disk eq 987)(foo eq ".*\\bup\\b.*"))'),
      'name=123 disk=987 AND foo=up')

    # OR not supported.

    T(('(name=123 AND disk=987) OR foo=up', None),
      '(name=123 AND disk=987) OR foo=up')
    T(('(name=123 OR disk=987) AND foo=up', 'foo eq ".*\\bup\\b.*"'),
      '(name=123 OR disk=987) AND foo=up')
    T(('name=123 (disk=987 OR foo=up)', 'name eq 123'),
      'name=123 (disk=987 OR foo=up)')

    # Inequalties not supported.

    T(('name<foo*bar', None),
      'name<foo*bar')
    T(('name<=foo*bar', None),
      'name<=foo*bar')
    T(('name>=foo*bar', None),
      'name>=foo*bar')
    T(('name>foo*bar', None),
      'name>foo*bar')

    T(('name=(abc, xyz)', None),
      'name=(abc, xyz)')
    T(('NOT (name=abc disk=123)', None),
      'NOT (name=abc disk=123)')

    # basename() is a core transform.
    T(('zone.basename():us-central1-b', None),
      'zone.basename():us-central1-b')

    # location() is a compute transform.
    T(('foo.location():us-central1', None),
      'foo.location():us-central1')

    # unknown() is not a transform.
    T(('region.unknown():x', None),
      'region.unknown():x')

    # region & zone workarounds to handle matching on full URI.

    T((None, r'other eq ".*\bus\-central1\-b\b.*"'), 'other:us-central1-b')
    T((None, r'region eq ".*\bus\-central1\-b\b.*"'), 'region:us-central1-b')
    T((None, r'zone eq ".*\bus\-central1\-b\b.*"'), 'zone:us-central1-b')

    T((None, r'other eq ".*\bus\-central1\-b\b.*"'), 'other=us-central1-b')
    T((None, r'region eq ".*\bus\-central1\-b\b.*"'), 'region=us-central1-b')
    T((None, r'zone eq ".*\bus\-central1\-b\b.*"'), 'zone=us-central1-b')

    T((None, r'other ne ".*\bus\-central1\-b\b.*"'), 'other!=us-central1-b')
    T((None, r'region ne ".*\bus\-central1\-b\b.*"'), 'region!=us-central1-b')
    T((None, r'zone ne ".*\bus\-central1\-b\b.*"'), 'zone!=us-central1-b')

    T((None, r'other eq ".*(us-central1-b).*"'), 'other~us-central1-b')
    T((None, r'region eq ".*(us-central1-b).*"'), 'region~us-central1-b')
    T((None, r'zone eq ".*(us-central1-b).*"'), 'zone~us-central1-b')

    T((None, r'other eq ".*(^us-central1-b).*"'), 'other~^us-central1-b')
    T((None, r'region eq ".*(\bus-central1-b).*"'), 'region~^us-central1-b')
    T((None, r'zone eq ".*(\bus-central1-b).*"'), 'zone~^us-central1-b')

    T((None, r'other eq ".*(^us-central1-b$).*"'), 'other~^us-central1-b$')
    T((None, r'region eq ".*(\bus-central1-b\b).*"'), 'region~^us-central1-b$')
    T((None, r'zone eq ".*(\bus-central1-b\b).*"'), 'zone~^us-central1-b$')

    T((None, r'other ne ".*(^us-central1-b).*"'), 'other!~^us-central1-b')
    T((None, r'region ne ".*(\bus-central1-b).*"'), 'region!~^us-central1-b')
    T((None, r'zone ne ".*(\bus-central1-b).*"'), 'zone!~^us-central1-b')

    T((None, r'other ne ".*(^us-central1-b$).*"'), 'other!~^us-central1-b$')
    T((None, r'region ne ".*(\bus-central1-b\b).*"'), 'region!~^us-central1-b$')
    T((None, r'zone ne ".*(\bus-central1-b\b).*"'), 'zone!~^us-central1-b$')

    # absent the resource proto message, enum-like operands are not matchable

    T((None, 'direction eq INGRESS'), 'direction:INGRESS')
    T((None, 'direction eq INGRESS'), 'direction=INGRESS')
    T((None, 'direction ne INGRESS'), 'direction!=INGRESS')

    T((None, 'direction ne INGRESS'), 'NOT direction:INGRESS')
    T((None, 'direction ne INGRESS'), 'NOT direction=INGRESS')
    T((None, 'direction eq INGRESS'), 'NOT direction!=INGRESS')

    T((None, 'direction ne INGRESS'), '-direction:INGRESS')
    T((None, 'direction ne INGRESS'), '-direction=INGRESS')
    T((None, 'direction eq INGRESS'), '-direction!=INGRESS')


class ComputeFilterRewriteResourceTest(subtests.Base):

  def RunSubTest(self, expression, message, frontend_fields):
    args = MockArgs({'filter': expression})
    return flags.RewriteFilter(
        args, message=message, frontend_fields=frontend_fields)

  def testResourceFilterRewriter(self):

    # In InstanceGroups, name, kind and zone are string fields, and size is a
    # numeric field. The InstanceGroup message overrides the heuristic that
    # uses the operand value as a hint.
    message = apis.GetMessagesModule('compute', 'v1').InstanceGroup

    def T(expected, expression, frontend_fields=None, exception=None):
      self.Run(expected, expression, message, frontend_fields=frontend_fields,
               depth=2, exception=exception)

    T((None, 'name eq ".*\\btrue\\b.*"'),
      'name=true')
    T((None, 'name eq ".*\\btrue\\b.*"'),
      'name=True')
    T((None, 'name eq ".*\\btrue\\b.*"'),
      'name=TRUE')
    T((None, 'name ne ".*\\bfalse\\b.*"'),
      'name!=false')
    T((None, 'name ne ".*\\bfalse\\b.*"'),
      'name!=False')
    T((None, 'name ne ".*\\bfalse\\b.*"'),
      'name!=FALSE')

    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      'name=foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      '-name=foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      'NOT name=foo*bar')

    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      'name!=foo*bar')
    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      '-name!=foo*bar')
    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      'NOT name!=foo*bar')

    T((None, r'name eq ".*\bfoo\*bar\b.*"'),
      'name:foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      '-name:foo*bar')
    T((None, r'name ne ".*\bfoo\*bar\b.*"'),
      'NOT name:foo*bar')

    T((None, 'name eq ".*\\b1\\.2\\b.*"'),
      'name=1.2')
    T((None, 'name ne ".*\\b1\\.2\\b.*"'),
      '-name=1.2')
    T((None, 'name ne ".*\\b1\\.2\\b.*"'),
      'NOT name=1.2')

    T((None, 'name ne ".*\\b1\\.2\\b.*"'),
      'name!=1.2')
    T((None, 'name eq ".*\\b1\\.2\\b.*"'),
      '-name!=1.2')
    T((None, 'name eq ".*\\b1\\.2\\b.*"'),
      'NOT name!=1.2')

    T((None, 'name eq ".*\\b1\\.2\\b.*"'),
      'name:1.2')
    T((None, 'name ne ".*\\b1\\.2\\b.*"'),
      '-name:1.2')
    T((None, 'name ne ".*\\b1\\.2\\b.*"'),
      'NOT name:1.2')

    T((None, 'name eq ".*\\b123\\b.*"'),
      'name=123')
    T((None, 'name ne ".*\\b123\\b.*"'),
      '-name=123')
    T((None, 'name ne ".*\\b123\\b.*"'),
      'NOT name=123')

    T((None, 'name ne ".*\\b123\\b.*"'),
      'name!=123')
    T((None, 'name eq ".*\\b123\\b.*"'),
      '-name!=123')
    T((None, 'name eq ".*\\b123\\b.*"'),
      'NOT name!=123')

    T((None, r'name ne ".*\ba\ eq\ b\b.*"'),
      '-name="a eq b"')
    T((None, r'name ne ".*\ba\ eq\ b\b.*"'),
      'NOT name="a eq b"')
    T((None, r'name eq ".*\ba\ eq\ b\b.*"'),
      'NOT -name="a eq b"')

    T((None, r'name ne ".*\ba\ ne\ b\b.*"'),
      '-name="a ne b"')
    T((None, r'name ne ".*\ba\ ne\ b\b.*"'),
      'NOT name="a ne b"')
    T((None, r'name eq ".*\ba\ ne\ b\b.*"'),
      'NOT -name="a ne b"')

    T((None, r'name eq ".*\ba\ eq\ b\b.*"'),
      '-name!="a eq b"')
    T((None, r'name eq ".*\ba\ eq\ b\b.*"'),
      'NOT name!="a eq b"')
    T((None, r'name ne ".*\ba\ eq\ b\b.*"'),
      'NOT -name!="a eq b"')

    T((None, r'name eq ".*\ba\ ne\ b\b.*"'),
      '-name!="a ne b"')
    T((None, r'name eq ".*\ba\ ne\ b\b.*"'),
      'NOT name!="a ne b"')
    T((None, r'name ne ".*\ba\ ne\ b\b.*"'),
      'NOT -name!="a ne b"')

    T((None, 'name eq ".*\\b123\\b.*"'),
      'name:123')
    T((None, 'name ne ".*\\b123\\b.*"'),
      '-name:123')
    T((None, 'name ne ".*\\b123\\b.*"'),
      'NOT name:123')

    # anomaly -- should be (None, ...)
    T(('NOT NOT name=123', 'name eq ".*\\b123\\b.*"'),
      'NOT NOT name=123')
    T((None, 'name eq ".*\\b123\\b.*"'),
      'NOT -name=123')

    T((None, r'name eq ".*(foo\*).*"'),
      r'name~foo\*')
    T((None, r'name eq ".*\bfoo\*\b.*"'),
      r'name=foo*')
    T((None, r'name eq ".*\bfoo.*"'),
      r'name:foo*')

    T((None, r'name eq ".*(foo.*\"bar).*"'),
      r'name~foo.*\"bar')
    T((None, r'name eq ".*\bfoo\*\"bar\b.*"'),
      r'name=foo*\"bar')
    T((None, r'name eq ".*\bfoo\*\"bar\b.*"'),
      r'name:foo*\"bar')

    # "name" and "kind" are string fields
    # "size" is a numeric field
    # "unknown" and "foo" are unknown

    T((None, r'(name eq ".*\bfoo\b.*")(kind eq ".*\bbar\b.*")'),
      'name:foo kind:bar')
    T((None, r'(name ne ".*\bfoo\b.*")(kind eq ".*\bbar\b.*")'),
      'NOT name:foo kind:bar')
    T((None, r'(name eq ".*\bfoo\b.*")(kind ne ".*\bbar\b.*")'),
      'name:foo NOT kind:bar')
    T((None, r'(name ne ".*\bfoo\b.*")(kind ne ".*\bbar\b.*")'),
      'NOT name:foo NOT kind:bar')

    T((None, '(name eq ".*\\b1\\.2\\b.*")(size eq 9.8)'),
      'name:1.2 size:9.8')
    T((None, '(name ne ".*\\b1\\.2\\b.*")(size eq 9.8)'),
      'NOT name:1.2 size:9.8')
    T((None, '(name eq ".*\\b1\\.2\\b.*")(size ne 9.8)'),
      'name:1.2 NOT size:9.8')
    T((None, '(name ne ".*\\b1\\.2\\b.*")(size ne 9.8)'),
      'NOT name:1.2 NOT size:9.8')

    T((None, '(name eq ".*\\b123\\b.*")(size eq 987)'),
      'name=123 size=987')
    T((None, '(name ne ".*\\b123\\b.*")(size eq 987)'),
      'NOT name=123 size=987')
    T((None, '(name eq ".*\\b123\\b.*")(size ne 987)'),
      'name=123 NOT size=987')
    T((None, '(name ne ".*\\b123\\b.*")(size ne 987)'),
      'NOT name=123 NOT size=987')

    # Implicit and explicit AND supported.

    T((None,
       '(name eq ".*\\b123\\b.*")((size eq 987)(kind eq ".*\\bup\\b.*"))'),
      'name=123 size=987 kind=up')
    T((None,
       '(name eq ".*\\b123\\b.*")((size eq 987)(kind eq ".*\\bup\\b.*"))'),
      'name=123 size=987 AND kind=up')

    # OR not supported.

    T(('(name=123 AND size=987) OR kind=up', None),
      '(name=123 AND size=987) OR kind=up')
    T(('(name=123 OR size=987) AND kind=up', 'kind eq ".*\\bup\\b.*"'),
      '(name=123 OR size=987) AND kind=up')
    T(('name=123 (size=987 OR kind=up)', 'name eq ".*\\b123\\b.*"'),
      'name=123 (size=987 OR kind=up)')

    T(('name:foo unknown:bar', 'name eq ".*\\bfoo\\b.*"'),
      'name:foo unknown:bar')
    T(('NOT name:foo unknown:bar', 'name ne ".*\\bfoo\\b.*"'),
      'NOT name:foo unknown:bar')
    T(('name:foo NOT unknown:bar', 'name eq ".*\\bfoo\\b.*"'),
      'name:foo NOT unknown:bar')
    T(('NOT name:foo NOT unknown:bar', 'name ne ".*\\bfoo\\b.*"'),
      'NOT name:foo NOT unknown:bar')

    T(('name:1.2 unknown:9.8', 'name eq ".*\\b1\\.2\\b.*"'),
      'name:1.2 unknown:9.8')
    T(('NOT name:1.2 unknown:9.8', 'name ne ".*\\b1\\.2\\b.*"'),
      'NOT name:1.2 unknown:9.8')
    T(('name:1.2 NOT unknown:9.8', 'name eq ".*\\b1\\.2\\b.*"'),
      'name:1.2 NOT unknown:9.8')
    T(('NOT name:1.2 NOT unknown:9.8', 'name ne ".*\\b1\\.2\\b.*"'),
      'NOT name:1.2 NOT unknown:9.8')

    T(('name=123 unknown=987', 'name eq ".*\\b123\\b.*"'),
      'name=123 unknown=987')
    T(('NOT name=123 unknown=987', 'name ne ".*\\b123\\b.*"'),
      'NOT name=123 unknown=987')
    T(('name=123 NOT unknown=987', 'name eq ".*\\b123\\b.*"'),
      'name=123 NOT unknown=987')
    T(('NOT name=123 NOT unknown=987', 'name ne ".*\\b123\\b.*"'),
      'NOT name=123 NOT unknown=987')

    T(('name=123 unknown=987 foo=up', 'name eq ".*\\b123\\b.*"'),
      'name=123 unknown=987 foo=up')
    T(('name=123 AND unknown=987 foo=up', 'name eq ".*\\b123\\b.*"'),
      'name=123 AND unknown=987 foo=up')
    T(('name=123 unknown=987 AND foo=up', 'name eq ".*\\b123\\b.*"'),
      'name=123 unknown=987 AND foo=up')
    T(('name=123 AND unknown=987 AND foo=up', 'name eq ".*\\b123\\b.*"'),
      'name=123 AND unknown=987 AND foo=up')

    T(('(name=123 AND unknown=987) OR foo=up', None),
      '(name=123 AND unknown=987) OR foo=up')
    T(('(name=123 OR unknown=987) AND foo=up', None),
      '(name=123 OR unknown=987) AND foo=up')
    T(('name=123 (unknown=987 OR foo=up)', 'name eq ".*\\b123\\b.*"'),
      'name=123 (unknown=987 OR foo=up)')

    # frontend_fields => unknown key exceptions.

    T(('name:foo unknown:bar', 'name eq ".*\\bfoo\\b.*"'),
      'name:foo unknown:bar', frontend_fields={},
      exception=resource_exceptions.UnknownFieldError)
    T(('name:foo unknown:bar', 'name eq ".*\\bfoo\\b.*"'),
      'name:foo unknown:bar', frontend_fields={'name'},
      exception=resource_exceptions.UnknownFieldError)

    # timestamp operand normalization.

    T((None,
       '(name eq ".*\\bfoo\\b.*")'
       '(creationTimestamp eq 2014-01-06T00:00:00.000Z)'),
      'name:foo creationTimestamp:"2014-01-06Z"')
    T((None, 'creationTimestamp eq ".*\\bnot\\ a\\ date\\/time\\b.*"'),
      'creationTimestamp:"not a date/time"')

    # Inequalties not supported.

    T(('name<foo*bar', None),
      'name<foo*bar')
    T(('name<=foo*bar', None),
      'name<=foo*bar')
    T(('name>=foo*bar', None),
      'name>=foo*bar')
    T(('name>foo*bar', None),
      'name>foo*bar')

    T(('name=(abc, xyz)', None),
      'name=(abc, xyz)')
    T(('NOT (name=abc disk=123)', 'name ne ".*\\babc\\b.*"'),
      'NOT (name=abc disk=123)')

    # basename() is a core transform.
    T(('zone.basename():us-central1-b', None),
      'zone.basename():us-central1-b')

    # location() is a compute transform.
    T(('foo.location():us-central1', None),
      'foo.location():us-central1')

    # unknown() is not a transform.
    T(('region.unknown():x', None),
      'region.unknown():x')

    # region & zone workarounds to handle matching on full URI.

    T(('unknown:us-central1-b', None), 'unknown:us-central1-b')
    T((None, r'region eq ".*\bus\-central1\-b\b.*"'), 'region:us-central1-b')
    T((None, r'zone eq ".*\bus\-central1\-b\b.*"'), 'zone:us-central1-b')

    T(('unknown=us-central1-b', None), 'unknown=us-central1-b')
    T((None, r'region eq ".*\bus\-central1\-b\b.*"'), 'region=us-central1-b')
    T((None, r'zone eq ".*\bus\-central1\-b\b.*"'), 'zone=us-central1-b')

    T(('unknown!=us-central1-b', None), 'unknown!=us-central1-b')
    T((None, r'region ne ".*\bus\-central1\-b\b.*"'), 'region!=us-central1-b')
    T((None, r'zone ne ".*\bus\-central1\-b\b.*"'), 'zone!=us-central1-b')


class GuessOperandTypeTest(subtests.Base):

  def RunSubTest(self, operand):
    return filter_rewrite._GuessOperandType(operand)

  def testGuessOperandType(self):

    def T(expected, operand):
      return self.Run(expected, operand, depth=2)

    T(int, '123')
    T(float, '1.23')
    T(bool, 'True')
    T(bool, 'TRUE')
    T(bool, 'true')
    T(bool, 'False')
    T(bool, 'FALSE')
    T(bool, 'false')
    T(messages.EnumField, 'RUNNING')
    T(messages.EnumField, 'THE_END')
    T(unicode, '1.23x')
    T(unicode, 'ascii!')


if __name__ == '__main__':
  test_case.main()
