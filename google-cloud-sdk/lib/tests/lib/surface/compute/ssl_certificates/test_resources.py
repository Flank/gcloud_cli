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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


def MakeSslCertificates(msgs, api):
  """Make ssl Certificate test resources for the given api version."""
  prefix = _COMPUTE_PATH + '/' + api + '/projects/my-project/'
  return [
      msgs.SslCertificate(
          type=msgs.SslCertificate.TypeValueValuesEnum.SELF_MANAGED,
          name='ssl-cert-1',
          selfManaged=msgs.SslCertificateSelfManagedSslCertificate(
              certificate=textwrap.dedent("""\
                -----BEGIN CERTIFICATE-----
                MIICZzCCAdACCQDjYQHCnQOiTDANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
                UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
                CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
                bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMTcxMloXDTE1MTAxMzIwMTcxMloweDEL
                MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
                bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
                FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
                gYEAw3JXUCTn8J2VeWqHuc9zJxdy1WfQJtbDxQUUy4nsqU6QPGso3HYXlI/eozg6
                bGhkJNtDVV4AAPQVv01aoFMt3T6MKLzAkjfse7zKQmQ399vQaE7lbLAV9M4FSV9s
                wksSvT7cOW9ddcdKdyV3NTbptW5PeUE8Zk/aCFLPLqOg800CAwEAATANBgkqhkiG
                9w0BAQsFAAOBgQCKMIRiThp2O+wg7M8wcNSdPzAZ61UMeisQKS5OEY90OsekWYUT
                zMkUznRtycTdTBxEqKQoJKeAXq16SezJaZYE48FpoObQc2ZLMvje7F82tOwC2kob
                v83LejX3zZnirv2PZVcFgvUE0k3a8/14enHi7j6jZu+Pl5ZM9BZ+vkBO8g==
                -----END CERTIFICATE-----"""),),
          creationTimestamp='2017-12-18T11:11:11.000-07:00',
          expireTime='2018-12-18T11:11:11.000-07:00',
          description='Self-managed certificate.',
          selfLink=prefix + 'global/sslCertificates/ssl-cert-1',
      ),
      msgs.SslCertificate(
          name='ssl-cert-2',
          region='us-west-1',
          certificate=(textwrap.dedent("""\
            -----BEGIN CERTIFICATE-----
            MIICZzCCAdACCQChX1chr91razANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
            UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
            CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
            bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMzExNVoXDTE1MTAxMzIwMzExNVoweDEL
            MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
            bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
            FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
            gYEAq3S7ZDKHHwdro6f9Zxk8kNZ39a2ejqls4LMropt+RpkHqpaQK17Q2rUykw+f
            P+mXojUB1ZUKkrCE+xcEHeafUgG1lBof56v2bSzIQVeeS1chvDNYGqweEHIkbFHv
            8e8RY9XPkk4hMcW+uxrzaKv1yddBucyETLa3/dYmaEzHcOsCAwEAATANBgkqhkiG
            9w0BAQsFAAOBgQAxBD6GUsgGYfeHkjo3CK/X5cbaPTdUncD13uaI4Q31GWZGhGJX
            t9hMvJdXQ6vzKXBuX6ZLUxvL9SFT+pMLTWGStUFNcDFv/Fqdcre0jPoYEJv/tOHT
            n82GtW9nMhZfVj2PrRiuZwOV8qB6+uEadbcPcET3TcH1WJacbBlHufk1wQ==
            -----END CERTIFICATE-----""")),
          creationTimestamp='2014-10-04T07:56:33.679-07:00',
          description='Self-managed certificate two.',
          selfLink=prefix + 'regions/us-west-1/sslCertificates/ssl-cert-2',
      ),
      msgs.SslCertificate(
          name='ssl-cert-3',
          type=msgs.SslCertificate.TypeValueValuesEnum.MANAGED,
          managed=msgs.SslCertificateManagedSslCertificate(
              domains=[
                  'test1.certsbridge.com',
                  # Punycode for Ṳᾔḯ¢◎ⅾℯ.certsbridge.com
                  'xn--8a342mzfam5b18csni3w.certsbridge.com',
              ],
              status=msgs.SslCertificateManagedSslCertificate
              .StatusValueValuesEnum.ACTIVE,
              domainStatus=msgs.SslCertificateManagedSslCertificate
              .DomainStatusValue(additionalProperties=[
                  msgs.SslCertificateManagedSslCertificate.DomainStatusValue
                  .AdditionalProperty(
                      key='test1.certsbridge.com',
                      value=msgs.SslCertificateManagedSslCertificate
                      .DomainStatusValue.AdditionalProperty.ValueValueValuesEnum
                      .ACTIVE,
                  ),
                  msgs.SslCertificateManagedSslCertificate.DomainStatusValue
                  .AdditionalProperty(
                      key='xn--8a342mzfam5b18csni3w.certsbridge.com',
                      value=msgs.SslCertificateManagedSslCertificate
                      .DomainStatusValue.AdditionalProperty.ValueValueValuesEnum
                      .FAILED_CAA_FORBIDDEN,
                  ),
              ])),
          creationTimestamp='2017-12-17T10:00:00.000-07:00',
          expireTime='2018-12-17T10:00:00.000-07:00',
          description='Managed certificate.',
          selfLink=prefix + 'global/sslCertificates/ssl-cert-3',
      ),
  ]
