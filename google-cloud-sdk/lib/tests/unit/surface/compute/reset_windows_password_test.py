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
"""Tests for the reset-windows-password subcommand."""
import datetime
import textwrap
import time

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import mock

try:
  # pylint:disable=g-import-not-at-top
  # pylint:disable=unused-import
  from googlecloudsdk.api_lib.compute import windows_encryption_utils
except ImportError:
  windows_encryption_utils = None


PRIVATE_KEY = textwrap.dedent("""\
    -----BEGIN RSA PRIVATE KEY-----
    MIIEpAIBAAKCAQEAwgsquN4IBNPqIUnu+h/5Za1kujb2YRhX1vCQVQAkBwnWigcC
    qOBVfRa5JoZfx6KIvEXjWqa77jPvlsxM4WPqnDIM2qiK36up3SKkYwFjff6F2ni/
    ry8vrwXCX3sGZ1hbIHlK0O012HpA3ISeEswVZmX2X67naOvJXfY5v0hGPWqCADao
    +xVxrmxsZD4IWnKl1UaZzI5lhAzr8fw6utHwx1EZ/MSgsEki6tujcZfN+GUDRnmJ
    GQSnPTXmsf7Q4DKreTZk49cuyB3prV91S0x3DYjCUpSXrkVy1Ha5XicGD/q+ystu
    FsJnrrhbNXJbpSjM6sjo/aduAkZJl4FmOt0R7QIDAQABAoIBAQCsT6hHc/tg9iIC
    H5pUiRI55Uj+R5JwVGKkXwl8Qdy8V1MpTOJivpuLsiMGf+sL51xO/CzRsiBOfdYz
    bgaTW9vZimR5w5NW3iTAV2Ps+y2zk9KfV/y3/0nzvUSG70OXgBGj+7GhaBQZwS5Z
    5HZOsOYMAV1QSIv8Uu2FQAK1xuOA4seJ/NK42iXgVB1XvYe2AxCWNqCBJylk9F5N
    8a213oJWw2mwQWCSfZhuvwYRO7w/V+mInKPkKlWvf3SLuMCWeDI8s0jLsJMQ0rbp
    jYXRzc2G+LF1aLxjatiGeLsqfVYerNohufGAajpNkSvcMciDXvD9aJhZqior+x2Q
    rCnMuNRNAoGBAPI6r32wIf8H9GmcvGrXk9OYLq0uJGqAtJDgGmJM5BSX4mlSz+Ni
    SYlQOfi24ykQDo3XbA59Lb6H0L64czi2a3OmpG8s6h4ymp+3cSd1k1AER1oZudwH
    9UScGfSgT/nMgufBwEGlQkCMp5x4Sl20clCHZ49p9eNiXML3wxpCZPIjAoGBAM0T
    NKt/rjqMs0qOWAJKemSPk0zV+1RSjCoOdKC6jmHRGr/MIoKiJLIkywV2m53yv8Wu
    BF3gVUDlwojoOKcVR8588tek5L0j9RshGovKj4Uxz9uPPhzeNnlSA+5PS284VtKz
    LX8xZ/b+MNCyor9jT0qoWylqym0w+M4aFL2tUQSvAoGABJvnQO38B51AIk5QK3xE
    nM8VfEgXe0tNpEAPYHV0FYw6S6S+veXd3lX/dGMOeXaLwFkr/i6Vkz2EVEywLJEU
    BFRUZqUlI0P1OzrDVWvgTLJ4JRe+OJiSKycJO2VdgDRK/Vvra5RYaWADxG9pgtTv
    I+cfqlPq0NPLTg5m0PYYc58CgYBpGt/SygTNA1Hc82mN+wgRxDhVmBJRHGG0KGaD
    /jl9TsOr638AfwPZvdvD+A83+7NoKJEaYCCxu1BiBMsMb263GPkJpvyJKAW2mtfV
    L8MxG9+Rgy/tccJvmaZkHIXoAfMV2DmISBUl1Q/F1thsyQRZmkHmz1Hidsf+MgXR
    VSQCBwKBgQCxwJtGZGPdQbDXcZZtL0yJJIbdt5Q/TrW0es17IPAoze+E6zFg9mo7
    ea9AuGxOGDQwO9n5DBn/3XcSjRnhvXaW60Taz6ZC60Zh/s6IilCmav+n9ewFHJ3o
    AglSJZRJ1Eer0m5m6s2FW5U0Yjthxwkm3WCWS61cOOTvb6xhQ5+WSw==
    -----END RSA PRIVATE KEY-----
    """)
PUBLIC_KEY = textwrap.dedent("""\
    -----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwgsquN4IBNPqIUnu+h/5
    Za1kujb2YRhX1vCQVQAkBwnWigcCqOBVfRa5JoZfx6KIvEXjWqa77jPvlsxM4WPq
    nDIM2qiK36up3SKkYwFjff6F2ni/ry8vrwXCX3sGZ1hbIHlK0O012HpA3ISeEswV
    ZmX2X67naOvJXfY5v0hGPWqCADao+xVxrmxsZD4IWnKl1UaZzI5lhAzr8fw6utHw
    x1EZ/MSgsEki6tujcZfN+GUDRnmJGQSnPTXmsf7Q4DKreTZk49cuyB3prV91S0x3
    DYjCUpSXrkVy1Ha5XicGD/q+ystuFsJnrrhbNXJbpSjM6sjo/aduAkZJl4FmOt0R
    7QIDAQAB
    -----END PUBLIC KEY-----
    """)
USERNAME = 'zaphod'
MODULUS = (
    'wgsquN4IBNPqIUnu+h/5Za1kujb2YRhX1vCQVQAkBwnWigcCqOBVfRa5JoZfx6KIvEXjW'
    'qa77jPvlsxM4WPqnDIM2qiK36up3SKkYwFjff6F2ni/ry8vrwXCX3sGZ1hbIHlK0O012H'
    'pA3ISeEswVZmX2X67naOvJXfY5v0hGPWqCADao+xVxrmxsZD4IWnKl1UaZzI5lhAzr8fw'
    '6utHwx1EZ/MSgsEki6tujcZfN+GUDRnmJGQSnPTXmsf7Q4DKreTZk49cuyB3prV91S0x3'
    'DYjCUpSXrkVy1Ha5XicGD/q+ystuFsJnrrhbNXJbpSjM6sjo/aduAkZJl4FmOt0R7Q==')
EXPONENT = 'AQAB'
EMAIL = 'zaphod@example.com'
IP_ADDRESS = '23.251.133.75'
PASSWORD = 'monkey'
CURRENT_TIME_SEC = 1428627600

SERIAL_PORT_CONT_1 = (
    '{"encryptedPassword":"WtM1LEOabn61Ju8CrNvJM0A1yQFCjtG6hYcmxOBt6hBdewVs'
    '9pgISFKjiBhmW4G4MQbzb8Bx1ARaOcETGKJkjD3n+yFu35E/jAjJR1kwb4hVnw94gS1uU3'
    'ttn0tfVG+fwxRP6YnMPCmz2ib8lsU12ttW0ggPMyceAEIgf+gpeZASM/TlA2sAYerozNaz'
    'Hvh1A6gZIZEmD8+EPuO5Zkfc9cvIyoYY6dxEmjkpwYrAWFwcCj8YwF5hR/RU3wmzNoZ15c'
    'DygaeAJB5vWjkdfaUI7YilyVMr1eBSYI0JVfNEeiaGuxa4vsR76EsuXmZfZeN6XmvH2igq'
    'wBrXpNtV2ebQvA==","exponent":"AQAB",'
    '"modulus":"yPIM0TkE9HR/GnumqfyY9Wu8C1BuU/oiht5OklyUEzD0rwnDYNltsdU9A0V'
    '32xniROlkM392XbEUpE7YPz6WQ9/EDrQDa53WRk6HxgjjKJrA3v6G4YNp5QayuDZaoKsXq'
    'xV7JNFhcIdwa6hzpxZJ9JnXgkeNYXWvgAFx4Hfqkp0zhkkF6aSIME4sfzGNS1ckJAPSqFU'
    'EPM/L00nXcQBuTURm9pisheZ6HnDszVXpli47kkzdxrJdtnz8itQ21nXa1mWJ7geEs8nmR'
    '5F2Hn7cEXjN4BlTnX1nnx7dPCnO7+lr6Vy59eXg1Qnvhujzn1j2YCpKk3lSFnnDZZY+GRw'
    'Unw==","passwordFound":true,"userName":"user1"}\n'
    '{"encryptedPassword":"PGj8U7vMs3nQViJ6ThoRZozUV9Z+1PZk589Zebnr3Xdt2WZm'
    'emZiHwifqsSH92MwxDRiL74O/GXtkWlsXMMkuS5j3i4GMe40p3E2nFWveSONS9Q9eWoCk3'
    'q7WKz9P/vPD9VoaZSgQGsjHEkuF8JXNLKFjZHHuuOFyfs82Af/Mfzxft5DuM3QoigLoyQD'
    'ClhmBD8O9BrnRizNUzBPnvLxKoXCdk+4sIeOIXIyT+VriuvQPVSFrNFDZqZlOl7LJvcaaG'
    '78ENV/PyYTuKmiAxA9ceDuDEkpgCT5a28rk1f6/6RrKOkZSm79smSzQ2d/D/ZxfuaHcIT/'
    'pNnPU89UH6vcHA==","exponent":"AQAB",'
    '"modulus":"oFy2tCx0YUtFSA4KxZzEa7zEwSkiYzyo+HsWG7Q4yQLtZi22fT8CjFTZM+m'
    'r/bpRJloszxa95DbhB7fSUUe4NXbCKzvC3QhWW6e1KlCpikoOX8QIme+lzN6htMsbtGGAI'
    'HIyvQJgkSM9VRSGm0IGWzduxVHct1b+rHbo04q9dOC/0IHDAfrsXZ4Yd8JDIh8QMjOrQ52'
    'PxLGvrLx4G/oqwlJ6m4AfVDBID3ZktRlFU4CVlORGXcOgEIAve2ipQ5Nhzgs8UtXNIkd0+'
    'nOSl0VQlDnnwPou7gBmYhI5twMGC8HzW3bIrSNnm8KBdsa7Z3K/hzO91pEUzRytQ81WvEw'
    'tnw==","passwordFound":true,"userName":"user2"}\n')
SERIAL_PORT_CONT_2 = SERIAL_PORT_CONT_1 + (
    '{"userName": "zaphod", "passwordFound": true, "encryptedPassword": "v/'
    '/UByaTEyO8NofgtcbMV2M1EmgV9v0x0bh3H1HpRsxc288IEvnrOm5ogboN0Jt2N9oy3cX+'
    'Poxhdx34jwWlc+JIzGJDK/WDrVYwYDFlI6qZ8Bt3ttDPF7AQhjCUl73zbjAjMrxIjb52hu'
    'mByA8OIkZ/l+lk6tHqbXRdIKSiF7vC2T2/Q7JB55HUMhMDTyB56+NTtkC/E0hltlW3h74E'
    'F6BYpdh+T/VkAUMgWKXfOldf9dMlSZ9o2hASy9lt3v5NnCbCBrPunk50VOl+AUepNn5A1z'
    'F24l6gcAigETsE2Xt8s+gLJkpiTPmOaDmDn9wvku5sMoBT/q8dYcogQKjbuw==",'
    '"modulus": "wgsquN4IBNPqIUnu+h/5Za1kujb2YRhX1vCQVQAkBwnWigcCqOBVfRa5Jo'
    'Zfx6KIvEXjWqa77jPvlsxM4WPqnDIM2qiK36up3SKkYwFjff6F2ni/ry8vrwXCX3sGZ1hb'
    'IHlK0O012HpA3ISeEswVZmX2X67naOvJXfY5v0hGPWqCADao+xVxrmxsZD4IWnKl1UaZzI'
    '5lhAzr8fw6utHwx1EZ/MSgsEki6tujcZfN+GUDRnmJGQSnPTXmsf7Q4DKreTZk49cuyB3p'
    'rV91S0x3DYjCUpSXrkVy1Ha5XicGD/q+ystuFsJnrrhbNXJbpSjM6sjo/aduAkZJl4FmOt'
    '0R7Q==", "exponent": "AQAB"}\n')

SERIAL_PORT_FAILED_CONT = SERIAL_PORT_CONT_1 + (
    '{"userName": "zaphod", "passwordFound": false, '
    '"errorMessage":"NERR_PasswordTooShort", '
    '"modulus": "wgsquN4IBNPqIUnu+h/5Za1kujb2YRhX1vCQVQAkBwnWigcCqOBVfRa5Jo'
    'Zfx6KIvEXjWqa77jPvlsxM4WPqnDIM2qiK36up3SKkYwFjff6F2ni/ry8vrwXCX3sGZ1hb'
    'IHlK0O012HpA3ISeEswVZmX2X67naOvJXfY5v0hGPWqCADao+xVxrmxsZD4IWnKl1UaZzI'
    '5lhAzr8fw6utHwx1EZ/MSgsEki6tujcZfN+GUDRnmJGQSnPTXmsf7Q4DKreTZk49cuyB3p'
    'rV91S0x3DYjCUpSXrkVy1Ha5XicGD/q+ystuFsJnrrhbNXJbpSjM6sjo/aduAkZJl4FmOt'
    '0R7Q==", "exponent": "AQAB"}\n')

EXPIRED_KEY = (
    '{{"userName": "arthur", "modulus": "expired", "exponent": "AQAB", '
    '"email": "arthur@example.com", "expireOn": "{0}"}}'.format(
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(CURRENT_TIME_SEC - 300))
        ))
NOT_EXPIRED_KEY = (
    '{{"userName": "arthur", "modulus": "not+expired", "exponent": "AQAB", '
    '"email": "arthur@example.com", "expireOn": "{0}"}}'.format(
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(CURRENT_TIME_SEC + 60))
        ))
BAD_KEY = (
    '{{"userName": "arthur", "modulus": "not+expired", "exponent": "AQAB", '
    '"email": "arthur@example.com"')
MISSING_EXPIRATION_KEY = (
    '{"userName": "arthur", "modulus": "missing+exp", "exponent": "AQAB", '
    '"email": "arthur@example.com"}')
KEY_WITH_EXTRA_FIELDS = (
    '{{"userName": "arthur", "modulus": "extra+fields", "exponent": "AQAB", '
    '"email": "arthur@example.com", "expireOn": "{0}", "foo": "bar"}}'.format(
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(CURRENT_TIME_SEC + 60))
        ))


class ResetWindowsPasswordTest(test_base.BaseTest):

  def SetUp(self):
    self.time.return_value = CURRENT_TIME_SEC
    self.expire_on = time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                   time.gmtime(CURRENT_TIME_SEC + 300))
    self.windows_key_entry = (
        '{{"email": "{0}", "expireOn": "{1}", "exponent": "{2}", '
        '"modulus": "{3}", "userName": "{4}"}}')
    self.expected_output = textwrap.dedent("""\
        ip_address: {0}
        password:   {1}
        username:   {2}
        """)
    self.expected_no_ip_address_output = textwrap.dedent("""\
        password: {0}
        username: {1}
        """)
    self.expected_json_output = textwrap.dedent("""\
        {{
          "ip_address": "{0}",
          "password": "{1}",
          "username": "{2}"
        }}
        """)

    properties.VALUES.core.account.Set(EMAIL)

    current_time_patcher = mock.patch(
        'googlecloudsdk.command_lib.util.time_util.CurrentDatetimeUtc',
        return_value=datetime.datetime.utcfromtimestamp(CURRENT_TIME_SEC),
        autospec=True)
    self.addCleanup(current_time_patcher.stop)
    self.current_time = current_time_patcher.start()

    if self.IsOnWindows():
      encryption_utils_import = ('googlecloudsdk.api_lib.compute.'
                                 'windows_encryption_utils.WinCrypt')
    else:
      encryption_utils_import = ('googlecloudsdk.api_lib.compute.'
                                 'openssl_encryption_utils.OpensslCrypt')

    key_pair_patcher = mock.patch(
        encryption_utils_import + '.GetKeyPair',
        return_value=PRIVATE_KEY,
        autospec=True)
    self.addCleanup(key_pair_patcher.stop)
    self.key_pair = key_pair_patcher.start()

    public_key_patcher = mock.patch(
        encryption_utils_import + '.GetPublicKey',
        return_value=PUBLIC_KEY,
        autospec=True)
    self.addCleanup(public_key_patcher.stop)
    self.public_key = public_key_patcher.start()

    decrypt_patcher = mock.patch(
        encryption_utils_import + '.DecryptMessage',
        return_value=PASSWORD,
        autospec=True)
    self.addCleanup(decrypt_patcher.stop)
    self.decrypt = decrypt_patcher.start()

    mod_exp_patcher = mock.patch(
        encryption_utils_import + '.GetModulusExponentFromPublicKey',
        return_value=(MODULUS, EXPONENT),
        autospec=True)
    self.addCleanup(mod_exp_patcher.stop)
    self.mod_exp = mod_exp_patcher.start()

    find_executable_patcher = mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value='mocked-ssh.sh',
        autospec=True)
    self.addCleanup(find_executable_patcher.stop)
    self.find_executable = find_executable_patcher.start()

  def GetInstanceMessage(self, network=True, existing_keys=None,
                         old_credentials=False):
    messages = self.messages
    if network:
      network_interfaces = [
          messages.NetworkInterface(
              accessConfigs=[
                  messages.AccessConfig(
                      name='external-nat',
                      natIP=IP_ADDRESS),
                  ],
              ),
          ]
    else:
      network_interfaces = [
          messages.NetworkInterface()]

    metadata_items = [
        messages.Metadata.ItemsValueListEntry(
            key='a',
            value='b'),
        ]

    if existing_keys:
      metadata_items.append(
          messages.Metadata.ItemsValueListEntry(
              key='windows-keys',
              value='\n'.join(existing_keys)))

    if old_credentials:
      metadata_items.extend([
          messages.Metadata.ItemsValueListEntry(
              key='gce-initial-windows-user',
              value='zaphod'),
          messages.Metadata.ItemsValueListEntry(
              key='gce-initial-windows-password',
              value='my-password')
          ])

    instance_message = messages.Instance(
        name='instance-1',
        networkInterfaces=network_interfaces,
        metadata=messages.Metadata(
            fingerprint='my-fingerprint',
            items=metadata_items),
        status=messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/instances/instance-1'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1'))
    return instance_message

  def GetInstanceGetRequest(self, project='my-project'):
    messages = self.messages
    return (self.compute.instances,
            'Get',
            messages.ComputeInstancesGetRequest(
                instance='instance-1',
                project=project,
                zone='zone-1'))

  def GetSerialPortGetRequest(self, project='my-project'):
    messages = self.messages
    return (self.compute.instances,
            'GetSerialPortOutput',
            messages.ComputeInstancesGetSerialPortOutputRequest(
                instance='instance-1',
                project=project,
                port=4,
                zone='zone-1'))

  def GetMetadataSetRequest(self, windows_key_entry, project='my-project'):
    messages = self.messages
    return (self.compute.instances,
            'SetMetadata',
            messages.ComputeInstancesSetMetadataRequest(
                instance='instance-1',
                metadata=messages.Metadata(
                    fingerprint='my-fingerprint',
                    items=[
                        messages.Metadata.ItemsValueListEntry(
                            key='a',
                            value='b'),
                        messages.Metadata.ItemsValueListEntry(
                            key='windows-keys',
                            value='{0}'.format(windows_key_entry)),
                        ]),
                project=project,
                zone='zone-1'))

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testUriCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    self.Run('compute reset-windows-password https://www.googleapis.com/'
             'compute/v1/projects/project-1/zones/zone-1/instances/instance-1')

    self.CheckRequests(
        [self.GetInstanceGetRequest(project='project-1')],
        [self.GetMetadataSetRequest(windows_key_entry, project='project-1')],
        [self.GetSerialPortGetRequest(project='project-1')],
    )
    self.AssertOutputEquals(expected_output)

  def testJsonOutput(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_json_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1 --format json
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testUserNameAndInstanceNameMatch(self):
    with self.assertRaisesRegexp(
        utils.InvalidUserError,
        r'User \[instance-1\] cannot be created on instance \[instance-1\].'):
      self.Run("""
          compute reset-windows-password instance-1 --user instance-1
          """)

  def testNoPasswordInFirstSerialPortOutput(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_1)],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testUserFlag(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, 'ford')
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, 'ford')

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1 --user ford
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testAgentNotRunning(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents='')],
    ])
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    with self.assertRaisesRegexp(
        utils.InstanceNotReadyError,
        'The instance may not be ready for use.'):
      self.Run("""
          compute reset-windows-password instance-1 --zone zone-1
          """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )

  def testOnOldWindowsWithOldAgent(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(old_credentials=True)],
        [self.GetInstanceMessage(old_credentials=True)],
        [messages.SerialPortOutput(contents='')],
    ])

    with self.assertRaisesRegexp(
        utils.WrongInstanceTypeError,
        'This Windows instance appears to be too old'):
      self.Run("""
          compute reset-windows-password instance-1 --zone zone-1
          """)

  def testNewWindowsWithLegacyCredentials(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(old_credentials=True)],
        [self.GetInstanceMessage(old_credentials=True)],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    expected_warning = ('WARNING: Instance [instance-1] appears to have been '
                        'created with an older')

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.assertIn(expected_warning, self.stderr.getvalue())
    self.AssertOutputEquals(expected_output)

  def testInstanceWithNoIpAddress(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(network=False)],
        [self.GetInstanceMessage(network=False)],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_no_ip_address_output.format(
        PASSWORD, USERNAME)
    expected_warning = ('WARNING: Instance [instance-1] does not appear to '
                        'have an external IP')
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.assertIn(expected_warning, self.stderr.getvalue())
    self.AssertOutputEquals(expected_output)

  def testExpiredKeyRemoved(self):
    messages = self.messages
    existing_keys = [EXPIRED_KEY, NOT_EXPIRED_KEY]
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(existing_keys=existing_keys)],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    new_windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)
    # The instance with existing keys has both an expired key and a key that
    # isn't expired. The MetadataSetRequest should include the new key and the
    # one that isn't expired, but it shouldn't include the expired key.
    windows_key_entry = '\n'.join([NOT_EXPIRED_KEY, new_windows_key_entry])

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testIgnoreBadKey(self):
    messages = self.messages
    existing_keys = [NOT_EXPIRED_KEY, BAD_KEY]
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(existing_keys=existing_keys)],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    new_windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)
    windows_key_entry = '\n'.join([NOT_EXPIRED_KEY, BAD_KEY,
                                   new_windows_key_entry])

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testIgnoreKeyWithNoExpiration(self):
    messages = self.messages
    existing_keys = [NOT_EXPIRED_KEY, MISSING_EXPIRATION_KEY]
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(existing_keys=existing_keys)],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    new_windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)
    windows_key_entry = '\n'.join([NOT_EXPIRED_KEY, MISSING_EXPIRATION_KEY,
                                   new_windows_key_entry])

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testKeyWithExtraFields(self):
    messages = self.messages
    existing_keys = [KEY_WITH_EXTRA_FIELDS]
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(existing_keys=existing_keys)],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    new_windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)
    windows_key_entry = '\n'.join([KEY_WITH_EXTRA_FIELDS,
                                   new_windows_key_entry])

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testFullMetadata(self):
    existing_keys = []
    test_key = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)
    max_keys = 262144 / len(test_key + '\n')

    for key_num in range(max_keys):
      key = test_key.replace(MODULUS, 'key-{0:06d}-{1}'
                             .format(key_num, MODULUS[11:]))
      existing_keys.append(key)
    messages = self.messages

    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage(existing_keys=existing_keys)],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    new_windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)
    # Request should have all existing keys, minus the first entry, plus the new
    # key.
    expected_keys = existing_keys[1:]
    expected_keys.append(new_windows_key_entry)
    windows_key_entry = '\n'.join(expected_keys)

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testResetPasswordFailedFirstTry(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
        [messages.SerialPortOutput(contents=SERIAL_PORT_FAILED_CONT)],
        [messages.SerialPortOutput(contents=SERIAL_PORT_CONT_2)],
    ])
    expected_output = self.expected_output.format(
        IP_ADDRESS, PASSWORD, USERNAME)
    windows_key_entry = self.windows_key_entry.format(
        EMAIL, self.expire_on, EXPONENT, MODULUS, USERNAME)

    self.Run("""
        compute reset-windows-password instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [self.GetInstanceGetRequest()],
        [self.GetMetadataSetRequest(windows_key_entry)],
        [self.GetSerialPortGetRequest()],
        [self.GetSerialPortGetRequest()],
    )
    self.AssertOutputEquals(expected_output)

  def testSerialPortFailure(self):
    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][1] != 'GetSerialPortOutput':
        yield self.GetInstanceMessage()
      else:
        kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        'Could not fetch resource'):
      self.Run("""
          compute reset-windows-password instance-1 --zone zone-1
          """)

  def testTimeoutFailure(self):
    self.time.side_effect = iter([
        CURRENT_TIME_SEC,       # Start time
        CURRENT_TIME_SEC + 1,   # Check for key expiration
        CURRENT_TIME_SEC + 2,   # Start of serial port checking
        CURRENT_TIME_SEC + 60,  # Check for time out
        CURRENT_TIME_SEC + 61,  # End Time
        ])

    self.make_requests.side_effect = iter([
        [self.GetInstanceMessage()],
        [self.GetInstanceMessage()],
    ])

    with self.assertRaisesRegexp(
        utils.TimeoutError,
        'Did not receive password in a reasonable amount of time'):
      self.Run("""
          compute reset-windows-password instance-1 --zone zone-1
          """)

  @test_case.Filters.DoNotRunOnWindows(
      'Windows uses Windows Crypto APIs instead of OpenSSL')
  def testNoOpenSSL(self):
    self.find_executable.return_value = None

    with self.assertRaisesRegexp(
        utils.MissingDependencyError,
        'Your platform does not support OpenSSL'):
      self.Run("""
          compute reset-windows-password instance-1 --zone zone-1
          """)


if __name__ == '__main__':
  test_case.main()
