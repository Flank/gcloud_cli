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

"""Unit tests for help search functionality."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.help_search import lookup
from googlecloudsdk.command_lib.help_search import search
from googlecloudsdk.core import module_util
from tests.lib import test_case
from tests.lib.surface import help_search_test_base


class SearchTests(help_search_test_base.HelpSearchTestBase):
  """Tests of search.RunSearch and search.Searcher."""

  def testUpdateTableHappensOnFirstRun(self):
    """Test that Search updates table if it doesn't exist, not every time."""
    # Mock that CLI tree path import fails.
    import_module_mock = self.StartObjectPatch(module_util, 'ImportModule')
    import_module_mock.side_effect = module_util.ImportModuleError
    table_update_mock = self.StartObjectPatch(cli_tree, 'Dump')

    # The table update should happen when the table doesn't exist, but SetUp()
    # already created it, so we don't expect any more updates.
    search.RunSearch(['term'], self.test_cli)
    table_update_mock.assert_not_called()

    # The table update shouldn't happen again.
    import_module_mock.side_effect = None
    search.RunSearch(['otherterm'], self.test_cli)
    table_update_mock.assert_not_called()

  def testSdkRootError(self):
    """Test that Search runs with cli if help index not available."""
    # Mock that there is an error getting the SDK root.
    self.StartObjectPatch(cli_tree, 'CliTreePath',
                          side_effect=cli_tree.SdkRootNotFoundError)
    table_update_mock = self.StartObjectPatch(cli_tree, 'Dump')
    results = search.RunSearch(['long-help'], self.test_cli)
    # The table update should not happen in this case.
    table_update_mock.assert_not_called()
    self.AssertErrContains(
        'Generating the gcloud CLI for one-time use (no SDK root)')
    # Assert that results are found.
    self.assertEqual({'gcloud sdk long-help', 'gcloud sdk'},
                     set([' '.join(c[lookup.PATH]) for c in results]))

  def testRunSearchWalksAllCommands(self):
    """Test that all commands are hit by Search."""
    def FakeSearch(command):
      return ' '.join(command[lookup.PATH])
    self.StartObjectPatch(search.Searcher, '_PossiblyGetResult',
                          side_effect=FakeSearch)
    searcher = search.Searcher(
        parent=cli_tree.Load(cli=self.test_cli, one_time_use_ok=True),
        terms=['term']
    )
    self.assertEqual(
        [
            'gcloud',
            'gcloud alpha',
            'gcloud alpha internal',
            'gcloud alpha internal internal-command',
            'gcloud alpha sdk',
            'gcloud alpha sdk alphagroup',
            'gcloud alpha sdk alphagroup alpha-command',
            'gcloud alpha sdk hidden-command',
            'gcloud alpha sdk hiddengroup',
            'gcloud alpha sdk hiddengroup hidden-command-2',
            'gcloud alpha sdk hiddengroup hidden-command-a',
            'gcloud alpha sdk long-help',
            'gcloud alpha sdk second-level-command-1',
            'gcloud alpha sdk second-level-command-b',
            'gcloud alpha sdk subgroup',
            'gcloud alpha sdk subgroup subgroup-command-2',
            'gcloud alpha sdk subgroup subgroup-command-a',
            'gcloud alpha sdk xyzzy',
            'gcloud alpha version',
            'gcloud beta',
            'gcloud beta internal',
            'gcloud beta internal internal-command',
            'gcloud beta sdk',
            'gcloud beta sdk betagroup',
            'gcloud beta sdk betagroup beta-command',
            'gcloud beta sdk betagroup sub-command-2',
            'gcloud beta sdk betagroup sub-command-a',
            'gcloud beta sdk hidden-command',
            'gcloud beta sdk hiddengroup',
            'gcloud beta sdk hiddengroup hidden-command-2',
            'gcloud beta sdk hiddengroup hidden-command-a',
            'gcloud beta sdk long-help',
            'gcloud beta sdk second-level-command-1',
            'gcloud beta sdk second-level-command-b',
            'gcloud beta sdk subgroup',
            'gcloud beta sdk subgroup subgroup-command-2',
            'gcloud beta sdk subgroup subgroup-command-a',
            'gcloud beta sdk xyzzy',
            'gcloud beta version',
            'gcloud internal',
            'gcloud internal internal-command',
            'gcloud sdk',
            'gcloud sdk hidden-command',
            'gcloud sdk hiddengroup',
            'gcloud sdk hiddengroup hidden-command-2',
            'gcloud sdk hiddengroup hidden-command-a',
            'gcloud sdk long-help',
            'gcloud sdk second-level-command-1',
            'gcloud sdk second-level-command-b',
            'gcloud sdk subgroup',
            'gcloud sdk subgroup subgroup-command-2',
            'gcloud sdk subgroup subgroup-command-a',
            'gcloud sdk xyzzy',
            'gcloud version',
        ],
        sorted(searcher._WalkTree(searcher.parent, [])))

  def testPossiblyGetResultNotResult(self):
    """Test _PossiblyGetResult returns None when no match is found."""
    searcher = search.Searcher({}, ['tarantula'])
    self.assertIsNone(searcher._PossiblyGetResult(self.xyzzy))  # pylint: disable=protected-access
    searcher = search.Searcher({}, ['phoebe'])
    self.assertIsNone(searcher._PossiblyGetResult(self.long_help))  # pylint: disable=protected-access

  def testPossiblyGetResultSingleTerm(self):
    """Test _PossiblyGetResult with a single term that does match."""
    searcher = search.Searcher({}, ['phoebe'])
    result = searcher._PossiblyGetResult(self.xyzzy)  # pylint: disable=protected-access
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.RESULTS: {'phoebe': 'flags.--three-choices.choices'},
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultSingleTermPositional(self):
    """Test _PossiblyGetResult with a single term that matches a positional."""
    searcher = search.Searcher({}, ['pdq'])
    result = searcher._PossiblyGetResult(self.xyzzy)  # pylint: disable=protected-access
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.RESULTS: {'pdq': 'positionals.pdq.name'},
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultSingleTermFlagName(self):
    """Test _PossiblyGetResult with a single term that matches a flag name."""
    searcher = search.Searcher({}, ['choices'])
    result = searcher._PossiblyGetResult(self.xyzzy)  # pylint: disable=protected-access
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.RESULTS: {'choices': 'flags.--three-choices.name'},
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultSingleTermFlagDefault(self):
    """Test _PossiblyGetResult with a single term that matches a flag default.
    """
    searcher = search.Searcher({}, ['moe'])
    result = searcher._PossiblyGetResult(self.xyzzy)  # pylint: disable=protected-access
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.RESULTS: {'moe': 'flags.--exactly-three.default'},
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultMultipleTermsOnePresent(self):
    """Test we get a result where one term is present and one term is not."""
    searcher = search.Searcher({}, ['phoebe', 'tarantula'])
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.RESULTS: {'phoebe': 'flags.--three-choices.choices'},
         lookup.COMMANDS: []})
    self.assertEqual(
        expected_result,
        searcher._PossiblyGetResult(self.xyzzy))  # pylint: disable=protected-access

  def testPossiblyGetResultMultipleTermsBothFound(self):
    """Test _PossiblyGetResult with multiple terms."""
    searcher = search.Searcher({}, ['phoebe', 'components'])
    result = searcher._PossiblyGetResult(self.xyzzy)  # pylint: disable=protected-access
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.RESULTS: {'phoebe': 'flags.--three-choices.choices',
                          'components': 'sections.EXAMPLES'},
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultCommandGroup(self):
    """Test _PossiblyGetResult works with a command group."""
    searcher = search.Searcher({}, ['xyzzy', 'second'])
    result = searcher._PossiblyGetResult(self.sdk)  # pylint: disable=protected-access
    expected_result = copy.deepcopy(self.sdk)
    expected_result.update(
        {lookup.RESULTS: {'xyzzy': 'commands',
                          'second': 'capsule'},
         lookup.COMMANDS: ['long-help', 'second-level-command-1',
                           'second-level-command-b', 'subgroup', 'xyzzy']})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultCommandGroupSubCommands(self):
    """Test command groups don't match if term is only present in subcommand."""
    # A term that would match for a command in a group should not match
    # the command group (except the command's name)
    # 'eureka' is a positional arg for one of the commands in the subgroup.
    searcher = search.Searcher({}, ['eureka'])
    result = searcher._PossiblyGetResult(self.subgroup)  # pylint: disable=protected-access
    self.assertIsNone(result)

  def testRunSearchSingleTerm(self):
    """Overall test of search with one term."""
    long_help = copy.deepcopy(self.long_help)
    long_help.update(
        {lookup.RESULTS: {'castle': 'sections.DESCRIPTION'},
         lookup.COMMANDS: [],
         lookup.RELEVANCE: 0.25})
    alpha = copy.deepcopy(self.parent.get(lookup.COMMANDS, {}).get(
        'alpha', {}).get(lookup.COMMANDS, {}).get('sdk', {}).get(
            lookup.COMMANDS, {}).get('long-help', {}))
    alpha.update(
        {lookup.RESULTS: {'castle': 'sections.DESCRIPTION'},
         lookup.COMMANDS: [],
         lookup.RELEVANCE: 0.25 * (0.1 ** 2)})

    beta = copy.deepcopy(self.parent.get(lookup.COMMANDS, {}).get(
        'beta', {}).get(lookup.COMMANDS, {}).get('sdk', {}).get(
            lookup.COMMANDS, {}).get('long-help', {}))
    beta.update(
        {lookup.RESULTS: {'castle': 'sections.DESCRIPTION'},
         lookup.COMMANDS: [],
         lookup.RELEVANCE: 0.25 * 0.1})

    result = search.RunSearch(['castle'], self.test_cli)
    self.assertIn(long_help, result)
    self.assertEqual(1, len(result))

  def testRunSearchMultipleTerms(self):
    """Overall test of search with three search terms."""
    sdk = copy.deepcopy(self.sdk)
    sdk.update(
        {lookup.COMMANDS: ['long-help', 'second-level-command-1',
                           'second-level-command-b', 'subgroup', 'xyzzy'],
         lookup.RESULTS: {'second': 'capsule',
                          'xyzzy': 'commands',
                          'long': 'commands'},
         lookup.RELEVANCE: 0.25 ** 3})
    xyzzy = copy.deepcopy(self.xyzzy)
    xyzzy.update(
        {lookup.COMMANDS: [],
         lookup.RESULTS: {'xyzzy': lookup.NAME},
         lookup.RELEVANCE: 1.0 * (0.1 ** 2)})
    result = search.RunSearch(['second', 'xyzzy', 'long'],
                              self.test_cli)
    self.assertIn(sdk, result)
    self.assertIn(xyzzy, result)
    self.assertEqual(
        {'xyzzy', 'sdk', 'long-help', 'second-level-command-b',
         'second-level-command-1'},
        set([command[lookup.NAME] for command in result]))


if __name__ == '__main__':
  test_case.main()
