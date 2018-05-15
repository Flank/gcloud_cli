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

"""Unit tests for the Cloud Resource Manager filter rewrite module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.cloudresourcemanager import filter_rewrite
from tests.lib import subtests
from tests.lib import test_case


class CloudResourceManagerListFilterRewriteTest(subtests.Base):

  def SetUp(self):
    self.rewrite = filter_rewrite.ListRewriter().Rewrite

  def RunSubTest(self, expression):
    return self.rewrite(expression)

  def testListFilterRewriter(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    T((None, None),
      None)
    T((None, None),
      '')

    T((None, 'id:foo'),
      'id:foo')
    T((None, 'labels.tier:prod'),
      'labels.tier:prod')
    T((None, 'name:bar'),
      'name:bar')

    T((None, 'id:foo'),
      'projectId:foo')
    T((None, 'name:bar'),
      'projectName:bar')

    T((None, 'id:foo'),
      'project_id:foo')
    T((None, 'name:bar'),
      'project_name:bar')

    T((None, 'id:foo AND (labels.tier:prod AND name:bar)'),
      'id:foo AND labels.tier:prod AND name:bar')
    T((None, 'id:foo AND (labels.tier:prod AND name:bar)'),
      'id:foo labels.tier:prod name:bar')
    T((None, 'id:foo AND (labels.tier:prod OR name:bar)'),
      'id:foo AND (labels.tier:prod OR name:bar)')
    T((None, '(id:foo AND labels.tier:prod) OR name:bar'),
      '(id:foo AND labels.tier:prod) OR name:bar')
    T((None, 'id:foo OR (labels.tier:prod AND name:bar)'),
      'id:foo OR (labels.tier:prod AND name:bar)')
    T((None, '(id:foo OR labels.tier:prod) AND name:bar'),
      '(id:foo OR labels.tier:prod) AND name:bar')
    T((None, '(id:foo OR labels.@xyz:prod) AND name:bar'),
      '(id:foo OR labels.@xyz:prod) AND name:bar')
    T((None, '(id:foo OR labels.abc@xyz:prod) AND name:bar'),
      '(id:foo OR labels.abc@xyz:prod) AND name:bar')
    T((None, '(id:foo OR labels.abc-xyz:prod) AND name:bar'),
      '(id:foo OR labels.abc-xyz:prod) AND name:bar')
    T((None, '(id:foo OR labels."abc+xyz":prod) AND name:bar'),
      '(id:foo OR labels."abc+xyz":prod) AND name:bar')

    T(('id:foo AND (unknown:prod OR name:bar)', 'id:foo'),
      'id:foo AND (unknown:prod OR name:bar)')
    T(('id:foo (unknown:prod OR name:bar)', 'id:foo'),
      'id:foo (unknown:prod OR name:bar)')
    T(('id:foo OR (unknown:prod AND name:bar)', 'id:foo OR name:bar'),
      'id:foo OR (unknown:prod AND name:bar)')
    T(('id:foo OR (unknown:prod name:bar)', 'id:foo OR name:bar'),
      'id:foo OR (unknown:prod name:bar)')

    T((None, 'createTime:-P1Y AND id:foo'),
      'create_time:-P1Y id:foo')

    T((None, 'id=foo'),
      'id=foo')
    T((None, 'labels.tier=prod'),
      'labels.tier=prod')
    T((None, 'name=bar'),
      'name=bar')
    T((None, 'NOT (name=bar)'),
      'name!=bar')

    T((None, 'NOT name:bar'),
      '-name:bar')
    T((None, 'id:foo OR (labels.tier:prod OR name:bar)'),
      'id:foo OR labels.tier:prod OR name:bar')
    T((None, 'id:foo OR id:bar'),
      'id:foo OR id:bar')
    T((None, '( id:foo OR id:bar )'),
      'id:(foo bar)')

    T((None, None),
      'id:foo AND labels.tier:prod OR name:bar',
      exception=('Parenthesis grouping is required when AND and OR are are '
                 'combined [id:foo AND labels.tier:prod OR *HERE* name:bar].'))
    T((None, 'id:foo AND (labels.tier:prod OR name:bar)'),
      'id:foo labels.tier:prod OR name:bar')

    T((None, 'parent.id:1234'),
      'parent.id:1234')
    T((None, 'parent.type:folder'),
      'parent.type:folder')
    T((None, 'lifecycleState:ACTIVE'),
      'lifecycleState:ACTIVE')
    T((None, 'lifecycleState:ACTIVE'),
      'lifecycle_state:ACTIVE')
    T((None,
       'parent.id:1234 AND (parent.type:folder AND lifecycleState:ACTIVE)'),
      'parent.id:1234 parent.type:folder lifecycleState:ACTIVE')


if __name__ == '__main__':
  test_case.main()
