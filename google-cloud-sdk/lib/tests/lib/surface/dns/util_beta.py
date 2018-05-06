# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Testing resources for DNS."""
from tests.lib.surface.dns import util


def GetMessages():
  return util.GetMessages("v1beta2")


def GetManagedZones():
  m = GetMessages()
  return [
      m.ManagedZone(
          creationTime=u"2014-10-20T20:06:50.077Z",
          description=u"My zone!",
          dnsName=u"zone.com.",
          id=67371891,
          kind=u"dns#managedZone",
          name=u"mz",
          nameServers=[
              u"ns-cloud-e1.googledomains.com.",
              u"ns-cloud-e2.googledomains.com.",
              u"ns-cloud-e3.googledomains.com.",
              u"ns-cloud-e4.googledomains.com."]),
      m.ManagedZone(
          creationTime=u"2014-10-21T20:06:50.077Z",
          description=u"My zone 1!",
          dnsName=u"zone1.com.",
          id=67671341,
          kind=u"dns#managedZone",
          name=u"mz1",
          nameServers=[
              u"ns-cloud-e2.googledomains.com.",
              u"ns-cloud-e1.googledomains.com.",
              u"ns-cloud-e3.googledomains.com.",
              u"ns-cloud-e4.googledomains.com."]),
  ]


def GetManagedZoneBeforeCreation(api_version="v1beta2"):
  m = util.GetMessages(api_version)
  nonexistence = m.ManagedZoneDnsSecConfig.NonExistenceValueValuesEnum.nsec3
  return m.ManagedZone(
      creationTime=None,
      description="Zone!",
      dnsName="zone.com.",
      dnssecConfig=m.ManagedZoneDnsSecConfig(
          defaultKeySpecs=[
          ],
          kind=u"dns#managedZoneDnsSecConfig",
          nonExistence=nonexistence,
          state=m.ManagedZoneDnsSecConfig.StateValueValuesEnum.on,
      ),
      kind=u"dns#managedZone",
      name="mz",
      nameServerSet=None,
      nameServers=[
      ],
  )


def GetBaseARecord():
  return GetMessages().ResourceRecordSet(
      kind=u"dns#resourceRecordSet",
      name=u"zone.com.",
      rrdatas=[
          u"1.2.3.4"
      ],
      ttl=21600,
      type=u"A"
  )


def GetNSRecord():
  return GetMessages().ResourceRecordSet(
      kind=u"dns#resourceRecordSet",
      name=u"zone.com.",
      rrdatas=[
          u"ns-cloud-e1.googledomains.com.",
          u"ns-cloud-e2.googledomains.com.",
          u"ns-cloud-e3.googledomains.com.",
          u"ns-cloud-e4.googledomains.com."
      ],
      ttl=21600,
      type=u"NS"
  )


def GetSOARecord():
  return GetMessages().ResourceRecordSet(
      kind=u"dns#resourceRecordSet",
      name=u"zone.com.",
      rrdatas=[
          u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 21600 "
          u"3600 1209600 300"
      ],
      ttl=21601,
      type=u"SOA"
  )


def GetMailARecord():
  return GetMessages().ResourceRecordSet(
      kind=u"dns#resourceRecordSet",
      name=u"mail.zone.com.",
      rrdatas=[
          u"5.6.7.8"
      ],
      ttl=21600,
      type=u"A"
  )


def GetCNameRecord():
  return GetMessages().ResourceRecordSet(
      kind=u"dns#resourceRecordSet",
      name=u"www.zone.com.",
      rrdatas=[
          u"zone.com."
      ],
      ttl=21600,
      type=u"CNAME"
  )


def GetMGRecord():
  return GetMessages().ResourceRecordSet(
      kind=u"dns#resourceRecordSet",
      name=u"www.zone.com.",
      rrdatas=[
          u"zone.com."
      ],
      ttl=21600,
      type=u"MG"
  )


def GetRecordSets():
  return [
      GetBaseARecord(),
      GetNSRecord(),
      GetSOARecord(),
      GetMailARecord(),
      GetCNameRecord(),
  ]


def GetRecordSetsForExport():
  messages = GetMessages()
  return [
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["192.0.2.1",
                   "192.0.2.2"],
          ttl=3600, type=u"A"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["2001:db8:10::1"],
          ttl=3600, type=u"AAAA"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["10 mail.zone.com.",
                   "20 mail2.zone.com.",
                   "50 mail3.zone.com."],
          ttl=3600, type=u"MX"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["ns-cloud1.googledomains.com.",
                   "ns-cloud2.googledomains.com.",
                   "ns-cloud3.googledomains.com.",
                   "ns-cloud4.googledomains.com."],
          ttl=21600, type=u"NS"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["ns-cloud1.googledomains.com. "
                   "username.zone.com. 20071207 86400 7200 "
                   "2419200 3600"],
          ttl=3600, type=u"SOA"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"",
                   "\"v=spf2\""],
          ttl=3600, type=u"SPF"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"",
                   "\"v=spf2\""],
          ttl=3600, type=u"TXT"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"2.zone.com.",
          rrdatas=["server.zone.com."],
          ttl=600, type=u"PTR"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"hello.zone.com.",
          rrdatas=["zone.com."],
          ttl=3600, type=u"CNAME"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail.zone.com.",
          rrdatas=["192.0.2.3"],
          ttl=3600, type=u"A"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail2.zone.com.",
          rrdatas=["192.0.2.4"],
          ttl=3600, type=u"A"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail3.zone.com.",
          rrdatas=["192.0.2.5"],
          ttl=3600, type=u"A"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"ns.zone.com.",
          rrdatas=["192.0.2.2"],
          ttl=3600, type=u"A"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"ns.zone.com.",
          rrdatas=["2001:db8:10::2"],
          ttl=3600, type=u"AAAA"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"sip.zone.com.",
          rrdatas=["0 5 5060 sip.zone.com."],
          ttl=3600, type=u"SRV"),
      messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"wwwtest.zone.com.",
          rrdatas=["www.zone.com."],
          ttl=3600, type=u"CNAME"),
  ]


def GetImportedRecordSets():
  messages = GetMessages()
  return {
      (u"zone.com.", u"SOA"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[u"{0} username.zone.com. 20071207 86400 7200 2419200 3600"],
          ttl=3600L,
          type=u"SOA"
      ),
      (u"zone.com.", u"NS"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[u"ns.zone.com.", u"ns.somewhere.example."],
          ttl=3600L,
          type=u"NS"
      ),
      (u"zone.com.", u"MX"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[u"10 mail.zone.com.", u"20 mail2.zone.com.",
                   u"50 mail3.zone.com."],
          ttl=3600L,
          type=u"MX"
      ),
      (u"zone.com.", u"A"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[u"192.0.2.1", u"192.0.2.2"],
          ttl=3600L,
          type=u"A"
      ),
      (u"zone.com.", u"AAAA"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[u"2001:db8:10::1"],
          ttl=3600L,
          type=u"AAAA"
      ),
      (u"zone.com.", u"SPF"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[u"\"v=spf1 mx:zone.com -all\"", u"\"v=spf2\""],
          ttl=3600L,
          type=u"SPF"
      ),
      (u"zone.com.", u"TXT"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[
              u"\"v=spf1 mx:zone.com -all\"", u"\"v=spf2 z=esg\" \"hats\""],
          ttl=3600L,
          type=u"TXT"
      ),
      (u"sip.zone.com.", u"SRV"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"sip.zone.com.",
          rrdatas=[u"0 5 5060 sip.zone.com."],
          ttl=3600L,
          type=u"SRV"
      ),
      (u"test.zone.com.", u"NS"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"test.zone.com.",
          rrdatas=[u"ns1.zone2.com.", u"ns2.zone2.com."],
          ttl=3600L,
          type=u"NS"
      ),
      (u"hello.zone.com.", u"CNAME"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"hello.zone.com.",
          rrdatas=[u"zone.com."],
          ttl=3600L,
          type=u"CNAME"
      ),
      (u"ns.zone.com.", u"A"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"ns.zone.com.",
          rrdatas=[u"192.0.2.2"],
          ttl=3600L,
          type=u"A"
      ),
      (u"ns.zone.com.", u"AAAA"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"ns.zone.com.",
          rrdatas=[u"2001:db8:10::2"],
          ttl=3600L,
          type=u"AAAA"
      ),
      (u"2.zone.com.", u"PTR"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"2.zone.com.",
          rrdatas=[u"server.zone.com."],
          ttl=600L,
          type=u"PTR"
      ),
      (u"mail.zone.com.", u"A"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail.zone.com.",
          rrdatas=[u"192.0.2.3"],
          ttl=3600L,
          type=u"A"
      ),
      (u"wwwtest.zone.com.", u"CNAME"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"wwwtest.zone.com.",
          rrdatas=[u"www.zone.com."],
          ttl=3600L,
          type=u"CNAME"
      ),
      (u"mail2.zone.com.", u"A"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail2.zone.com.",
          rrdatas=[u"192.0.2.4"],
          ttl=3600L,
          type=u"A"
      ),
      (u"mail3.zone.com.", u"A"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail3.zone.com.",
          rrdatas=[u"192.0.2.5"],
          ttl=3600L,
          type=u"A"
      ),
      (u"zone.com.", u"DNSKEY"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[
              u"256 3 5 AQPSKmynfzW4kyBv015MUG2DeIQ3Cbl+ BBZH4b/0PY1kxkmvHjcZc8"
              u"nokfzj31Ga jIQKY+5CptLr3buXA10hWqTkF7H6RfoR qXQeogmMHfpftf6zMv1"
              u"LyBUgia7za6ZE zOJBOztyvhjL742iU/TpPSEDhm2SNKLi jfUppn1UaNvv4w=="
          ],
          signatureRrdatas=[
          ],
          ttl=600L,
          type=u"DNSKEY",
      ),
      (u"test.zone.com.", u"DS"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"test.zone.com.",
          rrdatas=[
              u"60485 5 1 2bb183af5f22588179a53b0a98631fad1a292118",
          ],
          signatureRrdatas=[
          ],
          ttl=3600L,
          type=u"DS",
      ),
      (u"zone.com.", u"IPSECKEY"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[
              u"10 3 2 mygateway.example.com. AQNRU3mG7TVTO2BkR47usntb102uFJtu "
              u"gbo6BSGvgqt4AQ==",
          ],
          signatureRrdatas=[
          ],
          ttl=3600L,
          type=u"IPSECKEY",
      ),
      (u"zone.com.", u"SSHFP"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[
              u"2 1 123456789abcdef67890123456789abcdef67890",
          ],
          signatureRrdatas=[
          ],
          ttl=3600L,
          type=u"SSHFP",
      ),
      (u"zone.com.", u"TLSA"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[
              u"0 0 1 d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106"
              u"618e971",
          ],
          signatureRrdatas=[
          ],
          ttl=3600L,
          type=u"TLSA",
      ),
      (u"zone.com.", u"NAPTR"): messages.ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"zone.com.",
          rrdatas=[
              u"100 50 \"s\" \"z3950+I2L+I2C\" \"\" _z3950._tcp.gatech.edu.",
          ],
          signatureRrdatas=[
          ],
          ttl=3600L,
          type=u"NAPTR",
      ),
  }


def GetImportedRecordSetsWithoutConflicts():
  r = dict(GetImportedRecordSets())
  r.pop(("mail.zone.com.", "A"))
  r.pop(("zone.com.", "A"))
  r.pop(("zone.com.", "SOA"))
  r.pop(("zone.com.", "NS"))
  return r


def GetSOASequence():
  return [
      {
          (u"zone.com.", u"SOA"): GetMessages().ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"ns.zone.com. username.zone.com. 4294967294 1 2 3 4"],
              ttl=3600L,
              type=u"SOA"
          ),
      },
      {
          (u"zone.com.", u"SOA"): GetMessages().ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns.zone.com. username.zone.com. 4294967295 1 2 3 4"],
              ttl=3600L,
              type=u"SOA"
          ),
      },
      {
          (u"zone.com.", u"SOA"): GetMessages().ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns.zone.com. username.zone.com. 0 1 2 3 4"],
              ttl=3600L,
              type=u"SOA"
          ),
      }
  ]


def GetImportableRecord():
  return {
      (u"mail2.zone.com.", u"A"): GetMessages().ResourceRecordSet(
          kind=u"dns#resourceRecordSet",
          name=u"mail2.zone.com.",
          rrdatas=[u"192.0.2.4"],
          ttl=3600L,
          type=u"A"
      )}


def GetChanges():
  return [
      GetMessages().Change(
          additions=[
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[
                      u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                      u"21600 3600 1209600 300"],
                  ttl=21601,
                  type=u"SOA")],
          deletions=[
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[
                      u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 1 "
                      u"21600 3600 1209600 300"],
                  ttl=21600,
                  type=u"SOA")],
          id=u"2",
          kind=u"dns#change",
          startTime=u"2014-10-21T15:16:29.252Z",
          status=GetMessages().Change.StatusValueValuesEnum.pending),
      GetMessages().Change(
          additions=[
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[
                      u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 1 "
                      u"21600 3600 1209600 300"],
                  ttl=21600,
                  type=u"SOA"),
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[u"1.2.3.4"],
                  ttl=21600,
                  type=u"A"),
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"mail.zone.com.",
                  rrdatas=[u"5.6.7.8"],
                  ttl=21600,
                  type=u"A"),
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"www.zone.com.",
                  rrdatas=[
                      u"zone.com."],
                  ttl=21600,
                  type=u"CNAME")],
          deletions=[
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[
                      u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 0 "
                      u"21600 3600 1209600 300"],
                  ttl=21600,
                  type=u"SOA")],
          id=u"1",
          kind=u"dns#change",
          startTime=u"2014-10-20T21:34:21.073Z",
          status=GetMessages().Change.StatusValueValuesEnum.done),
      GetMessages().Change(
          additions=[
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[
                      u"ns-cloud-e1.googledomains.com.",
                      u"ns-cloud-e2.googledomains.com.",
                      u"ns-cloud-e3.googledomains.com.",
                      u"ns-cloud-e4.googledomains.com."],
                  ttl=21600,
                  type=u"NS"),
              GetMessages().ResourceRecordSet(
                  kind=u"dns#resourceRecordSet",
                  name=u"zone.com.",
                  rrdatas=[
                      u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 0 "
                      u"21600 3600 1209600 300"],
                  ttl=21600,
                  type=u"SOA")],
          id=u"0",
          kind=u"dns#change",
          startTime=u"2014-10-20T20:06:50.078Z",
          status=GetMessages().Change.StatusValueValuesEnum.done),
  ]


def GetImportChange():
  messages = GetMessages()
  return messages.Change(
      deletions=[
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                  u"21600 3600 1209600 300"],
              ttl=21601,
              type=u"SOA"),
      ],
      additions=[
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"2.zone.com.",
              rrdatas=[u"server.zone.com."],
              ttl=600L,
              type=u"PTR"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"hello.zone.com.",
              rrdatas=[u"zone.com."],
              ttl=3600L,
              type=u"CNAME"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"mail2.zone.com.",
              rrdatas=[u"192.0.2.4"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"mail3.zone.com.",
              rrdatas=[u"192.0.2.5"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"ns.zone.com.",
              rrdatas=[u"192.0.2.2"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"ns.zone.com.",
              rrdatas=[u"2001:db8:10::2"],
              ttl=3600L,
              type=u"AAAA"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"sip.zone.com.",
              rrdatas=[u"0 5 5060 sip.zone.com."],
              ttl=3600L,
              type=u"SRV"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"test.zone.com.",
              rrdatas=[
                  u"60485 5 1 2bb183af5f22588179a53b0a98631fad1a292118",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"DS",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"test.zone.com.",
              rrdatas=[u"ns1.zone2.com.", u"ns2.zone2.com."],
              ttl=3600L,
              type=u"NS"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"wwwtest.zone.com.",
              rrdatas=[u"www.zone.com."],
              ttl=3600L,
              type=u"CNAME"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"2001:db8:10::1"],
              ttl=3600L,
              type=u"AAAA"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "256 3 5 AQPSKmynfzW4kyBv015MUG2DeIQ3Cbl+ "
                  "BBZH4b/0PY1kxkmvHjcZc8nokfzj31Ga "
                  "jIQKY+5CptLr3buXA10hWqTkF7H6RfoR "
                  "qXQeogmMHfpftf6zMv1LyBUgia7za6ZE "
                  "zOJBOztyvhjL742iU/TpPSEDhm2SNKLi jfUppn1UaNvv4w==",
              ],
              signatureRrdatas=[
              ],
              ttl=600L,
              type=u"DNSKEY",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "10 3 2 mygateway.example.com. "
                  "AQNRU3mG7TVTO2BkR47usntb102uFJtu gbo6BSGvgqt4AQ==",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"IPSECKEY",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"10 mail.zone.com.",
                  u"20 mail2.zone.com.",
                  u"50 mail3.zone.com."],
              ttl=3600L,
              type=u"MX"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "100 50 \"s\" \"z3950+I2L+I2C\" \"\" _z3950._tcp.gatech.edu.",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"NAPTR",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 3 "
                  u"21600 3600 1209600 300"],
              ttl=21601,
              type=u"SOA"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"\"v=spf1 mx:zone.com -all\"", u"\"v=spf2\""],
              ttl=3600L,
              type=u"SPF"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "2 1 123456789abcdef67890123456789abcdef67890",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"SSHFP",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "0 0 1 "
                  "d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106618"
                  "e971",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"TLSA",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"\"v=spf1 mx:zone.com -all\"",
                       u"\"v=spf2 z=esg\" \"hats\""],
              ttl=3600L,
              type=u"TXT"),
      ]
  )


def GetImportChangeAfterCreation():
  r = GetMessages().Change()
  r.additions = GetImportChange().additions
  r.deletions = GetImportChange().deletions
  r.id = u"1"
  r.startTime = u"today now"
  r.status = (
      GetMessages().Change.StatusValueValuesEnum.pending)
  return r


def GetImportReplaceChange():
  messages = GetMessages()
  return messages.Change(
      deletions=[
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"mail.zone.com.",
              rrdatas=[u"5.6.7.8"],
              ttl=21600,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"www.zone.com.",
              rrdatas=[
                  u"zone.com."
              ],
              ttl=21600,
              type=u"CNAME"
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"1.2.3.4"],
              ttl=21600,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns-cloud-e1.googledomains.com.",
                  u"ns-cloud-e2.googledomains.com.",
                  u"ns-cloud-e3.googledomains.com.",
                  u"ns-cloud-e4.googledomains.com."],
              ttl=21600,
              type=u"NS"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                  u"21600 3600 1209600 300"],
              ttl=21601,
              type=u"SOA"),
      ],
      additions=[
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"2.zone.com.",
              rrdatas=[u"server.zone.com."],
              ttl=600L,
              type=u"PTR"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"hello.zone.com.",
              rrdatas=[u"zone.com."],
              ttl=3600L,
              type=u"CNAME"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"mail.zone.com.",
              rrdatas=[u"192.0.2.3"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"mail2.zone.com.",
              rrdatas=[u"192.0.2.4"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"mail3.zone.com.",
              rrdatas=[u"192.0.2.5"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"ns.zone.com.",
              rrdatas=[u"192.0.2.2"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"ns.zone.com.",
              rrdatas=[u"2001:db8:10::2"],
              ttl=3600L,
              type=u"AAAA"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"sip.zone.com.",
              rrdatas=[u"0 5 5060 sip.zone.com."],
              ttl=3600L,
              type=u"SRV"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"test.zone.com.",
              rrdatas=[
                  "60485 5 1 2bb183af5f22588179a53b0a98631fad1a292118",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"DS",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"test.zone.com.",
              rrdatas=[u"ns1.zone2.com.", u"ns2.zone2.com."],
              ttl=3600L,
              type=u"NS"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"wwwtest.zone.com.",
              rrdatas=[u"www.zone.com."],
              ttl=3600L,
              type=u"CNAME"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"192.0.2.1", u"192.0.2.2"],
              ttl=3600L,
              type=u"A"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"2001:db8:10::1"],
              ttl=3600L,
              type=u"AAAA"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "256 3 5 AQPSKmynfzW4kyBv015MUG2DeIQ3Cbl+ "
                  "BBZH4b/0PY1kxkmvHjcZc8nokfzj31Ga "
                  "jIQKY+5CptLr3buXA10hWqTkF7H6RfoR "
                  "qXQeogmMHfpftf6zMv1LyBUgia7za6ZE "
                  "zOJBOztyvhjL742iU/TpPSEDhm2SNKLi jfUppn1UaNvv4w==",
              ],
              signatureRrdatas=[
              ],
              ttl=600L,
              type=u"DNSKEY",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "10 3 2 mygateway.example.com. "
                  "AQNRU3mG7TVTO2BkR47usntb102uFJtu gbo6BSGvgqt4AQ==",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"IPSECKEY",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"10 mail.zone.com.",
                  u"20 mail2.zone.com.",
                  u"50 mail3.zone.com."],
              ttl=3600L,
              type=u"MX"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "100 50 \"s\" \"z3950+I2L+I2C\" \"\" _z3950._tcp.gatech.edu.",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"NAPTR",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"ns.zone.com.", u"ns.somewhere.example."],
              ttl=3600L,
              type=u"NS"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  u"ns-cloud-e1.googledomains.com. username.zone.com. "
                  u"20071207 86400 7200 2419200 3600"],
              ttl=3600L,
              type=u"SOA"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"\"v=spf1 mx:zone.com -all\"", u"\"v=spf2\""],
              ttl=3600L,
              type=u"SPF"),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "2 1 123456789abcdef67890123456789abcdef67890",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"SSHFP",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[
                  "0 0 1 "
                  "d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106618"
                  "e971",
              ],
              signatureRrdatas=[
              ],
              ttl=3600L,
              type=u"TLSA",
          ),
          messages.ResourceRecordSet(
              kind=u"dns#resourceRecordSet",
              name=u"zone.com.",
              rrdatas=[u"\"v=spf1 mx:zone.com -all\"",
                       u"\"v=spf2 z=esg\" \"hats\""],
              ttl=3600L,
              type=u"TXT"),
      ]
  )


def GetImportReplaceChangeAfterCreation():
  r = GetMessages().Change()
  r.additions = GetImportReplaceChange().additions
  r.deletions = GetImportReplaceChange().deletions
  r.id = u"2"
  r.startTime = u"today 5 mins ago"
  r.status = (
      GetMessages().Change.StatusValueValuesEnum.done)
  return r


def GetImportReplaceChangeNoReplaceOrigin():
  r = GetMessages().Change()
  r.additions = (GetImportReplaceChange().additions)
  r.deletions = (GetImportReplaceChange().deletions)
  del r.additions[17]
  del r.deletions[3]
  return r
