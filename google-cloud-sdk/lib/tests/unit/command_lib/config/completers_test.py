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

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import properties
from tests.lib import completer_test_base


class CompletersTest(completer_test_base.CompleterBase):

  def testComputeRegionPropertyValueCompleter(self):
    properties.VALUES.core.project.Set('my-project')
    completer = self.Completer(
        completers.PropertyValueCompleter, args={'property': 'compute/region'})
    self.assertEqual(['us-east1'],
                     completer.Complete('us-east', self.parameter_info))

  def testComputeZonePropertyValueCompleter(self):
    properties.VALUES.core.project.Set('my-project')
    completer = self.Completer(
        completers.PropertyValueCompleter, args={'property': 'compute/zone'})
    self.assertEqual(['us-east1-b', 'us-east1-c', 'us-east1-d'],
                     completer.Complete('us-east', self.parameter_info))


if __name__ == '__main__':
  completer_test_base.main()
