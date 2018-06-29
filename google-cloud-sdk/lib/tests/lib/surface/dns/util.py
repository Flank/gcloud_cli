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
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis


def GetMessages(api_version="v1"):
  return apis.GetMessagesModule("dns", api_version)


def GetManagedZones(api_version="v1"):
  return [
      GetMessages(api_version).ManagedZone(
          creationTime="2014-10-20T20:06:50.077Z",
          description="My zone!",
          dnsName="zone.com.",
          id=67371891,
          kind="dns#managedZone",
          name="mz",
          nameServers=[
              "ns-cloud-e1.googledomains.com.",
              "ns-cloud-e2.googledomains.com.",
              "ns-cloud-e3.googledomains.com.",
              "ns-cloud-e4.googledomains.com."]),
      GetMessages(api_version).ManagedZone(
          creationTime="2014-10-21T20:06:50.077Z",
          description="My zone 1!",
          dnsName="zone1.com.",
          id=67671341,
          kind="dns#managedZone",
          name="mz1",
          nameServers=[
              "ns-cloud-e2.googledomains.com.",
              "ns-cloud-e1.googledomains.com.",
              "ns-cloud-e3.googledomains.com.",
              "ns-cloud-e4.googledomains.com."]),
  ]


def GetManagedZoneBeforeCreation(api_version="v1"):
  return GetMessages(api_version).ManagedZone(
      description="Zone!",
      dnsName="zone.com.",
      kind="dns#managedZone",
      name="mz",
      nameServers=[])


def GetBaseARecord():
  return GetMessages().ResourceRecordSet(
      kind="dns#resourceRecordSet",
      name="zone.com.",
      rrdatas=[
          "1.2.3.4"
      ],
      ttl=21600,
      type="A"
  )


def GetNSRecord():
  return GetMessages().ResourceRecordSet(
      kind="dns#resourceRecordSet",
      name="zone.com.",
      rrdatas=[
          "ns-cloud-e1.googledomains.com.",
          "ns-cloud-e2.googledomains.com.",
          "ns-cloud-e3.googledomains.com.",
          "ns-cloud-e4.googledomains.com."
      ],
      ttl=21600,
      type="NS"
  )


def GetSOARecord():
  return GetMessages().ResourceRecordSet(
      kind="dns#resourceRecordSet",
      name="zone.com.",
      rrdatas=[
          "ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 21600 "
          "3600 1209600 300"
      ],
      ttl=21601,
      type="SOA"
  )


def GetMailARecord():
  return GetMessages().ResourceRecordSet(
      kind="dns#resourceRecordSet",
      name="mail.zone.com.",
      rrdatas=[
          "5.6.7.8"
      ],
      ttl=21600,
      type="A"
  )


def GetCNameRecord():
  return GetMessages().ResourceRecordSet(
      kind="dns#resourceRecordSet",
      name="www.zone.com.",
      rrdatas=[
          "zone.com."
      ],
      ttl=21600,
      type="CNAME"
  )


def GetMGRecord():
  return GetMessages().ResourceRecordSet(
      kind="dns#resourceRecordSet",
      name="www.zone.com.",
      rrdatas=[
          "zone.com."
      ],
      ttl=21600,
      type="MG"
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
  return [
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["192.0.2.1",
                   "192.0.2.2"],
          ttl=3600, type="A"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["2001:db8:10::1"],
          ttl=3600, type="AAAA"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["10 mail.zone.com.",
                   "20 mail2.zone.com.",
                   "50 mail3.zone.com."],
          ttl=3600, type="MX"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["ns-cloud1.googledomains.com.",
                   "ns-cloud2.googledomains.com.",
                   "ns-cloud3.googledomains.com.",
                   "ns-cloud4.googledomains.com."],
          ttl=21600, type="NS"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["ns-cloud1.googledomains.com. "
                   "username.zone.com. 20071207 86400 7200 "
                   "2419200 3600"],
          ttl=3600, type="SOA"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"",
                   "\"v=spf2\""],
          ttl=3600, type="SPF"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"",
                   "\"v=spf2\""],
          ttl=3600, type="TXT"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["0 issue \"ca.example.net\""],
          ttl=3600, type="CAA"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="2.zone.com.",
          rrdatas=["server.zone.com."],
          ttl=600, type="PTR"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="hello.zone.com.",
          rrdatas=["zone.com."],
          ttl=3600, type="CNAME"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail.zone.com.",
          rrdatas=["192.0.2.3"],
          ttl=3600, type="A"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail2.zone.com.",
          rrdatas=["192.0.2.4"],
          ttl=3600, type="A"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail3.zone.com.",
          rrdatas=["192.0.2.5"],
          ttl=3600, type="A"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["192.0.2.2"],
          ttl=3600, type="A"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["2001:db8:10::2"],
          ttl=3600, type="AAAA"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="sip.zone.com.",
          rrdatas=["0 5 5060 sip.zone.com."],
          ttl=3600, type="SRV"),
      GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="wwwtest.zone.com.",
          rrdatas=["www.zone.com."],
          ttl=3600, type="CNAME"),
  ]


def GetImportedRecordSets():
  return {
      ("zone.com.", "SOA"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["{0} username.zone.com. 20071207 86400 7200 2419200 3600"],
          ttl=3600,
          type="SOA"
      ),
      ("zone.com.", "NS"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["ns.zone.com.", "ns.somewhere.example."],
          ttl=3600,
          type="NS"
      ),
      ("zone.com.", "MX"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["10 mail.zone.com.", "20 mail2.zone.com.",
                   "50 mail3.zone.com."],
          ttl=3600,
          type="MX"
      ),
      ("zone.com.", "A"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["192.0.2.1", "192.0.2.2"],
          ttl=3600,
          type="A"
      ),
      ("zone.com.", "AAAA"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["2001:db8:10::1"],
          ttl=3600,
          type="AAAA"
      ),
      ("zone.com.", "SPF"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"", "\"v=spf2\""],
          ttl=3600,
          type="SPF"
      ),
      ("zone.com.", "TXT"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "\"v=spf1 mx:zone.com -all\"", "\"v=spf2 z=esg\" \"hats\""],
          ttl=3600,
          type="TXT"
      ),
      ("zone.com.", "CAA"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["0 issue \"ca.example.net\""],
          ttl=3600,
          type="CAA"
      ),
      ("sip.zone.com.", "SRV"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="sip.zone.com.",
          rrdatas=["0 5 5060 sip.zone.com."],
          ttl=3600,
          type="SRV"
      ),
      ("test.zone.com.", "NS"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="test.zone.com.",
          rrdatas=["ns1.zone2.com.", "ns2.zone2.com."],
          ttl=3600,
          type="NS"
      ),
      ("hello.zone.com.", "CNAME"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="hello.zone.com.",
          rrdatas=["zone.com."],
          ttl=3600,
          type="CNAME"
      ),
      ("ns.zone.com.", "A"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["192.0.2.2"],
          ttl=3600,
          type="A"
      ),
      ("ns.zone.com.", "AAAA"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["2001:db8:10::2"],
          ttl=3600,
          type="AAAA"
      ),
      ("2.zone.com.", "PTR"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="2.zone.com.",
          rrdatas=["server.zone.com."],
          ttl=600,
          type="PTR"
      ),
      ("mail.zone.com.", "A"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail.zone.com.",
          rrdatas=["192.0.2.3"],
          ttl=3600,
          type="A"
      ),
      ("wwwtest.zone.com.", "CNAME"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="wwwtest.zone.com.",
          rrdatas=["www.zone.com."],
          ttl=3600,
          type="CNAME"
      ),
      ("mail2.zone.com.", "A"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail2.zone.com.",
          rrdatas=["192.0.2.4"],
          ttl=3600,
          type="A"
      ),
      ("mail3.zone.com.", "A"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail3.zone.com.",
          rrdatas=["192.0.2.5"],
          ttl=3600,
          type="A"
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
          ("zone.com.", "SOA"): GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["ns.zone.com. username.zone.com. 4294967294 1 2 3 4"],
              ttl=3600,
              type="SOA"
          ),
      },
      {
          ("zone.com.", "SOA"): GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns.zone.com. username.zone.com. 4294967295 1 2 3 4"],
              ttl=3600,
              type="SOA"
          ),
      },
      {
          ("zone.com.", "SOA"): GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns.zone.com. username.zone.com. 0 1 2 3 4"],
              ttl=3600,
              type="SOA"
          ),
      }
  ]


def GetImportableRecord():
  return {
      ("mail2.zone.com.", "A"): GetMessages().ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail2.zone.com.",
          rrdatas=["192.0.2.4"],
          ttl=3600,
          type="A"
      )}


def GetChanges():
  return [
      GetMessages().Change(
          additions=[
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=[
                      "ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                      "21600 3600 1209600 300"],
                  ttl=21601,
                  type="SOA")],
          deletions=[
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=[
                      "ns-cloud-e1.googledomains.com. dns-admin.google.com. 1 "
                      "21600 3600 1209600 300"],
                  ttl=21600,
                  type="SOA")],
          id="2",
          kind="dns#change",
          startTime="2014-10-21T15:16:29.252Z",
          status=GetMessages().Change.StatusValueValuesEnum.pending),
      GetMessages().Change(
          additions=[
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=[
                      "ns-cloud-e1.googledomains.com. dns-admin.google.com. 1 "
                      "21600 3600 1209600 300"],
                  ttl=21600,
                  type="SOA"),
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=["1.2.3.4"],
                  ttl=21600,
                  type="A"),
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="mail.zone.com.",
                  rrdatas=["5.6.7.8"],
                  ttl=21600,
                  type="A"),
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="www.zone.com.",
                  rrdatas=[
                      "zone.com."],
                  ttl=21600,
                  type="CNAME")],
          deletions=[
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=[
                      "ns-cloud-e1.googledomains.com. dns-admin.google.com. 0 "
                      "21600 3600 1209600 300"],
                  ttl=21600,
                  type="SOA")],
          id="1",
          kind="dns#change",
          startTime="2014-10-20T21:34:21.073Z",
          status=GetMessages().Change.StatusValueValuesEnum.done),
      GetMessages().Change(
          additions=[
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=[
                      "ns-cloud-e1.googledomains.com.",
                      "ns-cloud-e2.googledomains.com.",
                      "ns-cloud-e3.googledomains.com.",
                      "ns-cloud-e4.googledomains.com."],
                  ttl=21600,
                  type="NS"),
              GetMessages().ResourceRecordSet(
                  kind="dns#resourceRecordSet",
                  name="zone.com.",
                  rrdatas=[
                      "ns-cloud-e1.googledomains.com. dns-admin.google.com. 0 "
                      "21600 3600 1209600 300"],
                  ttl=21600,
                  type="SOA")],
          id="0",
          kind="dns#change",
          startTime="2014-10-20T20:06:50.078Z",
          status=GetMessages().Change.StatusValueValuesEnum.done),
  ]


def GetImportChange():
  return GetMessages().Change(
      deletions=[
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                  "21600 3600 1209600 300"],
              ttl=21601,
              type="SOA"),
      ],
      additions=[
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="2.zone.com.",
              rrdatas=["server.zone.com."],
              ttl=600,
              type="PTR"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="hello.zone.com.",
              rrdatas=["zone.com."],
              ttl=3600,
              type="CNAME"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail2.zone.com.",
              rrdatas=["192.0.2.4"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail3.zone.com.",
              rrdatas=["192.0.2.5"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["192.0.2.2"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["2001:db8:10::2"],
              ttl=3600,
              type="AAAA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="sip.zone.com.",
              rrdatas=["0 5 5060 sip.zone.com."],
              ttl=3600,
              type="SRV"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="test.zone.com.",
              rrdatas=["ns1.zone2.com.", "ns2.zone2.com."],
              ttl=3600,
              type="NS"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="wwwtest.zone.com.",
              rrdatas=["www.zone.com."],
              ttl=3600,
              type="CNAME"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["2001:db8:10::1"],
              ttl=3600,
              type="AAAA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["0 issue \"ca.example.net\""],
              ttl=3600,
              type="CAA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "10 mail.zone.com.",
                  "20 mail2.zone.com.",
                  "50 mail3.zone.com."],
              ttl=3600,
              type="MX"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. dns-admin.google.com. 3 "
                  "21600 3600 1209600 300"],
              ttl=21601,
              type="SOA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["\"v=spf1 mx:zone.com -all\"", "\"v=spf2\""],
              ttl=3600,
              type="SPF"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["\"v=spf1 mx:zone.com -all\"",
                       "\"v=spf2 z=esg\" \"hats\""],
              ttl=3600,
              type="TXT"),
      ]
  )


def GetImportChangeAfterCreation():
  r = GetMessages().Change()
  r.additions = GetImportChange().additions
  r.deletions = GetImportChange().deletions
  r.id = "1"
  r.startTime = "today now"
  r.status = (
      GetMessages().Change.StatusValueValuesEnum.pending)
  return r


def GetImportReplaceChange():
  return GetMessages().Change(
      deletions=[
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail.zone.com.",
              rrdatas=["5.6.7.8"],
              ttl=21600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="www.zone.com.",
              rrdatas=[
                  "zone.com."
              ],
              ttl=21600,
              type="CNAME"
          ),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["1.2.3.4"],
              ttl=21600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com.",
                  "ns-cloud-e2.googledomains.com.",
                  "ns-cloud-e3.googledomains.com.",
                  "ns-cloud-e4.googledomains.com."],
              ttl=21600,
              type="NS"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                  "21600 3600 1209600 300"],
              ttl=21601,
              type="SOA"),
      ],
      additions=[
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="2.zone.com.",
              rrdatas=["server.zone.com."],
              ttl=600,
              type="PTR"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="hello.zone.com.",
              rrdatas=["zone.com."],
              ttl=3600,
              type="CNAME"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail.zone.com.",
              rrdatas=["192.0.2.3"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail2.zone.com.",
              rrdatas=["192.0.2.4"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail3.zone.com.",
              rrdatas=["192.0.2.5"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["192.0.2.2"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["2001:db8:10::2"],
              ttl=3600,
              type="AAAA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="sip.zone.com.",
              rrdatas=["0 5 5060 sip.zone.com."],
              ttl=3600,
              type="SRV"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="test.zone.com.",
              rrdatas=["ns1.zone2.com.", "ns2.zone2.com."],
              ttl=3600,
              type="NS"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="wwwtest.zone.com.",
              rrdatas=["www.zone.com."],
              ttl=3600,
              type="CNAME"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["192.0.2.1", "192.0.2.2"],
              ttl=3600,
              type="A"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["2001:db8:10::1"],
              ttl=3600,
              type="AAAA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["0 issue \"ca.example.net\""],
              ttl=3600,
              type="CAA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "10 mail.zone.com.",
                  "20 mail2.zone.com.",
                  "50 mail3.zone.com."],
              ttl=3600,
              type="MX"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["ns.zone.com.", "ns.somewhere.example."],
              ttl=3600,
              type="NS"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. username.zone.com. "
                  "20071207 86400 7200 2419200 3600"],
              ttl=3600,
              type="SOA"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["\"v=spf1 mx:zone.com -all\"", "\"v=spf2\""],
              ttl=3600,
              type="SPF"),
          GetMessages().ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["\"v=spf1 mx:zone.com -all\"",
                       "\"v=spf2 z=esg\" \"hats\""],
              ttl=3600,
              type="TXT"),
      ]
  )


def GetImportReplaceChangeAfterCreation():
  r = GetMessages().Change()
  r.additions = GetImportReplaceChange().additions
  r.deletions = GetImportReplaceChange().deletions
  r.id = "2"
  r.startTime = "today 5 mins ago"
  r.status = (
      GetMessages().Change.StatusValueValuesEnum.done)
  return r


def GetImportReplaceChangeNoReplaceOrigin():
  r = GetMessages().Change()
  r.additions = (GetImportReplaceChange().additions)
  r.deletions = (GetImportReplaceChange().deletions)
  del r.additions[14]
  del r.deletions[3]
  return r
