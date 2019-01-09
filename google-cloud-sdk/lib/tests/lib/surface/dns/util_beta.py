# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util as dns_util
from googlecloudsdk.core import resources
from tests.lib.surface.dns import util


def GetMessages():
  return util.GetMessages("v1beta2")


def GetDnsVisibilityDict(version, visibility="public", network_urls=None):
  """Build visibility messages."""
  messages = GetMessages()
  result = {"visibility":
            messages.ManagedZone.VisibilityValueValuesEnum(visibility)}

  if visibility == "private":
    if network_urls:
      network_configs = [
          messages.ManagedZonePrivateVisibilityConfigNetwork(
              networkUrl=dns_util.GetRegistry(version).Parse(
                  nurl,
                  collection="compute.networks",
                  params={"project": "fake-project"}).SelfLink())
          for nurl in network_urls]
    else:
      network_configs = []

    pvcfg = messages.ManagedZonePrivateVisibilityConfig
    result["privateVisibilityConfig"] = pvcfg(networks=network_configs)
  return result


def ParseManagedZoneForwardingConfig(target_servers=None):
  """Parses list of forwarding nameservers into ManagedZoneForwardingConfig."""
  if not target_servers:
    return None

  messages = GetMessages()
  target_servers = [
      messages.ManagedZoneForwardingConfigNameServerTarget(ipv4Address=name)
      for name in target_servers
  ]

  return messages.ManagedZoneForwardingConfig(targetNameServers=target_servers)


def GetPolicies(num=3, name_server_config=None, forwarding=False,
                networks=None):
  m = GetMessages()
  return [
      m.Policy(
          alternativeNameServerConfig=name_server_config,
          description="My policy {}".format(i),
          enableInboundForwarding=forwarding,
          name="mypolicy{}".format(i),
          networks=GetPolicyNetworks(networks)) for i in range(num)
  ]


def GetAltNameServerConfig(target_servers=None):
  """Get ForwardingConfig Message."""
  if not target_servers:
    return None

  m = GetMessages()
  if target_servers == [""]:
    return None

  target_servers = [
      m.PolicyAlternativeNameServerConfigTargetNameServer(ipv4Address=name)
      for name in target_servers
  ]

  return m.PolicyAlternativeNameServerConfig(targetNameServers=target_servers)


def GetNetworkURI(network, project):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName("compute", "v1")
  network_ref = registry.Parse(
      network, params={"project": project}, collection="compute.networks")
  return network_ref.SelfLink()


def GetPolicyNetworks(urls, project="fake-project"):
  m = GetMessages()
  if urls == [""]:
    return []
  return [
      m.PolicyNetwork(networkUrl=GetNetworkURI(url, project)) for url in urls
  ]


def GetManagedZones():
  m = GetMessages()
  return [
      m.ManagedZone(
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
      m.ManagedZone(
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


def GetManagedZoneBeforeCreation(messages,
                                 dns_sec_config=False,
                                 visibility_dict=None,
                                 forwarding_config=None):
  """Generate a create message for a managed zone."""
  m = messages
  mzone = m.ManagedZone(
      creationTime=None,
      description="Zone!",
      dnsName="zone.com.",
      kind=u"dns#managedZone",
      name="mz",
      forwardingConfig=forwarding_config)

  if dns_sec_config:
    nonexistence = m.ManagedZoneDnsSecConfig.NonExistenceValueValuesEnum.nsec3
    mzone.dnssecConfig = m.ManagedZoneDnsSecConfig(
        defaultKeySpecs=[],
        kind=u"dns#managedZoneDnsSecConfig",
        nonExistence=nonexistence,
        state=m.ManagedZoneDnsSecConfig.StateValueValuesEnum.on,
    )

  if visibility_dict:
    mzone.visibility = visibility_dict["visibility"]
    if mzone.visibility == m.ManagedZone.VisibilityValueValuesEnum("private"):
      mzone.privateVisibilityConfig = visibility_dict["privateVisibilityConfig"]
  elif hasattr(messages.ManagedZone, "VisibilityValueValuesEnum"):
    mzone.visibility = messages.ManagedZone.VisibilityValueValuesEnum.public

  return mzone


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
  messages = GetMessages()
  return [
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["192.0.2.1",
                   "192.0.2.2"],
          ttl=3600, type="A"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["2001:db8:10::1"],
          ttl=3600, type="AAAA"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["10 mail.zone.com.",
                   "20 mail2.zone.com.",
                   "50 mail3.zone.com."],
          ttl=3600, type="MX"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["ns-cloud1.googledomains.com.",
                   "ns-cloud2.googledomains.com.",
                   "ns-cloud3.googledomains.com.",
                   "ns-cloud4.googledomains.com."],
          ttl=21600, type="NS"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["ns-cloud1.googledomains.com. "
                   "username.zone.com. 20071207 86400 7200 "
                   "2419200 3600"],
          ttl=3600, type="SOA"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"",
                   "\"v=spf2\""],
          ttl=3600, type="SPF"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"",
                   "\"v=spf2\""],
          ttl=3600, type="TXT"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="2.zone.com.",
          rrdatas=["server.zone.com."],
          ttl=600, type="PTR"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="hello.zone.com.",
          rrdatas=["zone.com."],
          ttl=3600, type="CNAME"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail.zone.com.",
          rrdatas=["192.0.2.3"],
          ttl=3600, type="A"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail2.zone.com.",
          rrdatas=["192.0.2.4"],
          ttl=3600, type="A"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail3.zone.com.",
          rrdatas=["192.0.2.5"],
          ttl=3600, type="A"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["192.0.2.2"],
          ttl=3600, type="A"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["2001:db8:10::2"],
          ttl=3600, type="AAAA"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="sip.zone.com.",
          rrdatas=["0 5 5060 sip.zone.com."],
          ttl=3600, type="SRV"),
      messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="wwwtest.zone.com.",
          rrdatas=["www.zone.com."],
          ttl=3600, type="CNAME"),
  ]


def GetImportedRecordSets():
  messages = GetMessages()
  return {
      ("zone.com.", "SOA"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["{0} username.zone.com. 20071207 86400 7200 2419200 3600"],
          ttl=3600,
          type="SOA"
      ),
      ("zone.com.", "NS"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["ns.zone.com.", "ns.somewhere.example."],
          ttl=3600,
          type="NS"
      ),
      ("zone.com.", "MX"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["10 mail.zone.com.", "20 mail2.zone.com.",
                   "50 mail3.zone.com."],
          ttl=3600,
          type="MX"
      ),
      ("zone.com.", "A"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["192.0.2.1", "192.0.2.2"],
          ttl=3600,
          type="A"
      ),
      ("zone.com.", "AAAA"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["2001:db8:10::1"],
          ttl=3600,
          type="AAAA"
      ),
      ("zone.com.", "SPF"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=["\"v=spf1 mx:zone.com -all\"", "\"v=spf2\""],
          ttl=3600,
          type="SPF"
      ),
      ("zone.com.", "TXT"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "\"v=spf1 mx:zone.com -all\"", "\"v=spf2 z=esg\" \"hats\""],
          ttl=3600,
          type="TXT"
      ),
      ("sip.zone.com.", "SRV"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="sip.zone.com.",
          rrdatas=["0 5 5060 sip.zone.com."],
          ttl=3600,
          type="SRV"
      ),
      ("test.zone.com.", "NS"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="test.zone.com.",
          rrdatas=["ns1.zone2.com.", "ns2.zone2.com."],
          ttl=3600,
          type="NS"
      ),
      ("hello.zone.com.", "CNAME"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="hello.zone.com.",
          rrdatas=["zone.com."],
          ttl=3600,
          type="CNAME"
      ),
      ("ns.zone.com.", "A"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["192.0.2.2"],
          ttl=3600,
          type="A"
      ),
      ("ns.zone.com.", "AAAA"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="ns.zone.com.",
          rrdatas=["2001:db8:10::2"],
          ttl=3600,
          type="AAAA"
      ),
      ("2.zone.com.", "PTR"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="2.zone.com.",
          rrdatas=["server.zone.com."],
          ttl=600,
          type="PTR"
      ),
      ("mail.zone.com.", "A"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail.zone.com.",
          rrdatas=["192.0.2.3"],
          ttl=3600,
          type="A"
      ),
      ("wwwtest.zone.com.", "CNAME"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="wwwtest.zone.com.",
          rrdatas=["www.zone.com."],
          ttl=3600,
          type="CNAME"
      ),
      ("mail2.zone.com.", "A"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail2.zone.com.",
          rrdatas=["192.0.2.4"],
          ttl=3600,
          type="A"
      ),
      ("mail3.zone.com.", "A"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="mail3.zone.com.",
          rrdatas=["192.0.2.5"],
          ttl=3600,
          type="A"
      ),
      ("zone.com.", "DNSKEY"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "256 3 5 AQPSKmynfzW4kyBv015MUG2DeIQ3Cbl+ BBZH4b/0PY1kxkmvHjcZc8"
              "nokfzj31Ga jIQKY+5CptLr3buXA10hWqTkF7H6RfoR qXQeogmMHfpftf6zMv1"
              "LyBUgia7za6ZE zOJBOztyvhjL742iU/TpPSEDhm2SNKLi jfUppn1UaNvv4w=="
          ],
          signatureRrdatas=[
          ],
          ttl=600,
          type="DNSKEY",
      ),
      ("test.zone.com.", "DS"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="test.zone.com.",
          rrdatas=[
              "60485 5 1 2bb183af5f22588179a53b0a98631fad1a292118",
          ],
          signatureRrdatas=[
          ],
          ttl=3600,
          type="DS",
      ),
      ("zone.com.", "IPSECKEY"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "10 3 2 mygateway.example.com. AQNRU3mG7TVTO2BkR47usntb102uFJtu "
              "gbo6BSGvgqt4AQ==",
          ],
          signatureRrdatas=[
          ],
          ttl=3600,
          type="IPSECKEY",
      ),
      ("zone.com.", "SSHFP"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "2 1 123456789abcdef67890123456789abcdef67890",
          ],
          signatureRrdatas=[
          ],
          ttl=3600,
          type="SSHFP",
      ),
      ("zone.com.", "TLSA"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "0 0 1 d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106"
              "618e971",
          ],
          signatureRrdatas=[
          ],
          ttl=3600,
          type="TLSA",
      ),
      ("zone.com.", "NAPTR"): messages.ResourceRecordSet(
          kind="dns#resourceRecordSet",
          name="zone.com.",
          rrdatas=[
              "100 50 \"s\" \"z3950+I2L+I2C\" \"\" _z3950._tcp.gatech.edu.",
          ],
          signatureRrdatas=[
          ],
          ttl=3600,
          type="NAPTR",
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
  messages = GetMessages()
  return messages.Change(
      deletions=[
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                  "21600 3600 1209600 300"],
              ttl=21601,
              type="SOA"),
      ],
      additions=[
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="2.zone.com.",
              rrdatas=["server.zone.com."],
              ttl=600,
              type="PTR"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="hello.zone.com.",
              rrdatas=["zone.com."],
              ttl=3600,
              type="CNAME"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail2.zone.com.",
              rrdatas=["192.0.2.4"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail3.zone.com.",
              rrdatas=["192.0.2.5"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["192.0.2.2"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["2001:db8:10::2"],
              ttl=3600,
              type="AAAA"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="sip.zone.com.",
              rrdatas=["0 5 5060 sip.zone.com."],
              ttl=3600,
              type="SRV"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="test.zone.com.",
              rrdatas=[
                  "60485 5 1 2bb183af5f22588179a53b0a98631fad1a292118",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="DS",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="test.zone.com.",
              rrdatas=["ns1.zone2.com.", "ns2.zone2.com."],
              ttl=3600,
              type="NS"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="wwwtest.zone.com.",
              rrdatas=["www.zone.com."],
              ttl=3600,
              type="CNAME"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["2001:db8:10::1"],
              ttl=3600,
              type="AAAA"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "256 3 5 AQPSKmynfzW4kyBv015MUG2DeIQ3Cbl+ "
                  "BBZH4b/0PY1kxkmvHjcZc8nokfzj31Ga "
                  "jIQKY+5CptLr3buXA10hWqTkF7H6RfoR "
                  "qXQeogmMHfpftf6zMv1LyBUgia7za6ZE "
                  "zOJBOztyvhjL742iU/TpPSEDhm2SNKLi jfUppn1UaNvv4w==",
              ],
              signatureRrdatas=[
              ],
              ttl=600,
              type="DNSKEY",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "10 3 2 mygateway.example.com. "
                  "AQNRU3mG7TVTO2BkR47usntb102uFJtu gbo6BSGvgqt4AQ==",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="IPSECKEY",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "10 mail.zone.com.",
                  "20 mail2.zone.com.",
                  "50 mail3.zone.com."],
              ttl=3600,
              type="MX"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "100 50 \"s\" \"z3950+I2L+I2C\" \"\" _z3950._tcp.gatech.edu.",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="NAPTR",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. dns-admin.google.com. 3 "
                  "21600 3600 1209600 300"],
              ttl=21601,
              type="SOA"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["\"v=spf1 mx:zone.com -all\"", "\"v=spf2\""],
              ttl=3600,
              type="SPF"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "2 1 123456789abcdef67890123456789abcdef67890",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="SSHFP",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "0 0 1 "
                  "d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106618"
                  "e971",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="TLSA",
          ),
          messages.ResourceRecordSet(
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
  messages = GetMessages()
  return messages.Change(
      deletions=[
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail.zone.com.",
              rrdatas=["5.6.7.8"],
              ttl=21600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="www.zone.com.",
              rrdatas=[
                  "zone.com."
              ],
              ttl=21600,
              type="CNAME"
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["1.2.3.4"],
              ttl=21600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com.",
                  "ns-cloud-e2.googledomains.com.",
                  "ns-cloud-e3.googledomains.com.",
                  "ns-cloud-e4.googledomains.com."],
              ttl=21600,
              type="NS"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 "
                  "21600 3600 1209600 300"],
              ttl=21601,
              type="SOA"),
      ],
      additions=[
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="2.zone.com.",
              rrdatas=["server.zone.com."],
              ttl=600,
              type="PTR"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="hello.zone.com.",
              rrdatas=["zone.com."],
              ttl=3600,
              type="CNAME"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail.zone.com.",
              rrdatas=["192.0.2.3"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail2.zone.com.",
              rrdatas=["192.0.2.4"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="mail3.zone.com.",
              rrdatas=["192.0.2.5"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["192.0.2.2"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="ns.zone.com.",
              rrdatas=["2001:db8:10::2"],
              ttl=3600,
              type="AAAA"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="sip.zone.com.",
              rrdatas=["0 5 5060 sip.zone.com."],
              ttl=3600,
              type="SRV"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="test.zone.com.",
              rrdatas=[
                  "60485 5 1 2bb183af5f22588179a53b0a98631fad1a292118",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="DS",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="test.zone.com.",
              rrdatas=["ns1.zone2.com.", "ns2.zone2.com."],
              ttl=3600,
              type="NS"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="wwwtest.zone.com.",
              rrdatas=["www.zone.com."],
              ttl=3600,
              type="CNAME"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["192.0.2.1", "192.0.2.2"],
              ttl=3600,
              type="A"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["2001:db8:10::1"],
              ttl=3600,
              type="AAAA"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "256 3 5 AQPSKmynfzW4kyBv015MUG2DeIQ3Cbl+ "
                  "BBZH4b/0PY1kxkmvHjcZc8nokfzj31Ga "
                  "jIQKY+5CptLr3buXA10hWqTkF7H6RfoR "
                  "qXQeogmMHfpftf6zMv1LyBUgia7za6ZE "
                  "zOJBOztyvhjL742iU/TpPSEDhm2SNKLi jfUppn1UaNvv4w==",
              ],
              signatureRrdatas=[
              ],
              ttl=600,
              type="DNSKEY",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "10 3 2 mygateway.example.com. "
                  "AQNRU3mG7TVTO2BkR47usntb102uFJtu gbo6BSGvgqt4AQ==",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="IPSECKEY",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "10 mail.zone.com.",
                  "20 mail2.zone.com.",
                  "50 mail3.zone.com."],
              ttl=3600,
              type="MX"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "100 50 \"s\" \"z3950+I2L+I2C\" \"\" _z3950._tcp.gatech.edu.",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="NAPTR",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["ns.zone.com.", "ns.somewhere.example."],
              ttl=3600,
              type="NS"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "ns-cloud-e1.googledomains.com. username.zone.com. "
                  "20071207 86400 7200 2419200 3600"],
              ttl=3600,
              type="SOA"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=["\"v=spf1 mx:zone.com -all\"", "\"v=spf2\""],
              ttl=3600,
              type="SPF"),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "2 1 123456789abcdef67890123456789abcdef67890",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="SSHFP",
          ),
          messages.ResourceRecordSet(
              kind="dns#resourceRecordSet",
              name="zone.com.",
              rrdatas=[
                  "0 0 1 "
                  "d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106618"
                  "e971",
              ],
              signatureRrdatas=[
              ],
              ttl=3600,
              type="TLSA",
          ),
          messages.ResourceRecordSet(
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
  del r.additions[17]
  del r.deletions[3]
  return r
