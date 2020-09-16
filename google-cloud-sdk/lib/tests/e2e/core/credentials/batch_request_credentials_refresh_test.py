# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for cases when credentials are refreshed by apitools batch executor.

Apitools batch executor refreshes the credentials uniquely. This test is to
simulate the following situation. gcloud uses apitools to send a batch request
to GCP with a invalid access token. The status code of the batch response is
still 200, so the authorized http client does not refresh credentials. apitools
batch request executor will refresh the credentials instead. This behavior is
different from non-batch request.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import e2e_base
from tests.lib import test_case


class TestApitoolsBatchRequestCredentialsRefresh(
    e2e_base.WithExpiredUserAuthEnforcedRetry):

  def testBasic(self):
    self.Run('compute instances describe do-not-delete-windows-instance '
             '--zone=us-west2-a --account={}'.format(self.Account()))


if __name__ == '__main__':
  test_case.main()
