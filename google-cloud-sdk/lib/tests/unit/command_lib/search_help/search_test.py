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

"""Unit tests for help search functionality."""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.search_help import lookup
from googlecloudsdk.command_lib.search_help import search
from googlecloudsdk.core import module_util
from tests.lib.surface import search_help_test_base


class SearchTests(search_help_test_base.SearchHelpTestBase):
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
    self.assertEqual(set(['gcloud sdk long-help', 'gcloud sdk']),
                     set([' '.join(c[lookup.PATH]) for c in results]))

  def testRunSearchWalksAllCommands(self):
    """Test that all commands are hit by Search."""
    def FakeSearch(command):
      return ' '.join(command[lookup.PATH])
    self.StartObjectPatch(search.Searcher, 'PossiblyGetResult',
                          side_effect=FakeSearch)
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
        sorted(search.RunSearch(['term'], self.test_cli)))

  def testPossiblyGetResultNotResult(self):
    """Test PossiblyGetResult returns None when no match is found."""
    searcher = search.Searcher({}, ['tarantula'])
    self.assertIsNone(searcher.PossiblyGetResult(self.xyzzy))
    searcher = search.Searcher({}, ['phoebe'])
    self.assertIsNone(searcher.PossiblyGetResult(self.long_help))

  def testPossiblyGetResultMultipleTermsNotResult(self):
    """Test no result where one term is present and one term is not."""
    searcher = search.Searcher({}, ['phoebe', 'tarantula'])
    self.assertIsNone(searcher.PossiblyGetResult(self.xyzzy))
    self.assertIsNone(searcher.PossiblyGetResult(self.long_help))

  def testPossiblyGetResultSingleTerm(self):
    """Test PossiblyGetResult with a single term that does match."""
    searcher = search.Searcher({}, ['phoebe'])
    result = searcher.PossiblyGetResult(self.xyzzy)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'Brief description of what Nothing Happens means.\n'
                        'FLAGS\n'
                        '--three-choices\n'
                        'Choices description. FRIENDS must be one of: '
                        'rachel, phoebe, monica.')
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultSingleTermPositional(self):
    """Test PossiblyGetResult with a single term that matches a positional."""
    searcher = search.Searcher({}, ['pdq'])
    result = searcher.PossiblyGetResult(self.xyzzy)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'Brief description of what Nothing Happens means.\n'
                        'POSITIONALS\n'
                        'pdq\n'
                        'pdq the PDQ.')
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultSingleTermFlagName(self):
    """Test PossiblyGetResult with a single term that matches a flag name."""
    searcher = search.Searcher({}, ['choices'])
    result = searcher.PossiblyGetResult(self.xyzzy)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'Brief description of what Nothing Happens means.\n'
                        'FLAGS\n'
                        '--three-choices\n'
                        'Choices description. '
                        'FRIENDS must be one of: rachel, phoebe, monica.')
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultSingleTermFlagDefault(self):
    """Test PossiblyGetResult with a single term that matches a flag default.
    """
    searcher = search.Searcher({}, ['moe'])
    result = searcher.PossiblyGetResult(self.xyzzy)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'Brief description of what Nothing Happens means.\n'
                        'FLAGS\n'
                        '--exactly-three\n'
                        'Exactly three description. Default: '
                        'Moe, Larry, Shemp.')
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultMultipleTerms(self):
    """Test PossiblyGetResult with multiple terms."""
    searcher = search.Searcher({}, ['phoebe', 'components'])
    result = searcher.PossiblyGetResult(self.xyzzy)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'Brief description of what Nothing Happens means.\n'
                        'EXAMPLES\n'
                        'Try these: $ echo one $ gcloud components list\n'
                        'FLAGS\n'
                        '--three-choices\n'
                        'Choices description. FRIENDS must be one of: '
                        'rachel, phoebe, monica.')
    expected_result = copy.deepcopy(self.xyzzy)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultWithExcerpt(self):
    """Test PossiblyGetResult correctly excerpts long descriptions."""
    searcher = search.Searcher({}, ['tarantula'])
    result = searcher.PossiblyGetResult(self.long_help)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'A test command with a long help section.\n'
                        'DESCRIPTION\n'
                        '...or summarizing it as for gcloud search-help. If '
                        'a person is searching the word scorpion or '
                        'tarantula, this sentence should be in the excerpt. '
                        'That way they know why they are seeing this '
                        'command,...')
    expected_result = copy.deepcopy(self.long_help)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultWithExcerptTwoTerms(self):
    """Test PossiblyGetResult correctly excerpts when multiple terms match."""
    searcher = search.Searcher({}, ['castle', 'mittens'])
    result = searcher.PossiblyGetResult(self.long_help)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'A test command with a long help section.\n'
                        'DESCRIPTION\n'
                        '...with a very long help section, and some newlines '
                        'and things like that, and weird words including '
                        'castle. It can be used to test displaying long help, '
                        'or summarizing it as for gcloud search-help....'
                        'aren\'t so close to the other terms in the next '
                        'paragraph. On the other hand if they aren\'t looking '
                        'for scary bugs and are searching the word mittens, '
                        'the excerpt should center around this part.')
    expected_result = copy.deepcopy(self.long_help)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: []})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultCommandGroup(self):
    """Test PossiblyGetResult works with a command group."""
    searcher = search.Searcher({}, ['xyzzy', 'second'])
    result = searcher.PossiblyGetResult(self.sdk)
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'gcloud sdk tests second level group.\n'
                        'COMMANDS\n'
                        'long-help, second-level-command-1, '
                        'second-level-command-b, subgroup, xyzzy')
    expected_result = copy.deepcopy(self.sdk)
    expected_result.update(
        {lookup.SUMMARY: expected_summary,
         lookup.COMMANDS: ['long-help', 'second-level-command-1',
                           'second-level-command-b', 'subgroup', 'xyzzy']})
    self.assertEqual(expected_result, result)

  def testPossiblyGetResultCommandGroupSubCommands(self):
    """Test command groups don't match if term is only present in subcommand."""
    # A term that would match for a command in a group should not match
    # the command group (except the command's name)
    # 'eureka' is a positional arg for one of the commands in the subgroup.
    searcher = search.Searcher({}, ['eureka'])
    result = searcher.PossiblyGetResult(self.subgroup)
    self.assertIsNone(result)

  def testPossiblyGetResultAlpha(self):
    """Alpha commands never return."""
    searcher = search.Searcher({}, ['alpha'])
    result = searcher.PossiblyGetResult(
        self.parent.get(lookup.COMMANDS).get('alpha'))
    self.assertIsNone(result)

  def testRunSearchSingleTerm(self):
    """Overall test of search with one term."""
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'A test command with a long help section.\n'
                        'DESCRIPTION\n'
                        '...with a very long help section, and '
                        'some newlines and things like that, and weird words '
                        'including castle. It can be used to test '
                        'displaying long help, or summarizing it as for '
                        'gcloud search-help....')
    expected_result = copy.deepcopy(self.long_help)
    # The result should replace the 'commands' with a list and add a summary.
    expected_result.update({lookup.COMMANDS: [],
                            lookup.SUMMARY: expected_summary})
    result = search.RunSearch(['castle'], self.test_cli)
    self.assertEqual([expected_result], result)

  def testRunSearchMultipleTerms(self):
    """Overall test of search with three search terms."""
    expected_summary = ('SUMMARY DESCRIPTION\n'
                        'gcloud sdk tests second level group.\n'
                        'COMMANDS\n'
                        'long-help, second-level-command-1, '
                        'second-level-command-b, subgroup, xyzzy')
    expected_result = copy.deepcopy(self.sdk)
    expected_result.update({lookup.COMMANDS:
                            ['long-help', 'second-level-command-1',
                             'second-level-command-b', 'subgroup', 'xyzzy'],
                            lookup.SUMMARY: expected_summary})
    result = search.RunSearch(['second', 'xyzzy', 'long'],
                              self.test_cli)
    self.assertEqual([expected_result], result)


if __name__ == '__main__':
  search_help_test_base.main()
