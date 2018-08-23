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

from tests.lib import e2e_base
from tests.lib import test_case


# Not using e2e.WithServiceAuth here (as any other e2e tests does) since
# here only testing functionality related to activating service account.
class ServiceAuthTestJSON(e2e_base.WithServiceAccountFile):

  def testJSONKeyServiceAuth(self):
    """Test service account auth with a JSON key."""
    self.Run(
        'auth activate-service-account {0} --key-file={1}'
        .format(self.Account(), self.json_key_file))
    self.AssertErrContains('Activated service account credentials for: [{0}]'
                           .format(self.Account()))
    # Make sure activated credentials are usable.
    self.Run('compute zones list --project={0}'.format(self.Project()))
    self.AssertOutputContains('us-central1')


if __name__ == '__main__':
  test_case.main()
