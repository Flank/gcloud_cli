# -*- coding: utf-8 -*- #
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

"""Unit tests for the rater.Rater class."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.help_search import lookup
from googlecloudsdk.command_lib.help_search import rater
from googlecloudsdk.command_lib.help_search import search_util
from tests.lib import parameterized
from tests.lib import test_case


class RaterTest(test_case.TestCase, parameterized.TestCase):
  """Tests of rater."""

  def DummyCommand(self, name='bar', path=None, release=lookup.GA,
                   results=None):
    """Make a dummy command resource."""
    results = results or {}
    path = ['gcloud', 'foo']
    return {
        lookup.NAME: name,
        lookup.PATH: path,
        lookup.RELEASE: release,
        lookup.RESULTS: results}

  @parameterized.named_parameters(
      ('CommandName', lookup.NAME, 1.0),
      ('CommandPath', lookup.PATH, 0.5),
      ('FlagName', '{}.--flag.{}'.format(lookup.FLAGS, lookup.NAME), 0.5),
      ('PositionalName', '{}.POS.{}'.format(lookup.POSITIONALS, lookup.NAME),
       0.5),
      ('FlagDescription',
       '{}.--flag.{}'.format(lookup.FLAGS, lookup.DESCRIPTION), 0.25),
      ('PositionalDescription',
       '{}.--flag.{}'.format(lookup.POSITIONALS, lookup.DESCRIPTION), 0.25),
      ('FlagDefault',
       '{}.--flag.{}'.format(lookup.FLAGS, lookup.DEFAULT), 0.25),
      ('FlagChoices',
       '{}.--flag.{}'.format(lookup.FLAGS, lookup.CHOICES), 0.25),
      ('OtherSection', 'sections.DESCRIPTION', 0.25))
  def testRatingSingleLocation(self, location, expected_rating):
    results = search_util.CommandSearchResults({'t': location})
    command = self.DummyCommand()
    found_commands = [command]
    self.assertEqual(
        expected_rating,
        rater.CommandRater(results, command, found_commands).Rate())

  @parameterized.named_parameters(
      ('OneNotFound', {'t': lookup.NAME, 't1': lookup.NAME, 't2': ''}, 0.1),
      ('TwoNotFound', {'t': lookup.NAME, 't1': '', 't2': ''}, 0.1 ** 2),
      # In the case where no terms are present, we can still rate
      ('ThreeNotFound', {'t': '', 't1': '', 't2': ''}, 0.1 ** 3))
  def testRatingSomeTermsNotFound(self, results_data, expected_rating):
    results = search_util.CommandSearchResults(results_data)
    command = self.DummyCommand()
    found_commands = [command]
    self.assertEqual(
        expected_rating,
        rater.CommandRater(results, command, found_commands).Rate())

  @parameterized.named_parameters(
      ('CommandNameAndPath', {'t': lookup.NAME, 't1': lookup.PATH}, 0.5),
      ('PathAndPath', {'t': lookup.PATH, 't1': lookup.PATH}, 0.25),
      ('PathAndFlagName',
       {'t': lookup.PATH,
        't1': '{}.--flag.{}'.format(lookup.FLAGS, lookup.NAME)}, 0.25),
      ('Other', {'t': 'sections.DESCRIPTION', 't1': 'sections.EXAMPLES'},
       0.25 ** 2))
  def testRatingMultipleLocations(self, results_data, expected_rating):
    results = search_util.CommandSearchResults(results_data)
    command = self.DummyCommand()
    found_commands = [command]
    self.assertEqual(
        expected_rating,
        rater.CommandRater(results, command, found_commands).Rate())

  # The below cases go in order from most to least relevant.
  @parameterized.named_parameters(
      ('NameAndPathOneNotFound',
       {'t': lookup.NAME, 't1': lookup.PATH, 't2': ''},
       0.5 * 0.1),  # 0.05
      ('NameAndFlagNameOneNotFound',
       {'t': lookup.NAME, 't1': '.'.join([lookup.FLAGS, '--flag', lookup.NAME]),
        't2': ''},
       0.5 * 0.1),  # 0.05
      ('PathOneNotFound',
       {'t': lookup.PATH, 't1': lookup.PATH, 't2': ''},
       0.25 * 0.1),  # 0.025
      ('NameAndOtherSectionOneNotFound',
       {'t': lookup.NAME, 't1': 'sections.EXAMPLES', 't2': ''},
       0.25 * 0.1),  # 0.025
      ('NameTwoNotFound',
       {'t': lookup.NAME, 't1': '', 't2': ''},
       0.1 ** 2),  # .01
      ('OtherSectionsOneNotFound',
       {'t': 'sections.EXAMPLES', 't1': 'sections.DESCRIPTION', 't2': ''},
       (0.25 ** 2) * 0.1),  # 0.00625
      ('OtherSectionsTwoNotFound',
       {'t': 'sections.EXAMPLES', 't1': '', 't2': ''},
       0.25 * (0.1 ** 2))  # 0.0025
      )
  def testRatingMultipleLocationsSomeNotFound(self, results_data,
                                              expected_rating):
    results = search_util.CommandSearchResults(results_data)
    command = self.DummyCommand()
    found_commands = [command]
    self.assertEqual(
        expected_rating,
        rater.CommandRater(results, command, found_commands).Rate())

  @parameterized.named_parameters(
      # No penalty for duplicates because this is the highest release track.
      ('GA',
       {'t': 'sections.DESCRIPTION'},
       {'release': lookup.GA},
       [{'release': lookup.ALPHA, 'path': ['gcloud', 'alpha', 'foo']},
        {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
        {'release': lookup.GA}],
       0.25),
      ('Beta',
       {'t': 'sections.DESCRIPTION'},
       {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
       [{'release': lookup.ALPHA, 'path': ['gcloud', 'alpha', 'foo']},
        {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
        {'release': lookup.GA}],
       0.25 * 0.1),
      # Double penalty for two higher release tracks.
      ('Alpha',
       {'t': 'sections.DESCRIPTION'},
       {'release': lookup.ALPHA, 'path': ['gcloud', 'alpha', 'foo']},
       [{'release': lookup.ALPHA, 'path': ['gcloud', 'alpha', 'foo']},
        {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
        {'release': lookup.GA}],
       0.25 * (0.1 ** 2)),
      # There's no GA command, so beta command isn't penalized.
      ('BetaPrimary',
       {'t': 'sections.DESCRIPTION'},
       {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
       [{'release': lookup.ALPHA, 'path': ['gcloud', 'alpha', 'foo']},
        {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']}],
       0.25),
      # The GA command results are different, so the beta command isn't
      # penalized.
      ('BetaGADoesNotMatch',
       {'t': 'section.DESCRIPTION'},
       {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
       [{'release': lookup.ALPHA, 'path': ['gcloud', 'alpha', 'foo']},
        {'release': lookup.BETA, 'path': ['gcloud', 'beta', 'foo']},
        {'release': lookup.GA, 'results': {'t': 'sections.EXAMPLES'}}],
       0.25))
  def testRatingDuplicateCommands(self, results_data, command_kwargs,
                                  found_command_kwargs, expected_rating):
    results = search_util.CommandSearchResults(results_data)
    command = self.DummyCommand(**command_kwargs)
    found_commands = []
    for kwargs in found_command_kwargs:
      found_commands.append(self.DummyCommand(**kwargs))
    self.assertEqual(
        expected_rating,
        rater.CommandRater(results, command, found_commands).Rate())

  def testCumulativeRater(self):
    cumulative_rater = rater.CumulativeRater()
    alpha_command = self.DummyCommand(
        release=lookup.ALPHA,
        path=['gcloud', 'alpha', 'foo'],
        results={'t': 'sections.DESCRIPTION'})
    beta_command = self.DummyCommand(
        release=lookup.BETA,
        path=['gcloud', 'beta', 'foo'],
        results={'t': 'sections.DESCRIPTION'})
    ga_command = self.DummyCommand(
        release=lookup.ALPHA,
        results={'t': 'sections.EXAMPLES'})

    cumulative_rater.AddFoundCommand(
        alpha_command,
        search_util.CommandSearchResults({'t': 'sections.DESCRIPTION'}))
    cumulative_rater.AddFoundCommand(
        beta_command,
        search_util.CommandSearchResults({'t': 'sections.DESCRIPTION'}))
    cumulative_rater.AddFoundCommand(
        ga_command,
        search_util.CommandSearchResults({'t': 'sections.EXAMPLES'}))
    cumulative_rater.RateAll()

    self.assertEqual(0.25 * 0.1, alpha_command[lookup.RELEVANCE])
    self.assertEqual(0.25, beta_command[lookup.RELEVANCE])
    self.assertEqual(0.25, ga_command[lookup.RELEVANCE])


if __name__ == '__main__':
  test_case.main()
