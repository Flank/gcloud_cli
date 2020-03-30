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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateWithReservation(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateWithNoReservationAffinity(self):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--reservation-affinity=none')

    template = self._MakeInstanceTemplate(
        reservationAffinity=m.ReservationAffinity(
            consumeReservationType=m.ReservationAffinity
            .ConsumeReservationTypeValueValuesEnum.NO_RESERVATION))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithSpecificReservationAffinity(self):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--reservation-affinity=specific --reservation=my-reservation')

    template = self._MakeInstanceTemplate(
        reservationAffinity=m.ReservationAffinity(
            consumeReservationType=m.ReservationAffinity
            .ConsumeReservationTypeValueValuesEnum.SPECIFIC_RESERVATION,
            key='compute.googleapis.com/reservation-name',
            values=['my-reservation']))

    self.CheckRequests(self.get_default_image_requests,
                       [(self.compute.instanceTemplates, 'Insert',
                         m.ComputeInstanceTemplatesInsertRequest(
                             instanceTemplate=template,
                             project='my-project',
                         ))])

  def testCreateWithAnyReservationAffinity(self):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--reservation-affinity=any')

    template = self._MakeInstanceTemplate(
        reservationAffinity=m.ReservationAffinity(
            consumeReservationType=m.ReservationAffinity
            .ConsumeReservationTypeValueValuesEnum.ANY_RESERVATION))

    self.CheckRequests(self.get_default_image_requests,
                       [(self.compute.instanceTemplates, 'Insert',
                         m.ComputeInstanceTemplatesInsertRequest(
                             instanceTemplate=template,
                             project='my-project',
                         ))])

  def testCreateWithNotSpecifiedReservation(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        'The name the specific reservation must be specified.'):
      self.Run('compute instance-templates create template-1 '
               '--reservation-affinity=specific')


class InstanceTemplatesCreateWithReservationBeta(
    InstanceTemplatesCreateWithReservation):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateWithReservationAlpha(
    InstanceTemplatesCreateWithReservationBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
