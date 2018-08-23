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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseTiersListTest(object):

  def testTiersList(self):
    self.mocked_client.tiers.List.Expect(
        self.messages.SqlTiersListRequest(project=self.Project(),),
        self.messages.TiersListResponse(
            items=[
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=134217728,
                    kind='sql#tier',
                    region=[
                        'us-central',
                        'europe-west1',
                        'asia-east1',
                    ],
                    tier='D0',
                ),
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=536870912,
                    kind='sql#tier',
                    region=[
                        'us-central',
                        'europe-west1',
                        'asia-east1',
                    ],
                    tier='D1',
                ),
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=1073741824,
                    kind='sql#tier',
                    region=[
                        'us-central',
                        'europe-west1',
                        'asia-east1',
                    ],
                    tier='D2',
                ),
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=2147483648,
                    kind='sql#tier',
                    region=[
                        'us-central',
                        'europe-west1',
                        'asia-east1',
                    ],
                    tier='D4',
                ),
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=4294967296,
                    kind='sql#tier',
                    region=[
                        'us-central',
                        'europe-west1',
                        'asia-east1',
                    ],
                    tier='D8',
                ),
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=8589934592,
                    kind='sql#tier',
                    region=[
                        'us-central',
                        'europe-west1',
                        'asia-east1',
                    ],
                    tier='D16',
                ),
                self.messages.Tier(
                    DiskQuota=268435456000,
                    RAM=17179869184,
                    kind='sql#tier',
                    region=[
                        'us-central',
                    ],
                    tier='D32',
                ),
            ],
            kind='sql#tiersList',
        ))

    self.Run('sql tiers list')
    self.AssertOutputContains("""\
TIER  AVAILABLE_REGIONS                     RAM     DISK
D0    us-central,europe-west1,asia-east1  128 MiB  250 GiB
D1    us-central,europe-west1,asia-east1  512 MiB  250 GiB
D2    us-central,europe-west1,asia-east1  1 GiB    250 GiB
D4    us-central,europe-west1,asia-east1  2 GiB    250 GiB
D8    us-central,europe-west1,asia-east1  4 GiB    250 GiB
D16   us-central,europe-west1,asia-east1  8 GiB    250 GiB
D32   us-central                          16 GiB   250 GiB
""", normalize_space=True)


class TiersListGATest(_BaseTiersListTest, base.SqlMockTestGA):
  pass


class TiersListBetaTest(_BaseTiersListTest, base.SqlMockTestBeta):
  pass


class TiersListAlphaTest(_BaseTiersListTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
