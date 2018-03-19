# Copyright 2018 Google Inc. All Rights Reserved.
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

"""e2e tests for the 'dataproc workflow-templates' commands."""

import contextlib

from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import e2e_base


# TODO(b/74369111): Add non-iam-policy e2e tests for workflow-templates.
class WorkflowTemplatesE2ETest(e2e_base.DataprocIntegrationTestBase,
                               base.DataprocTestBaseBeta):

  def SetUp(self):
    self.name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='workflow_templates_test')

  def testWorkflowTemplateGetSetIAMPolicy(self):
    name = self.name_generator.next()
    with self.CreateWorkflowTemplate(name) as _:
      self.GetSetIAMPolicy('workflow-templates', name)

  @contextlib.contextmanager
  def CreateWorkflowTemplate(self, name):
    try:
      resource = self.RunDataproc('workflow-templates create {0}'.format(name))
      yield resource
    finally:
      self.RunDataproc('workflow-templates delete {0}'.format(name))


if __name__ == '__main__':
  sdk_test_base.main()
