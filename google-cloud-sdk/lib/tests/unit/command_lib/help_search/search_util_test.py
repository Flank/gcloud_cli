# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for help search utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import textwrap

from googlecloudsdk.command_lib.help_search import lookup
from googlecloudsdk.command_lib.help_search import search_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import help_search_test_base


class SnipTests(test_case.TestCase, parameterized.TestCase):
  """Tests of search_util.Snip."""

  def SetUp(self):
    self.text = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
                 'Donec pharetra, enim non volutpat viverra, libero ex '
                 'bibendum nibh, eu cursus nisl risus vitae lorem. Donec lorem '
                 'nibh, vestibulum a lacinia at, interdum eget metus. Sed '
                 'ultricies metus vitae consequat egestas. Sed lacinia ut '
                 'augue sit amet scelerisque. Vestibulum lacinia convallis '
                 'quam eu molestie.\n'  # Paragraph will be removed.
                 'Nam pharetra in justo et congue. Vivamus '
                 'velit lorem, elementum eget ante at, volutpat egestas eros. '
                 'Suspendisse pulvinar, mauris sit amet varius congue, sem '
                 'nisl varius orci, feugiat facilisis purus quam in nisl. '
                 'Vestibulum elementum turpis in lacus dictum, dictum congue '
                 'elit aliquam. Fusce sodales metus ut nulla lacinia pulvinar. '
                 'Donec et nulla enim. Duis malesuada euismod aliquet. Nunc '
                 'augue quam, lobortis a laoreet ac, blandit eu est. Fusce '
                 'justo nulla, egestas a viverra sed, pulvinar eget enim. '
                 'Cras quis cursus lorem.')  # 886 chars

  def testSnipNoTerms(self):
    self.assertEqual(search_util._Snip(self.text, 200, []),
                     ('Lorem ipsum dolor sit amet, consectetur adipiscing '
                      'elit. Donec pharetra, enim non volutpat viverra, libero '
                      'ex bibendum nibh, eu cursus nisl risus vitae lorem. '
                      'Donec lorem nibh, vestibulum a lacinia...'))
    self.assertEqual(search_util._Snip(self.text, 900, []),
                     self.text.replace('\n', ' '))
    # Terms that don't match.
    self.assertEqual(search_util._Snip(self.text, 200, ['notalatinword']),
                     ('Lorem ipsum dolor sit amet, consectetur adipiscing '
                      'elit. Donec pharetra, enim non volutpat viverra, libero '
                      'ex bibendum nibh, eu cursus nisl risus vitae lorem. '
                      'Donec lorem nibh, vestibulum a lacinia...'))

  @parameterized.named_parameters(
      ('MiddleOfText', 'lacinia',
       '...viverra, libero ex bibendum nibh, eu cursus nisl risus vitae lorem. '
       'Donec lorem nibh, vestibulum a lacinia at, interdum eget metus. Sed '
       'ultricies metus vitae consequat egestas. Sed lacinia ut augue...'),
      ('EndOfText', 'Cras',
       '...Donec et nulla enim. Duis malesuada euismod aliquet. Nunc augue '
       'quam, lobortis a laoreet ac, blandit eu est. Fusce justo nulla, '
       'egestas a viverra sed, pulvinar eget enim. Cras quis cursus lorem.'),
      ('BeginningOfText', 'consectetur',
       'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec '
       'pharetra, enim non volutpat viverra, libero ex bibendum nibh, eu '
       'cursus nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
       'lacinia...'))
  def testSnipOneTerm(self, term, expected_result):
    self.assertEqual(expected_result,
                     search_util._Snip(self.text, 200, [term]))

  def testSnipPartialWord(self):
    self.assertEqual(('...viverra, libero ex bibendum nibh, eu cursus '
                      'nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
                      'lacinia at, interdum eget metus. Sed ultricies metus '
                      'vitae consequat egestas. Sed lacinia ut augue...'),
                     search_util._Snip(self.text, 200, ['lacin']))

  @parameterized.named_parameters(
      ('FarApart', ['lacinia', 'cras'],
       '...viverra, libero ex bibendum nibh, eu cursus nisl risus vitae lorem. '
       'Donec lorem nibh, vestibulum a lacinia at, interdum eget metus. Sed '
       'ultricies metus vitae consequat egestas. Sed lacinia ut augue...Donec '
       'et nulla enim. Duis malesuada euismod aliquet. Nunc augue quam, '
       'lobortis a laoreet ac, blandit eu est. Fusce justo nulla, egestas a '
       'viverra sed, pulvinar eget enim. Cras quis cursus lorem.'),
      ('CloseTogether', ['lacinia', 'metus'],
       '...viverra, libero ex bibendum nibh, eu cursus nisl risus vitae lorem. '
       'Donec lorem nibh, vestibulum a lacinia at, interdum eget metus. Sed '
       'ultricies metus vitae consequat egestas. Sed lacinia ut augue...'),
      ('ExcerptsCombined', ['lacinia', 'scelerisque'],
       '...viverra, libero ex bibendum nibh, eu cursus nisl risus vitae lorem. '
       'Donec lorem nibh, vestibulum a lacinia at, interdum eget metus. Sed '
       'ultricies metus vitae consequat egestas. Sed lacinia ut augue sit amet '
       'scelerisque. Vestibulum lacinia convallis quam eu molestie. Nam '
       'pharetra in justo et congue. Vivamus...'))
  def testSnipTwoTerms(self, terms, expected_summary):
    self.assertEqual(expected_summary,
                     search_util._Snip(self.text, 200, terms))

  def testSnipNoWhitespace(self):
    text = self.text.replace(' ', '')
    self.assertEqual(search_util._Snip(text, 40, ['elementum']),
                     '...e.Vivamusvelitlorem,elementumegetanteat,...')
    two_word_text = 'Shortword ' + text
    # Should not be affected by earlier whitespace.
    self.assertEqual(search_util._Snip(two_word_text, 40, ['elementum']),
                     '...e.Vivamusvelitlorem,elementumegetanteat,...')

  def testMergeRaises(self):
    slice1 = search_util.TextSlice(0, 1)
    slice2 = search_util.TextSlice(5, 10)
    with self.assertRaisesRegex(
        ValueError,
        r'Cannot merge text slices \[0\:1\] and \[5\:10\]\: Do not overlap'):
      slice1.Merge(slice2)


class SummaryTests(help_search_test_base.HelpSearchTestBase,
                   parameterized.TestCase):
  """Tests of search_util functions."""

  @parameterized.named_parameters(
      ('', {'test': lookup.CAPSULE}, {},
       'A TEST command with a long help section.'),
      ('PathAndNameDoNotAffect',
       {'test': lookup.CAPSULE, 'random': lookup.PATH,
        'something': lookup.NAME},
       {},
       'A TEST command with a long help section.'),
      ('Snip', {'long': lookup.CAPSULE}, {'length_per_snippet': 16},
       '...with a LONG help...'),
      ('CapsuleIsAdded', {}, {}, 'A test command with a long help section.'))
  def testGetSummaryJustCapsule(self, results_map, summary_kwargs,
                                expected_summary):
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, results_map,
                                            **summary_kwargs))

  @parameterized.named_parameters(
      ('SingleFlag',
       {'': lookup.CAPSULE, 'zero': '.'.join([lookup.FLAGS, '--zero-or-one',
                                              lookup.NAME])},
       textwrap.dedent("""\
       Brief description of what Nothing Happens means.
       # FLAGS
       --ZERO-or-one::
       ZERO or one description.""")),
      ('TwoFlagsWithDefault',
       {'': lookup.CAPSULE,
        'rachel': '.'.join([lookup.FLAGS, '--three-choices',
                            lookup.DESCRIPTION]),
        'curly': '.'.join([lookup.FLAGS, '--exactly-one', lookup.DEFAULT])},
       'Brief description of what Nothing Happens means.\n'
       '# FLAGS\n'
       '--exactly-one::\n'
       'Exactly one description.\n'
       'Default: CURLY.\n'
       '--three-choices::\n'
       'Choices description. _FRIENDS_ must be one of: *RACHEL*, *phoebe*, '
       '*monica*.'),
      ('WithPositionals',
       {'': lookup.CAPSULE,
        'pdq': '.'.join([lookup.POSITIONALS, 'pdq', lookup.NAME])},
       'Brief description of what Nothing Happens means.\n'
       '# POSITIONALS\n'
       'PDQ::\n'
       'PDQ the PDQ.'),
      ('SeveralTermsSameFlag',
       {'one': '.'.join([lookup.FLAGS, '--exactly-one', lookup.NAME]),
        'desc': '.'.join([lookup.FLAGS, '--exactly-one', lookup.DESCRIPTION]),
        'tion': '.'.join([lookup.FLAGS, '--exactly-one', lookup.DESCRIPTION]),
        'curly': '.'.join([lookup.FLAGS, '--exactly-one', lookup.DEFAULT])},
       # Flag should only be shown once.
       'Brief DESCripTION of what Nothing Happens means.\n'
       '# FLAGS\n'
       '--exactly-ONE::\n'
       'Exactly ONE DESCripTION.\n'
       'Default: CURLY.'))
  def testGetSummaryWithArgument(self, results_map, expected_summary):
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.xyzzy, results_map))

  @parameterized.named_parameters(
      ('', {'': lookup.CAPSULE, 'castle': lookup.SECTIONS + '.DESCRIPTION'},
       'A test command with a long help section.\n'
       '# DESCRIPTION\n'
       '...with a very long help section, and some newlines '
       'and things like that, and weird words including `CASTLE`. '
       'It can be used to test displaying long help, or summarizing it as '
       'for `gcloud search-help`....'),
      ('MultipleTerms',
       {'': lookup.CAPSULE,
        'tarantula': lookup.SECTIONS + '.DESCRIPTION',
        'mittens': lookup.SECTIONS + '.DESCRIPTION'},
       'A test command with a long help section.\n'
       '# DESCRIPTION\n'
       '...or summarizing it as for `gcloud search-help`. If a person is '
       'searching the word `scorpion` or `TARANTULA`, this sentence should '
       'be in the excerpt. That way they know why they are seeing this '
       'command,'
       '...aren\'t so close to the other terms in the next paragraph. '
       'On the other hand if they aren\'t looking for scary '
       'bugs and are searching the word `MITTENS`, the excerpt should center '
       'around this part.'))
  def testGetSummaryWithSection(self, results_map, expected_summary):
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, results_map))

  def testGetSummaryWithCommandGroup(self):
    # With just a list of positional arguments.
    results_map = {'': lookup.CAPSULE, 'long': lookup.COMMANDS}
    expected_summary = (
        'gcloud sdk tests second level group.\n'
        '# COMMANDS\n'
        'hidden-command, hiddengroup, LONG-help, second-level-command-1, '
        'second-level-command-b, subgroup, xyzzy'
    )
    # Mimic the first step of replacing 'commands' dict with list of keys.
    sdk_node = copy.deepcopy(self.sdk)
    sdk_node.update(
        {lookup.COMMANDS:
         list(self.sdk.get(lookup.COMMANDS, {}).keys())})
    self.assertEqual(expected_summary,
                     search_util.GetSummary(sdk_node, results_map))
    # Should still work if the commands dict wasn't changed for some reason.
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.sdk, results_map))

  @parameterized.named_parameters(
      ('InvalidFirstTerm', 'randomsection', 'invalid'),
      ('InvalidSection', 'sections.anothersection', 'invalid'),
      ('InvalidThirdTerm', 'flags.--exactly-three.junk', 'invalid'),
      ('InvalidFlag', 'flags.--junk.name', 'invalid'),
      ('InvalidPositional', 'positionals.junk.name', 'invalid'),
      ('ShortFlagLocation', 'flags.--exactly-three', 'three segments'),
      ('ShortPositionalLocation', 'positionals.pdq', 'three segments'))
  def testGetSummaryWithInvalidSections(self, location, expected_expression):
    with self.assertRaisesRegex(AssertionError, expected_expression):
      search_util.GetSummary(self.xyzzy, {'term': location})

  def testGetSummaryWithNonStringSections(self):
    found_terms = {
        'dict': 'dictsection',
        'number': 'numbersection'}
    expected_summary = ('Brief description of what Nothing Happens means.\n'
                        '# DICTSECTION\n'
                        'a, b\n'
                        '# NUMBERSECTION\n'
                        '12345')
    # Test that sections that contain non strings are handled.
    xyzzy = copy.deepcopy(self.xyzzy)
    xyzzy.update({'dictsection': {'a': 1, 'b': 2},
                  'numbersection': 12345})
    self.assertEqual(expected_summary,
                     search_util.GetSummary(xyzzy, found_terms))

  @parameterized.named_parameters(
      ('SingleTerm', {'term1': lookup.NAME}),
      ('MultipleTerms', {'term1': lookup.NAME, 'term2': ''}))
  def testProcessResult(self, results_data):
    # Test that result 'commands' and 'result' are correctly set.
    version_command = self.parent.get(lookup.COMMANDS, {}).get('version', {})
    result = search_util.ProcessResult(
        version_command,
        search_util.CommandSearchResults(results_data))
    self.assertEqual([], result.get(lookup.COMMANDS))
    # The results are the same for both cases because only found terms are
    # shown.
    self.assertEqual({'term1': lookup.NAME},
                     result.get(lookup.RESULTS))

  @parameterized.named_parameters(
      ('FlagChoice', 'phoebe', 'flags.--three-choices.choices'),
      ('FlagName', 'choices', 'flags.--three-choices.name'),
      ('Junk', 'junk', ''),
      ('Default', 'moe', 'flags.--exactly-three.default'),
      ('Examples', 'components', 'sections.EXAMPLES'),
      ('PositionalName', 'pdq', 'positionals.pdq.name'),
      # The word 'description' appears in the brief description as well as
      # flags. Should only return 'capsule'
      ('Capsule', 'description', 'capsule'),
      ('Path', 'sdk', 'path'))
  def testLocateTerms(self, term, expected_location):
    # Test that terms are correctly located in command.
    self.assertEqual(expected_location,
                     search_util.LocateTerm(self.xyzzy, term))

  @parameterized.named_parameters(
      ('Capsule', {'': lookup.CAPSULE},
       'Brief description of what Nothing Happens means.'),
      ('WithMarkdown',
       {'': lookup.CAPSULE, 'the': lookup.POSITIONALS + '.pdq.description'},
       'Brief description of what Nothing Happens means.\n'
       'POSITIONALS\n'
       'pdq\n'
       'pdq THE PDQ.'))
  def testSummaryTransforms(self, results_map, expected_summary):
    command = copy.deepcopy(self.xyzzy)
    command[lookup.RESULTS] = results_map
    self.assertEqual(expected_summary, search_util.SummaryTransform(command))

  @parameterized.named_parameters(
      ('NoChange',
       {lookup.RESULTS: {'abc': 'sections.DESCRIPTION'},
        lookup.PATH: ['xyz', 'foo']},
       'xyz foo'),
      ('OneTerm',
       {lookup.RESULTS: {'xyz': lookup.PATH}, lookup.PATH: ['xyz', 'foo']},
       'XYZ foo'),
      # Doesn't matter if the term was found elsewhere originally.
      ('TwoTerms',
       {lookup.RESULTS: {'xyz': lookup.PATH, 'foo': lookup.NAME},
        lookup.PATH: ['xyz', 'foo']},
       'XYZ FOO'))
  def testCommandPathTransforms(self, command, expected_path):
    self.assertEqual(expected_path,
                     search_util.PathTransform(command))


if __name__ == '__main__':
  test_case.main()
