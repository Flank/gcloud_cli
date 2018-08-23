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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.config.configurations import test_base


class ListTest(test_base.ConfigurationsBaseTest):

  def testMissingConfigDirOk(self):
    self.Run('config configurations list')
    # configuration is auto created
    self.AssertOutputContains('default True', normalize_space=True)

  def testListOk(self):
    files.MakeDir(self.named_config_dir)

    good = ('hellothere', 'x--------', 'x0123456789')
    bad = ('-warn-warn-warn', '1warn-warn-warn', 'wWARN-warn-warn')

    for c in good + bad:
      open(self.named_config_file_prefix + c, 'w').close()

    self.Run('config configurations list')

    for c in good:
      self.AssertOutputContains(c)
      self.AssertErrNotContains(c)

    for c in bad:
      self.AssertOutputNotContains(c)

  def testActiveColumn(self):
    self.Run('config configurations create foo')
    self.Run('config configurations create bar')
    self.Run('config configurations activate foo')
    self.Run('config configurations list')

    self.AssertOutputContains('foo True', normalize_space=True)
    self.AssertOutputContains('bar False', normalize_space=True)

if __name__ == '__main__':
  test_case.main()

