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

"""Unit tests for the usage_text module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.calliope import util

import mock


class UsageTextTest(util.WithTestTool):

  def testExtractHelpStrings(self):
    # pylint: disable=g-continuation-misaligned
    # pylint: disable=g-continuation-in-dict-misaligned
    test_cases = (
        {'input': None, 'expected_short': '', 'expected_long': ''},
        {'input': 'short\n',
         'expected_short': 'short', 'expected_long': 'short'},
        {'input': 'short 1\nshort 2\n',
         'expected_short': 'short 1 short 2',
         'expected_long': 'short 1 short 2'},
        {'input': 'short\n\nlong',
         'expected_short': 'short', 'expected_long': 'long'},
        {'input': 'short 1\nshort 2\n\n   long\n     long indented',
         'expected_short': 'short 1 short 2',
         'expected_long': 'long\n  long indented'},
        {'input': 'short\n\n  long para 1\n\n  long para 2\n',
         'expected_short': 'short',
         'expected_long': 'long para 1\n\nlong para 2'},
        {'input': '\nline 1 after blank line\n line 2 after blank line',
         'expected_short':
                 'line 1 after blank line line 2 after blank line',
         'expected_long':
                 'line 1 after blank line\n line 2 after blank line'},
        {'input': '', 'expected_short': '', 'expected_long': ''},
        {'input': ' ', 'expected_short': '', 'expected_long': ''},
        {'input': '\tshort\t\n\n long \n',
         'expected_short': 'short', 'expected_long': 'long'},
        # In the following corner cases, there are two blank lines. The first is
        # taken as the divider between the (nonexistant) short help and the long
        # help, both of which are stripped to '' and replaced by None.
        {'input': '\n', 'expected_short': '', 'expected_long': ''},
        {'input': '\n ', 'expected_short': '', 'expected_long': ''},
        {'input': ' \n', 'expected_short': '', 'expected_long': ''},
        {'input': ' \n ', 'expected_short': '', 'expected_long': ''},
        # In the following case, there are three blank lines, the last two of
        # which are interpreted as long help. The long help is transformed from
        # ' \n  ' to '\n ' by dedenting, and then to '' by stripping, and then
        # replaced by None.
        {'input': ' \n \n  \n', 'expected_short': '', 'expected_long': ''},
        # In the following case, there is a line consisting of a space, followed
        # by two lines taken as the long help. The long help is dedented to
        # '\n x\n' and then stripped to 'x'. Since there is no short help but
        # nonempty long help, we flow the words of the long help together to
        # form the short help.
        {'input': ' \n \n  x\n', 'expected_short': 'x', 'expected_long': 'x'},
    )
    for testcase in test_cases:
      input_string = testcase['input']
      (short_help, long_help) = usage_text.ExtractHelpStrings(input_string)
      self.assertEqual(
          testcase['expected_short'], short_help,
          'short help for input<%s>' % (input_string,))
      self.assertEqual(
          testcase['expected_long'], long_help,
          'long help for input<%s>' % (input_string,))

  def testArgOrder(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 remainder-with-flags'.split())
    self.AssertErrContains(
        'remainder-with-flags SINGLE_POSITIONAL --foo=FOO [optional flags] '
        '[-- PASSTHROUGH_ARGS ...]')

  def testRemainderExtraArgs(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 extra-args -- foo --bar'.split())
    self.AssertErrContains(
        'extra-args POSITIONAL [optional flags] [-- EXTRA_ARGS ...]')

  def testSuppressedPositionalUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 suppressed-positional -h'.split())
    self.AssertOutputNotContains('SUPPRESSED')
    self.AssertOutputNotContains('positional arguments')
    self.AssertOutputNotContains('--hidden')

  def testSuppressedPositionalHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 suppressed-positional --help'.split())
    self.AssertOutputNotContains('SUPPRESSED')
    self.AssertOutputNotContains('POSITIONAL ARGUMENTS')
    self.AssertOutputNotContains('==SUPPRESS==')
    self.AssertOutputNotContains('--hidden')

  def testUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 [optional flags] <group | command>
  group may be           lotsofargs
  command may be         arg-groups | bool-mutex | combinations | command2 |
                         common-flags | common-other-flags | deprecated-args |
                         dynamic-args | extra-args | list-command-flags |
                         modal-group | multiple-positional | nested-groups |
                         ordered-choices | other-flags | remainder |
                         remainder-with-flags | required-common-flags |
                         required-common-other-flags | required-flags |
                         required-other-flags | required-vs-optional |
                         requiredargcommand | suppressed-positional

For detailed information on this command and its flags, run:
  test sdk2 --help
""")

  def testUsageTop(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('-h'.split())
    self.AssertOutputEquals("""\
Usage: test [optional flags] <group | command>
  group may be           beta | broken-sdk | cfg | compound-group |
                         newstylegroup | sdk11 | sdk2 | sdk3 | sdk7
  command may be         command1 | dict-list | exceptioncommand | exit2 |
                         help | implementation-args | loggingcommand |
                         mutex-command | newstylecommand | recommand |
                         requiredargcommand | simple-command | unsetprop

For detailed information on this command and its flags, run:
  test --help
""")

  def testUsageCommon(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 common-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 common-flags [optional flags]
  optional flags may be  --common | --help

For detailed information on this command and its flags, run:
  test sdk2 common-flags --help
""")

  def testUsageCommonOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 common-other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 common-other-flags [optional flags]
  optional flags may be  --common | --help | --other

For detailed information on this command and its flags, run:
  test sdk2 common-other-flags --help
""")

  def testUsageOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 other-flags [optional flags]
  optional flags may be  --help | --other

For detailed information on this command and its flags, run:
  test sdk2 other-flags --help
""")

  def testUsageRequiredCommonOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-common-other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-common-other-flags --required=REQUIRED [optional flags]
  optional flags may be  --common | --help | --other

For detailed information on this command and its flags, run:
  test sdk2 required-common-other-flags --help
""")

  def testUsageRequiredCommon(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-common-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-common-flags --required=REQUIRED [optional flags]
  optional flags may be  --common | --help

For detailed information on this command and its flags, run:
  test sdk2 required-common-flags --help
""")

  def testUsageRequiredOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-other-flags --required=REQUIRED [optional flags]
  optional flags may be  --help | --other

For detailed information on this command and its flags, run:
  test sdk2 required-other-flags --help
""")

  def testUsageRequired(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-flags --required=REQUIRED [optional flags]
  optional flags may be  --help

For detailed information on this command and its flags, run:
  test sdk2 required-flags --help
""")

  def testUsageListCommand(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 list-command-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 list-command-flags [optional flags]
  optional flags may be  --filter | --help | --limit | --page-size | --sort-by |
                         --uri

For detailed information on this command and its flags, run:
  test sdk2 list-command-flags --help
""")

  def testUsagePositionalsStableSort(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 multiple-positional -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 multiple-positional [USER@]ZZZ [[USER@]ZZZ ...] [USER@]AAA [[USER@]AAA ...] [optional flags]
  optional flags may be  --help

For detailed information on this command and its flags, run:
  test sdk2 multiple-positional --help
""")

  def testCategoricalUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2'.split())
    self.AssertErrContains("""\
ERROR: (test.sdk2) Command name argument expected.

Available command groups for test sdk2:

      lotsofargs              A group with required and optional flags.

Available commands for test sdk2:

  Category 1
      arg-groups              Argument groups test command.
      combinations            A command to test generator / exception
                              combinations.

  Category 2
      bool-mutex              A command with a Boolean flag in a mutex group.

  Other
      command2                     A command with context and flags.
      common-flags                 A command with common flags and explicit
                                   NOTES.
      common-other-flags           A command with common+other flags.
      deprecated-args              actions.DeprecationAction test command.
      dynamic-args                 parser_extensions.DynamicPositionalAction
                                   test command.
      extra-args                   A command to test the posix '--' workaround.
      hidden                       A command that is hidden.
      list-command-flags           A command with list command flags.
      modal-group                  A command with a modal group with multiple
                                   required flags.
      multiple-positional          A command to test argument ordering in usage
                                   text.
      nested-groups                A command with nested argument group
                                   combinations.
      ordered-choices              A command with required flags.
      other-flags                  A command with other flags.
      remainder                    A command to test remainder args.
      remainder-with-flags         A command to test remainder args.
      required-common-flags        A command with required+common flags.
      required-common-other-flags  A command with required+common+other flags.
      required-flags               A command with required flags.
      required-other-flags         A command with required+other flags.
      required-vs-optional         A command with required vs optional flag
                                   combinations.
      requiredargcommand           A command with an underscored flag.
      suppressed-positional        A command to test remainder args.
""")

  def testUncategorizedUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk3'.split())
    self.AssertErrEquals("""\
ERROR: (test.sdk3) Command name argument expected.

Available groups for test sdk3:

      newstylegroup           Group short help.

Available commands for test sdk3:

      nested                  A nested command.

For detailed information on this command and its flags, run:
  test sdk3 --help
""")

  def testHelpBoolMutex(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 bool-mutex --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 bool-mutex - a command with a Boolean flag in a mutex group

SYNOPSIS
    test sdk2 bool-mutex [--no-bool-independent] [--bool-mutex | --value=VALUE]
        [TEST_WIDE_FLAG ...]

DESCRIPTION
    A command with a Boolean flag in a mutex group.

FLAGS
     --bool-independent
        Independent Boolean flag on by default. Enabled by default, use
        --no-bool-independent to disable.

     At most one of these may be specified:

       --bool-mutex
          Boolean flag in mutex group.

       --value=VALUE
          Value flag.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity.

    Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 bool-mutex
""")

  def testHelpRequiredVsOptional(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-vs-optional --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 required-vs-optional - a command with required vs optional flag
        combinations

SYNOPSIS
    test sdk2 required-vs-optional EPISODE
        --required-singleton=REQUIRED_SINGLETON
        (--that-one=THAT_ONE | --this-one=THIS_ONE)
        [--optional-singleton=OPTIONAL_SINGLETON]
        [--half-dozen-of-the-other=HALF_DOZEN_OF_THE_OTHER
          | --six-of-one=SIX_OF_ONE] [--larry=QUOTE --moe=QUOTE --shemp=QUOTE]
        [TEST_WIDE_FLAG ...]

DESCRIPTION
    A command with required vs optional flag combinations.

POSITIONAL ARGUMENTS
     EPISODE
        your favorite eposide.

REQUIRED FLAGS
     --required-singleton=REQUIRED_SINGLETON
        Required singleton flag.

     Exactly one of these must be specified:

       --that-one=THAT_ONE
          That one.

       --this-one=THIS_ONE
          This one.

OPTIONAL FLAGS
     --optional-singleton=OPTIONAL_SINGLETON
        Optional singleton flag.

     At most one of these may be specified:

       --half-dozen-of-the-other=HALF_DOZEN_OF_THE_OTHER
          Half dozen of the other.

       --six-of-one=SIX_OF_ONE
          Six of one.

     These are the stooge related flags:

       --larry=QUOTE
          I didn't wanna say yes but I couldn't say no.

       --moe=QUOTE
          Why you.

       --shemp=QUOTE
          Hey Moe! Hey Larry!

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity.

    Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 required-vs-optional
""")

  def testHelpEmptyDocstringDescription(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('beta sdk2 command2 --help'.split())
    self.AssertOutputContains("""\
NAME
    test beta sdk2 command2 - test empty DESCRIPTION followed by EXAMPLES

SYNOPSIS
    test beta sdk2 command2 [TEST_WIDE_FLAG ...]

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity.

    Run $ test help for details.

EXAMPLES
    Don't use this example as an example for writing examples.

NOTES
    This command is currently in BETA and may change without notice. This
    variant is also available:

        $ test sdk2 command2
""")

  def testHelpMarkdownDeprecatedAction(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 deprecated-args --document=style=markdown'.split())
    self.AssertOutputContains("""\
# TEST_SDK2_DEPRECATED-ARGS(1)


## NAME

test sdk2 deprecated-args - actions.DeprecationAction test command


## SYNOPSIS

`test sdk2 deprecated-args` [*--begin*=_BEGIN_] [*--deprecated-arg*=_DEPRECATED_ARG_] [*--end*=_END_] [*--removed-arg*=_REMOVED_ARG_] [_TEST_WIDE_FLAG ..._]


## DESCRIPTION

actions.DeprecationAction test command.


## FLAGS

*--begin*=_BEGIN_::

Begin flag help.

*--deprecated-arg*=_DEPRECATED_ARG_::

(DEPRECATED) Deprecated flag help.
+
Note we have more to say about this. Run:
+
  $ gcloud alpha container clusters update example-cluster \\
      --zone us-central1-a --additional-zones ""
+
This flag is messed up.

*--end*=_END_::

End flag help.

*--removed-arg*=_REMOVED_ARG_::

(REMOVED) Removed flag help. Run:
+
  gcloud bar --removed-arg=foo
+
Flag removed_arg has been removed.


## TEST WIDE FLAGS

These flags are available to all commands: --configuration, --flags-file, --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled, --verbosity.

Run *$ link:test/help[test help]* for details.


## NOTES

This variant is also available:

  $ link:test/beta/sdk2/deprecated-args[test beta sdk2 deprecated-args]
""")

  def testHelpDeprecatedAction(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 deprecated-args --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 deprecated-args - actions.DeprecationAction test command

SYNOPSIS
    test sdk2 deprecated-args [--begin=BEGIN] [--deprecated-arg=DEPRECATED_ARG]
        [--end=END] [--removed-arg=REMOVED_ARG] [TEST_WIDE_FLAG ...]

DESCRIPTION
    actions.DeprecationAction test command.

FLAGS
     --begin=BEGIN
        Begin flag help.

     --deprecated-arg=DEPRECATED_ARG
        (DEPRECATED) Deprecated flag help.

        Note we have more to say about this. Run:

            $ gcloud alpha container clusters update example-cluster \\
                --zone us-central1-a --additional-zones ""

        This flag is messed up.

     --end=END
        End flag help.

     --removed-arg=REMOVED_ARG
        (REMOVED) Removed flag help. Run:

            gcloud bar --removed-arg=foo

        Flag removed_arg has been removed.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity.

    Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 deprecated-args
""")

  def testHelpExplicitNotes(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 common-flags --document=style=markdown'.split())
    self.AssertOutputContains("""\
## NOTES

Move along, no autogenerated notes to see here.
""")

  def testHelpUnicodeChoices(self):
    self.SetEncoding('utf8')
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk11 sdk optional-flags --help'.split())
    self.AssertOutputContains('☠123')

  def testMarkdownExplicitAndAutogeneratedNotes(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'beta sdk2 common-flags --document=style=markdown'.split())
    self.AssertOutputContains("""\
## NOTES

Explicit notes should appear along with BETA autogenerated notes.

This command is currently in BETA and may change without notice.
This variant is also available:

  $ link:test/sdk2/common-flags[test sdk2 common-flags]

""")

  def testArgumentGroupsMarkdown(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2 arg-groups --document=style=markdown'.split())
    self.AssertOutputContains("""\
# TEST_SDK2_ARG-GROUPS(1)


## NAME

test sdk2 arg-groups - argument groups test command


## SYNOPSIS

`test sdk2 arg-groups` (_REQUIRED_MODAL_POSITIONAL_ : *--abc*) [[_OPTIONAL_MODAL_POSITIONAL_ ...] *--def*] (*--required-modal-flag* : *--ghi*) [*--optional-modal-flag* : *--jkl*] [_TEST_WIDE_FLAG ..._]


## DESCRIPTION

Argument groups test command.


## POSITIONAL ARGUMENTS

:: Required positional group. This must be specified.


_REQUIRED_MODAL_POSITIONAL_:::

Required modal positional.
This positional must be specified if any of the other arguments in this group are specified.

*--abc*:::

Optional flag.

:: Optional positional group.


[_OPTIONAL_MODAL_POSITIONAL_ ...]:::

Optional modal positional.

*--def*:::

Optional flag.


## REQUIRED FLAGS

:: Required flag group. This must be specified.


*--required-modal-flag*:::

Required modal flag.
This flag must be specified if any of the other arguments in this group are specified.

*--ghi*:::

Optional flag.


## OPTIONAL FLAGS

:: Optional flag group.


*--optional-modal-flag*:::

Optional modal flag.
This flag must be specified if any of the other arguments in this group are specified.

*--jkl*:::

Optional flag.
""")

  def testArgumentGroupsText(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2 arg-groups --document=style=text'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 arg-groups - argument groups test command

SYNOPSIS
    test sdk2 arg-groups (REQUIRED_MODAL_POSITIONAL : --abc)
        [[OPTIONAL_MODAL_POSITIONAL ...] --def] (--required-modal-flag : --ghi)
        [--optional-modal-flag : --jkl] [TEST_WIDE_FLAG ...]

DESCRIPTION
    Argument groups test command.

POSITIONAL ARGUMENTS
     Required positional group. This must be specified.

       REQUIRED_MODAL_POSITIONAL
          Required modal positional. This positional must be specified if any
          of the other arguments in this group are specified.

       --abc
          Optional flag.

     Optional positional group.

       [OPTIONAL_MODAL_POSITIONAL ...]
          Optional modal positional.

       --def
          Optional flag.

REQUIRED FLAGS
     Required flag group. This must be specified.

       --required-modal-flag
          Required modal flag. This flag must be specified if any of the other
          arguments in this group are specified.

       --ghi
          Optional flag.

OPTIONAL FLAGS
     Optional flag group.

       --optional-modal-flag
          Optional modal flag. This flag must be specified if any of the other
          arguments in this group are specified.

       --jkl
          Optional flag.
""")

  def testArgumentGroupsShort(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2 arg-groups -h'.split())
    self.AssertOutputContains("""\
Usage: test sdk2 arg-groups (REQUIRED_MODAL_POSITIONAL : --abc) [[OPTIONAL_MODAL_POSITIONAL ...] --def] (--required-modal-flag : --ghi) [optional flags]
  optional flags may be  --abc | --def | --ghi | --help | --jkl |
                         --optional-modal-flag
""")

  def testOrderedChoicesText(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 ordered-choices --help'.split())
    self.AssertOutputContains("""\
     --foo=FOO
        Ordered Choices. FOO must be one of:

         a-1g
            first
         a-10g
            second
         a-100g
            third
""")


class UsageTextTestWithIOCapture(util.WithTestTool,
                                 test_case.WithInput,
                                 test_case.WithOutputCapture):

  def testPromptSuggester(self):
    properties.VALUES.core.disable_prompts.Set(False)
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL)

    self.WriteInput('hez', 'yoy', 'ovre', 'their')
    options = ['hey', 'you', 'over', 'there']

    suggester = usage_text.TextChoiceSuggester(choices=options)
    result = console_io.PromptChoice(options, allow_freeform=True,
                                     freeform_suggester=suggester)

    self.AssertErrContains('[hez] not in list. Did you mean [hey]?')
    self.AssertErrContains('[yoy] not in list. Did you mean [you]?')
    self.AssertErrContains('[ovre] not in list. Did you mean [over]?')
    self.AssertErrContains('[their] not in list. Did you mean [there]?')

    self.assertEqual(result, None)


class UsageUtilTest(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()

  def testGetFlagUsageDefaultString(self):
    arg = self.parser.add_argument(
        '--flag', default='default', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default="default"',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultString(self):
    arg = self.parser.add_argument(
        '--flag', default='default', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultStringWithDoubleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR "b"', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default=\'"a" OR "b"\'',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultStringWithDoubleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR "b"', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultStringWithSingleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default="'a' OR 'b'", help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default="\'a\' OR \'b\'"',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultStringWithSingleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default="'a' OR 'b'", help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultStringWithMixedQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR \'b\'', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default=\'"a" OR \\\'b\\\'\'',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultStringWithMixedQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR \'b\'', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultInt(self):
    arg = self.parser.add_argument(
        '--flag', default=123, help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default=123',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultInt(self):
    arg = self.parser.add_argument(
        '--flag', default=123, help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultFalse(self):
    arg = self.parser.add_argument(
        '--bool', default=False, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageDefaultFalseInverted(self):
    arg = self.parser.add_argument(
        '--bool', default=False, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--no-bool',
                     usage_text.GetFlagUsage(
                         arg, inverted=usage_text.InvertedValue.INVERTED))

  def testGetFlagUsageBriefDefaultFalse(self):
    arg = self.parser.add_argument(
        '--bool', default=False, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultTrue(self):
    arg = self.parser.add_argument(
        '--bool', default=True, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageDefaultTrueInverted(self):
    arg = self.parser.add_argument(
        '--bool', default=True, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--no-bool',
                     usage_text.GetFlagUsage(
                         arg, inverted=usage_text.InvertedValue.INVERTED))

  def testGetFlagUsageBriefDefaultTrue(self):
    arg = self.parser.add_argument(
        '--bool', default=True, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg, brief=True))


class GcloudUsageTextTest(util.WithTestTool):

  def SetUp(self):
    self.known_error_handler = mock.MagicMock()
    self._loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=self.Resource('surface'),
        allow_non_existing_modules=True,
        known_error_handler=self.known_error_handler,
        yaml_command_translator=yaml_command_translator.Translator())

    self.cli = self._loader.Generate()

  def testGcloudUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute([])
    print('error is', self.GetErr(), 'end error')
    expected = r"""ERROR: \(gcloud\) Command name argument expected\.

Available command groups for gcloud:

  AI and Machine Learning
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  API Platform and Ecosystems
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  CI\/CD
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Compute
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Data Analytics
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Databases
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Identity
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Identity and Security
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Internet of Things
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Management Tools
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Mobile
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Networking
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  SDK Tools
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Security
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Storage
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+"""

    self.assertIsNotNone(re.match(expected, self.GetErr()))

  def testGcloudComputeUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('compute'.split())
    expected = r"""ERROR: \(gcloud\.compute\) Command name argument expected\.

Available command groups for gcloud compute:

  Compute
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Disks
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Info
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Instances
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Load Balancing
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Networking
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Tools
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+"""

    self.assertIsNotNone(re.match(expected, self.GetErr()))

  def testGcloudComputeUsagePager(self):
    self.StartObjectPatch(console_io, 'IsInteractive', return_value=True)
    mock_more = self.StartObjectPatch(console_io, 'More')
    with self.assertRaises(SystemExit):
      self.cli.Execute('compute'.split())
    self.AssertErrEquals(
        'ERROR: (gcloud.compute) Command name argument expected.\n')
    contents = r"""Command name argument expected\.

Available command groups for gcloud compute:

  Compute
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Disks
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Info
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Instances
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Load Balancing
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Networking
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
  Tools
(      [-\w]+\s+[-./,'\w\s]+?\.\n)+"""

    self.assertEquals(1, mock_more.call_count)
    self.assertEquals(1, len(mock_more.call_args[0]))
    self.assertIsNotNone(re.match(contents, mock_more.call_args[0][0]))
    self.assertEquals({'out': mock.ANY}, mock_more.call_args[1])

  def testGcloudComputeInstancesUsage(self):
    # Expect to see uncategorized usage text since no categories are defined.
    with self.assertRaises(SystemExit):
      self.cli.Execute('compute instances'.split())
    expected = r"""ERROR: \(gcloud\.compute\.instances\) Command name argument expected\.

Available groups for gcloud compute instances:

(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
Available commands for gcloud compute instances:

(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
For detailed information on this command and its flags, run:
  gcloud compute instances --help\n\Z"""

    self.assertIsNotNone(re.match(expected, self.GetErr()))

  def testGcloudConfigUsage(self):
    # Expect to see uncategorized usage text since no categories are defined.
    with self.assertRaises(SystemExit):
      self.cli.Execute('config'.split())
    expected = r"""ERROR: \(gcloud\.config\) Command name argument expected\.

Available groups for gcloud config:

(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
Available commands for gcloud config:

(      [-\w]+\s+[-./,'\w\s]+?\.\n)+
For detailed information on this command and its flags, run:
  gcloud config --help\n\Z"""

    self.assertIsNotNone(re.match(expected, self.GetErr()))

if __name__ == '__main__':
  test_case.main()
