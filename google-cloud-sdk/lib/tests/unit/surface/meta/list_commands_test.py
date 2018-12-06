# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for gcloud meta list-commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import walker
from tests.lib import calliope_test_base


class ListCommandsTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.WalkTestCli('sdk3')
    def MockWalk(unused_hidden, unused_restrict):
      return {'_name_': 'test'}

    self.walk = self.StartObjectPatch(walker.Walker, 'Walk')
    self.walk.side_effect = MockWalk

  def testListCommandsNoRestrictions(self):
    self.Run(['meta', 'list-commands'])
    self.walk.assert_called_once_with(False, [])

  def testListCommandsOneRestriction(self):
    self.Run(['meta', 'list-commands', 'meta'])
    self.walk.assert_called_once_with(False, ['meta'])

  def testListCommandsTwoRestrictions(self):
    self.Run(['meta', 'list-commands', 'meta', 'compute'])
    self.walk.assert_called_once_with(False, ['meta', 'compute'])

  def testListCommandsHiddenNoRestrictions(self):
    self.Run(['meta', 'list-commands', '--hidden'])
    self.walk.assert_called_once_with(True, [])

  def testListCommandsHiddenOneRestriction(self):
    self.Run(['meta', 'list-commands', '--hidden', 'meta'])
    self.walk.assert_called_once_with(True, ['meta'])

  def testListCommandsHiddenTwoRestrictions(self):
    self.Run(['meta', 'list-commands', '--hidden', 'meta', 'compute'])
    self.walk.assert_called_once_with(True, ['meta', 'compute'])

  def testListCommandsBadFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --No-SuCh-FlAg'):
      self.Run(['meta', 'list-commands', '--No-SuCh-FlAg'])


class RunListCommandsHiddenTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.WalkTestCli('sdk3')

  def testListCommandsNonHidden(self):
    """Test the list of the non-hidden commands via Run()."""
    self.Run('meta list-commands')
    self.AssertOutputEquals("""\
gcloud
gcloud markdown
gcloud markdown markdown-command
""")

  def testListCommandsNonHiddenFlags(self):
    """Test the list of the non-hidden commands with flags via Run()."""
    self.Run('meta list-commands --flags')
    self.AssertOutputEquals("""\
gcloud ---flag-file-line- --authority-selector --authorization-token-file --configuration --credential-file-override --document --flags-file --flatten --format --help --http-timeout --log-http --top-group-flag --user-output-enabled --verbosity -h
gcloud markdown
gcloud markdown markdown-command --choices-dict --choices-dict-arg-list --choices-dict-bloviate --choices-dict-only-one-choice-yes-we-really-do-this --choices-list --choices-list-arg-list --choices-list-only-one-choice-yes-we-really-do-this --dict-flag --filter --list-flag --optional-flag --question-flag --root-flag --store-false-default-false-flag --store-false-default-none-flag --store-false-default-true-flag --store-true-default-false-flag --store-true-default-none-flag --store-true-default-true-flag --value-flag --y-common-flag --z-required-flag
""")

  def testListCommandsNonHiddenFlagsValues(self):
    """Test the list of the non-hidden commands with flags/values via Run()."""
    self.Run('meta list-commands --flags --flag-values')
    self.AssertOutputEquals("""\
gcloud ---flag-file-line-=:FLAG_FILE_LINE_: --authority-selector=:AUTHORITY_SELECTOR: --authorization-token-file=:AUTHORIZATION_TOKEN_FILE: --configuration=:CONFIGURATION: --credential-file-override=:CREDENTIAL_FILE_OVERRIDE: --document=:dict: --flags-file=:YAML_FILE: --flatten=:list: --format=:FORMAT: --help --http-timeout=:HTTP_TIMEOUT: --log-http --top-group-flag=:TOP_GROUP_FLAG: --user-output-enabled --verbosity=critical,debug,error,info,none,warning -h
gcloud markdown
gcloud markdown markdown-command --choices-dict-arg-list=:list: --choices-dict-bloviate=bar,foo,none --choices-dict-only-one-choice-yes-we-really-do-this=this-is-it --choices-dict=bar,foo,none --choices-list-arg-list=:list: --choices-list-only-one-choice-yes-we-really-do-this=this-is-it --choices-list=bar,foo,none --dict-flag=:dict: --filter=:EXPRESSION: --list-flag=:list: --optional-flag=:OPTIONAL_FLAG: --question-flag=:QUESTION_FLAG: --root-flag=:ROOT_PATH: --store-false-default-false-flag --store-false-default-none-flag --store-false-default-true-flag --store-true-default-false-flag --store-true-default-none-flag --store-true-default-true-flag --value-flag=:VALUE_FLAG: --y-common-flag=:Y_COMMON_FLAG: --z-required-flag=:Z_REQUIRED_FLAG:
""")

  def testListCommandsHidden(self):
    """Test the list of the non-hidden commands via Run()."""
    self.Run('meta list-commands --hidden')
    self.AssertOutputEquals("""\
gcloud
gcloud hidden-group
gcloud hidden-group hidden-command
gcloud markdown
gcloud markdown markdown-command
""")

  def testListCommandsHiddenFlags(self):
    """Test the list of the non-hidden commands via Run()."""
    self.Run('meta list-commands --hidden --flags')
    self.AssertOutputEquals("""\
gcloud ---flag-file-line- --authority-selector --authorization-token-file --configuration --credential-file-override --document --flags-file --flatten --format --help --http-timeout --log-http --top-group-flag --user-output-enabled --verbosity -h
gcloud hidden-group
gcloud hidden-group hidden-command
gcloud markdown
gcloud markdown markdown-command --choices-dict --choices-dict-arg-list --choices-dict-bloviate --choices-dict-only-one-choice-yes-we-really-do-this --choices-list --choices-list-arg-list --choices-list-only-one-choice-yes-we-really-do-this --dict-flag --filter --list-flag --optional-flag --question-flag --root-flag --store-false-default-false-flag --store-false-default-none-flag --store-false-default-true-flag --store-true-default-false-flag --store-true-default-none-flag --store-true-default-true-flag --value-flag --y-common-flag --z-required-flag
""")


class RunListCommandsSubGroupTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.WalkTestCli('sdk4')

  def testListCommandsAll(self):
    """Test the list of all commands via Run()."""
    self.Run('meta list-commands')
    self.AssertOutputEquals("""\
gcloud
gcloud alpha
gcloud alpha internal
gcloud alpha internal internal-command
gcloud alpha sdk
gcloud alpha sdk alphagroup
gcloud alpha sdk ordered-choices
gcloud alpha sdk second-level-command-1
gcloud alpha sdk second-level-command-b
gcloud alpha sdk subgroup
gcloud alpha sdk subgroup subgroup-command-2
gcloud alpha sdk subgroup subgroup-command-a
gcloud alpha sdk xyzzy
gcloud alpha version
gcloud beta
gcloud beta internal
gcloud beta internal internal-command
gcloud beta sdk
gcloud beta sdk betagroup
gcloud beta sdk betagroup beta-command
gcloud beta sdk betagroup sub-command-2
gcloud beta sdk betagroup sub-command-a
gcloud beta sdk ordered-choices
gcloud beta sdk second-level-command-1
gcloud beta sdk second-level-command-b
gcloud beta sdk subgroup
gcloud beta sdk subgroup subgroup-command-2
gcloud beta sdk subgroup subgroup-command-a
gcloud beta sdk xyzzy
gcloud beta version
gcloud internal
gcloud internal internal-command
gcloud sdk
gcloud sdk ordered-choices
gcloud sdk second-level-command-1
gcloud sdk second-level-command-b
gcloud sdk subgroup
gcloud sdk subgroup subgroup-command-2
gcloud sdk subgroup subgroup-command-a
gcloud sdk xyzzy
gcloud version
""")

  def testListCommandsSubGroup(self):
    """Test the list of the sdk subgroup commands via Run()."""
    self.Run('meta list-commands gcloud.sdk')
    self.AssertOutputEquals("""\
gcloud
gcloud sdk
gcloud sdk ordered-choices
gcloud sdk second-level-command-1
gcloud sdk second-level-command-b
gcloud sdk subgroup
gcloud sdk subgroup subgroup-command-2
gcloud sdk subgroup subgroup-command-a
gcloud sdk xyzzy
""")


class RunListCommandsCompletionsTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.WalkTestCli('sdk4')

  def testListCommandsAll(self):
    """Test the completions list of all commands via Run()."""
    self.Run('meta list-commands --completions')
    self.AssertOutputContains("""\
_SC__GCLOUD_WIDE_FLAGS_=(---flag-file-line-=:FLAG_FILE_LINE_: --authority-selector=:AUTHORITY_SELECTOR: --authorization-token-file=:AUTHORIZATION_TOKEN_FILE: --configuration=:CONFIGURATION: --credential-file-override=:CREDENTIAL_FILE_OVERRIDE: --document=:dict: --flags-file=:YAML_FILE: --flatten=:list: --format=:FORMAT: --help --http-timeout=:HTTP_TIMEOUT: --log-http --user-output-enabled --verbosity=critical,debug,error,info,none,warning -h)
_SC_gcloud=(version alpha beta internal sdk)
_SC_gcloud__version=()
_SC_gcloud__alpha=(version internal sdk)
_SC_gcloud__alpha__version=()
_SC_gcloud__alpha__internal=(internal-command)
_SC_gcloud__alpha__internal__internal_command=()
_SC_gcloud__alpha__sdk=(hidden-command ordered-choices second-level-command-1 second-level-command-b xyzzy alphagroup hiddengroup subgroup)
_SC_gcloud__alpha__sdk__hidden_command=()
_SC_gcloud__alpha__sdk__ordered_choices=(--ordered-choices=a-100g,a-10g,a-1g)
_SC_gcloud__alpha__sdk__second_level_command_1=()
_SC_gcloud__alpha__sdk__second_level_command_b=()
_SC_gcloud__alpha__sdk__xyzzy=(--exactly-one=:STOOGE: --exactly-three=:STOOGE: --hidden --one-or-more=:ATTRIBUTE: --zero-or-more=:ZERO_OR_MORE: --zero-or-one=:ZERO_OR_ONE:)
_SC_gcloud__alpha__sdk__hiddengroup=(hidden-command-2 hidden-command-a)
_SC_gcloud__alpha__sdk__hiddengroup__hidden_command_2=()
_SC_gcloud__alpha__sdk__hiddengroup__hidden_command_a=()
_SC_gcloud__alpha__sdk__subgroup=(subgroup-command-2 subgroup-command-a)
_SC_gcloud__alpha__sdk__subgroup__subgroup_command_2=()
_SC_gcloud__alpha__sdk__subgroup__subgroup_command_a=(--delete-in=:DELETE_IN: --delete-on=:DELETE_ON: --obsolete-in=:OBSOLETE_IN: --obsolete-on=:OBSOLETE_ON:)
_SC_gcloud__beta=(version internal sdk)
_SC_gcloud__beta__version=()
_SC_gcloud__beta__internal=(internal-command)
_SC_gcloud__beta__internal__internal_command=()
_SC_gcloud__beta__sdk=(hidden-command ordered-choices second-level-command-1 second-level-command-b xyzzy betagroup hiddengroup subgroup)
_SC_gcloud__beta__sdk__hidden_command=()
_SC_gcloud__beta__sdk__ordered_choices=(--ordered-choices=a-100g,a-10g,a-1g)
_SC_gcloud__beta__sdk__second_level_command_1=()
_SC_gcloud__beta__sdk__second_level_command_b=()
_SC_gcloud__beta__sdk__xyzzy=(--exactly-one=:STOOGE: --exactly-three=:STOOGE: --hidden --one-or-more=:ATTRIBUTE: --zero-or-more=:ZERO_OR_MORE: --zero-or-one=:ZERO_OR_ONE:)
_SC_gcloud__beta__sdk__betagroup=(beta-command sub-command-2 sub-command-a --location=:LOCATION:)
_SC_gcloud__beta__sdk__betagroup__beta_command=(--location=:LOCATION:)
_SC_gcloud__beta__sdk__betagroup__sub_command_2=(--location=:LOCATION:)
_SC_gcloud__beta__sdk__betagroup__sub_command_a=(--location=:LOCATION: --one-two-three=1,2,3 --resourceful=:RESOURCEFUL:)
_SC_gcloud__beta__sdk__hiddengroup=(hidden-command-2 hidden-command-a)
_SC_gcloud__beta__sdk__hiddengroup__hidden_command_2=()
_SC_gcloud__beta__sdk__hiddengroup__hidden_command_a=()
_SC_gcloud__beta__sdk__subgroup=(subgroup-command-2 subgroup-command-a)
_SC_gcloud__beta__sdk__subgroup__subgroup_command_2=()
_SC_gcloud__beta__sdk__subgroup__subgroup_command_a=(--delete-in=:DELETE_IN: --delete-on=:DELETE_ON: --obsolete-in=:OBSOLETE_IN: --obsolete-on=:OBSOLETE_ON:)
_SC_gcloud__internal=(internal-command)
_SC_gcloud__internal__internal_command=()
_SC_gcloud__sdk=(hidden-command ordered-choices second-level-command-1 second-level-command-b xyzzy hiddengroup subgroup)
_SC_gcloud__sdk__hidden_command=()
_SC_gcloud__sdk__ordered_choices=(--ordered-choices=a-100g,a-10g,a-1g)
_SC_gcloud__sdk__second_level_command_1=()
_SC_gcloud__sdk__second_level_command_b=()
_SC_gcloud__sdk__xyzzy=(--exactly-one=:STOOGE: --exactly-three=:STOOGE: --hidden --one-or-more=:ATTRIBUTE: --zero-or-more=:ZERO_OR_MORE: --zero-or-one=:ZERO_OR_ONE:)
_SC_gcloud__sdk__hiddengroup=(hidden-command-2 hidden-command-a)
_SC_gcloud__sdk__hiddengroup__hidden_command_2=()
_SC_gcloud__sdk__hiddengroup__hidden_command_a=()
_SC_gcloud__sdk__subgroup=(subgroup-command-2 subgroup-command-a)
_SC_gcloud__sdk__subgroup__subgroup_command_2=()
_SC_gcloud__sdk__subgroup__subgroup_command_a=(--delete-in=:DELETE_IN: --delete-on=:DELETE_ON: --obsolete-in=:OBSOLETE_IN: --obsolete-on=:OBSOLETE_ON:)
""")

  def testListCommandsSubGroup(self):
    """Test the completions list of the sdk subgroup commands via Run()."""
    self.Run('meta list-commands --completions gcloud.sdk')
    self.AssertOutputContains("""\
_SC__GCLOUD_WIDE_FLAGS_=(---flag-file-line-=:FLAG_FILE_LINE_: --authority-selector=:AUTHORITY_SELECTOR: --authorization-token-file=:AUTHORIZATION_TOKEN_FILE: --configuration=:CONFIGURATION: --credential-file-override=:CREDENTIAL_FILE_OVERRIDE: --document=:dict: --flags-file=:YAML_FILE: --flatten=:list: --format=:FORMAT: --help --http-timeout=:HTTP_TIMEOUT: --log-http --user-output-enabled --verbosity=critical,debug,error,info,none,warning -h)
_SC_gcloud=(sdk)
_SC_gcloud__sdk=(hidden-command ordered-choices second-level-command-1 second-level-command-b xyzzy hiddengroup subgroup)
_SC_gcloud__sdk__hidden_command=()
_SC_gcloud__sdk__ordered_choices=(--ordered-choices=a-100g,a-10g,a-1g)
_SC_gcloud__sdk__second_level_command_1=()
_SC_gcloud__sdk__second_level_command_b=()
_SC_gcloud__sdk__xyzzy=(--exactly-one=:STOOGE: --exactly-three=:STOOGE: --hidden --one-or-more=:ATTRIBUTE: --zero-or-more=:ZERO_OR_MORE: --zero-or-one=:ZERO_OR_ONE:)
_SC_gcloud__sdk__hiddengroup=(hidden-command-2 hidden-command-a)
_SC_gcloud__sdk__hiddengroup__hidden_command_2=()
_SC_gcloud__sdk__hiddengroup__hidden_command_a=()
_SC_gcloud__sdk__subgroup=(subgroup-command-2 subgroup-command-a)
_SC_gcloud__sdk__subgroup__subgroup_command_2=()
_SC_gcloud__sdk__subgroup__subgroup_command_a=(--delete-in=:DELETE_IN: --delete-on=:DELETE_ON: --obsolete-in=:OBSOLETE_IN: --obsolete-on=:OBSOLETE_ON:)
""")


if __name__ == '__main__':
  calliope_test_base.main()
