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

"""Unit tests for help search utils."""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import textwrap

from googlecloudsdk.command_lib.search_help import lookup
from googlecloudsdk.command_lib.search_help import search_util
from tests.lib import test_case
from tests.lib.surface import search_help_test_base


class SnipTests(test_case.TestCase):
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

  def testSnipOneTerm(self):
    self.assertEqual(search_util._Snip(self.text, 200, ['lacinia']),
                     ('...viverra, libero ex bibendum nibh, eu cursus '
                      'nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
                      'lacinia at, interdum eget metus. Sed ultricies metus '
                      'vitae consequat egestas. Sed lacinia ut augue...'))
    # At the end of the text
    self.assertEqual(search_util._Snip(self.text, 200, ['Cras']),
                     ('...Donec et nulla enim. Duis malesuada euismod aliquet. '
                      'Nunc augue quam, lobortis a laoreet ac, blandit eu est. '
                      'Fusce justo nulla, egestas a viverra sed, pulvinar eget '
                      'enim. Cras quis cursus lorem.'))
    # At the beginning of the text.
    self.assertEqual(search_util._Snip(self.text, 200, ['consectetur']),
                     ('Lorem ipsum dolor sit amet, consectetur adipiscing '
                      'elit. Donec pharetra, enim non volutpat viverra, libero '
                      'ex bibendum nibh, eu cursus nisl risus vitae lorem. '
                      'Donec lorem nibh, vestibulum a lacinia...'))

  def testSnipPartialWord(self):
    self.assertEqual(search_util._Snip(self.text, 200, ['lacin']),
                     ('...viverra, libero ex bibendum nibh, eu cursus '
                      'nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
                      'lacinia at, interdum eget metus. Sed ultricies metus '
                      'vitae consequat egestas. Sed lacinia ut augue...'))

  def testSnipTwoTerms(self):
    # With terms far apart (2 snippets)
    self.assertEqual(search_util._Snip(self.text, 200, ['lacinia', 'cras']),
                     ('...viverra, libero ex bibendum nibh, eu cursus '
                      'nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
                      'lacinia at, interdum eget metus. Sed ultricies metus '
                      'vitae consequat egestas. Sed lacinia ut augue...Donec '
                      'et nulla enim. Duis malesuada euismod aliquet. Nunc '
                      'augue quam, lobortis a laoreet ac, blandit eu est. '
                      'Fusce justo nulla, egestas a viverra sed, pulvinar '
                      'eget enim. Cras quis cursus lorem.'))
    # With terms close together
    self.assertEqual(search_util._Snip(self.text, 200, ['lacinia', 'metus']),
                     ('...viverra, libero ex bibendum nibh, eu cursus '
                      'nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
                      'lacinia at, interdum eget metus. Sed ultricies metus '
                      'vitae consequat egestas. Sed lacinia ut augue...'))
    # With terms close enough together for their excerpts to be combined.
    self.assertEqual(search_util._Snip(self.text, 200,
                                       ['lacinia', 'scelerisque']),
                     ('...viverra, libero ex bibendum nibh, eu cursus '
                      'nisl risus vitae lorem. Donec lorem nibh, vestibulum a '
                      'lacinia at, interdum eget metus. Sed ultricies metus '
                      'vitae consequat egestas. Sed lacinia ut augue sit amet '
                      'scelerisque. Vestibulum lacinia convallis quam eu '
                      'molestie. Nam pharetra in justo et congue. Vivamus...'))

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


class SummaryTests(search_help_test_base.SearchHelpTestBase):
  """Tests of search_util functions."""

  def testGetSummaryJustCapsule(self):
    # Get a basic summary, just capsule.
    terms_to_locations = {'': lookup.CAPSULE}
    expected_summary = textwrap.dedent("""\
    # SUMMARY DESCRIPTION
    A test command with a long help section.""")
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, terms_to_locations))
    # path and name should do nothing.
    terms_to_locations = {'': lookup.CAPSULE,
                          'random': lookup.PATH,
                          'something': lookup.NAME}
    expected_summary = textwrap.dedent("""\
    # SUMMARY DESCRIPTION
    A test command with a long help section.""")
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, terms_to_locations))
    # Snip the capsule.
    terms_to_locations = {'long': lookup.CAPSULE}
    expected_summary = textwrap.dedent("""\
    # SUMMARY DESCRIPTION
    ...with a long help...""")
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, terms_to_locations,
                                            length_per_snippet=16))

  def testGetSummaryWithAllFlags(self):
    terms_to_locations = {'exactly': lookup.FLAGS}
    expected_summary = (
        '# SUMMARY DESCRIPTION\nBrief description of what '
        'Nothing Happens means.\n'
        '# FLAGS\n'
        '--authority-selector, --authorization-token-file, --configuration, '
        '--credential-file-override, --exactly-one, --exactly-three, '
        '--flatten, --format, --help, --hidden, --http-timeout, --log-http,...'
    )
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.xyzzy, terms_to_locations))

  def testGetSummaryWithFlag(self):
    terms_to_locations = {'': lookup.CAPSULE,
                          'zero': '.'.join([lookup.FLAGS, '--zero-or-one'])}
    expected_summary = textwrap.dedent("""\
    # SUMMARY DESCRIPTION
    Brief description of what Nothing Happens means.
    # FLAGS
    --zero-or-one::
    Zero or one description.""")
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.xyzzy, terms_to_locations))
    # With flag choices and defaults
    terms_to_locations = {'': lookup.CAPSULE,
                          'rachel': '.'.join([lookup.FLAGS, '--three-choices',
                                              lookup.CHOICES]),
                          'curly': '.'.join([lookup.FLAGS, '--exactly-one',
                                             lookup.DEFAULT])}
    expected_summary = """\
# SUMMARY DESCRIPTION
Brief description of what Nothing Happens means.
# FLAGS
--exactly-one::
Exactly one description.
Default: Curly.
--three-choices::
Choices description. _FRIENDS_ must be one of: *rachel*, *phoebe*, *monica*."""
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.xyzzy, terms_to_locations))

  def testGetSummaryWithSection(self):
    terms_to_locations = {'': lookup.CAPSULE,
                          'castle': lookup.SECTIONS + '.DESCRIPTION'}
    expected_summary = (
        '# SUMMARY DESCRIPTION\n'
        'A test command with a long help section.\n'
        '# DESCRIPTION\n'
        '...with a very long help section, and some newlines '
        'and things like that, and weird words including `castle`. '
        'It can be used to test displaying long help, or summarizing it as '
        'for `gcloud search-help`....')
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, terms_to_locations))
    # Multiple terms.
    terms_to_locations = {'': lookup.CAPSULE,
                          'tarantula': lookup.SECTIONS + '.DESCRIPTION',
                          'mittens': lookup.SECTIONS + '.DESCRIPTION'}
    expected_summary = (
        '# SUMMARY DESCRIPTION\n'
        'A test command with a long help section.\n'
        '# DESCRIPTION\n'
        '...or summarizing it as for `gcloud search-help`. If a person is '
        'searching the word `scorpion` or `tarantula`, this sentence should '
        'be in the excerpt. That way they know why they are seeing this '
        'command,'
        '...aren\'t so close to the other terms in the next paragraph. '
        'On the other hand if they aren\'t looking for scary '
        'bugs and are searching the word `mittens`, the excerpt should center '
        'around this part.')
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.long_help, terms_to_locations))

  def testGetSummaryWithPositionals(self):
    # With just a list of positional arguments.
    terms_to_locations = {'': lookup.CAPSULE, 'pdq': lookup.POSITIONALS}
    expected_summary = (
        '# SUMMARY DESCRIPTION\n'
        'Brief description of what Nothing Happens means.\n'
        '# POSITIONALS\n'
        'pdq')
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.xyzzy, terms_to_locations))
    terms_to_locations = {'': lookup.CAPSULE,
                          'the': lookup.POSITIONALS + '.pdq'}
    # Including positional description.
    expected_summary = (
        '# SUMMARY DESCRIPTION\n'
        'Brief description of what Nothing Happens means.\n'
        '# POSITIONALS\n'
        'pdq::\n'
        'pdq the PDQ.')
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.xyzzy, terms_to_locations))

  def testGetSummaryWithCommandGroup(self):
    # With just a list of positional arguments.
    terms_to_locations = {'': lookup.CAPSULE, 'long': lookup.COMMANDS}
    expected_summary = (
        '# SUMMARY DESCRIPTION\n'
        'gcloud sdk tests second level group.\n'
        '# COMMANDS\n'
        'hidden-command, hiddengroup, long-help, second-level-command-1, '
        'second-level-command-b, subgroup, xyzzy'
    )
    # Mimic the first step of replacing 'commands' dict with list of keys.
    sdk_node = copy.deepcopy(self.sdk)
    sdk_node.update(
        {lookup.COMMANDS:
         list(self.sdk.get(lookup.COMMANDS, {}).keys())})
    self.assertEqual(expected_summary,
                     search_util.GetSummary(sdk_node, terms_to_locations))
    # Should still work if the commands dict wasn't changed for some reason.
    self.assertEqual(expected_summary,
                     search_util.GetSummary(self.sdk, terms_to_locations))

  def testGetSummaryWithArbitrarySections(self):
    found_terms = {
        'random': 'randomsection',
        'another': 'sections.anothersection',
        'dict': 'dictsection',
        'number': 'numbersection',
        'three': 'flags.--exactly-three.nonexistentflagsection',
        'nonexistentflag': 'flags.nonexistentflag',
        'nonexistentarg': 'positionals.nonexistentarg'}
    expected_summary = ('# SUMMARY DESCRIPTION\n'
                        'Brief description of what Nothing Happens means.\n'
                        '# FLAGS\n'
                        '--exactly-three::\n'
                        'Exactly three description.\n'
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
    # Test that warnings were logged for sections that weren't found.
    for section in ['randomsection', 'anothersection',
                    'nonexistentflagsection', 'nonexistentflag',
                    'nonexistentarg']:
      self.AssertErrContains(section)

  def testProcessResultWithSummary(self):
    # Test that summary is properly rendered and added to result.
    summary = ('## SUMMARY DESCRIPTION\n'
               'This is a brief description of the command.\n'
               '## FLAGS\n'
               '--flag-name::\n'
               '...part of the flag description goes here. It '
               'is a very long description because we\'re going to see if the '
               'markdown rendering works properly. It should not do any '
               'wrapping of the text, because the table printer is going to do '
               'that for us.')
    self.StartObjectPatch(search_util, 'GetSummary',
                          return_value=summary)
    version_command = self.parent.get(lookup.COMMANDS, {}).get('version', {})
    result = search_util.ProcessResult(version_command, {})
    self.assertEqual(result.get(lookup.COMMANDS, None),
                     [])
    self.assertEqual(result.get(lookup.SUMMARY),
                      ('SUMMARY DESCRIPTION\n'
                       'This is a brief description of the command.\n'
                       'FLAGS\n'
                       '--flag-name\n'
                       '...part of the flag description goes here. It is a '
                       'very long description because we\'re going to see if '
                       'the markdown rendering works properly. It should not '
                       'do any wrapping of the text, because the table printer '
                       'is going to do that for us.'))

  def testLocateTerms(self):
    # Test that terms are correctly located in command.
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'phoebe'),
                     'flags.--three-choices')
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'choices'),
                     'flags.--three-choices')
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'choice(s'),
                     '')
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'moe'),
                     'flags.--exactly-three.default')
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'components'),
                     'sections.EXAMPLES')
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'pdq'),
                     'positionals.pdq')
    # The word 'description appears in the brief description as well as flags.
    # Should only return 'capsule'
    self.assertEqual(search_util.LocateTerm(self.xyzzy, 'description'),
                     'capsule')

  def testLocateTerm_Notes(self):
    """Test that commands don't match if terms are only in ancestor path."""
    # If the terms only occur in the ancestors of the command, do not return.
    # The NOTES section now contains alternate release track commands, so the
    # ancestor of a command will show up in the NOTES section.
    location = search_util.LocateTerm(self.xyzzy, 'sdk')
    self.assertEqual('sections.NOTES', location)

  def testLocateTerm_NameToCapsule(self):
    """Test that term located in name returns 'capsule'."""
    location = search_util.LocateTerm(self.sdk, 'sdk')
    self.assertEqual('capsule', location)


if __name__ == '__main__':
  test_case.main()
