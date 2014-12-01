#!/usr/bin/python

from marvin.asyncJobMgr import asyncJobMgr
from marvin.codes import (FAILED, PASS, ADMIN, DOMAIN_ADMIN,
                          USER, SUCCESS, XEN_SERVER)
from marvin.dbConnection import DbConnection
from marvin.cloudstackAPI import *
from marvin.cloudstackAPI.cloudstackAPIClient import CloudStackAPIClient
from marvin.cloudstackException import CloudstackAPIException
from marvin.cloudstackException import GetDetailExceptionInfo
from marvin.cloudstackConnection import CSConnection
from marvin.configGenerator import ConfigManager
from marvin.lib.utils import (random_gen, validateList)

from CSUtils import *
import json
import time
import sys

utils = CSUtils()
conn = utils.getConnection()
apiclient = CloudStackAPIClient(conn)


# Query Zone
lz = listZones.listZonesCmd()
lz.available = True
resp = apiclient.listZones(lz)
zone = resp[0]

# Create SSH Keys
rsk = registerSSHKeyPair.registerSSHKeyPairCmd()
rsk.name = "UploadedSSHKey"
rsk.publickey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC2D2Cs0XAEqm+ajJpumIPrMpKp0CWtIW+8ZY2/MJCWhge1eY18u9I3PPnkMVJsTOaN0wQojjw4AkKgKjNZXA9wyUq56UyN/stmipu8zifWPgxQGDRkuzzZ6bukef8q2Awjpo8hv5/0SRPJxQLEafESnUP+Uu/LUwk5VVC7PHzywJRUGFuzDl/uT72+6hqpL2YpC6aTl4/P2eDvUQhCdL9dBmUSFX8ftT53W1jhsaQl7mPElVgSCtWz3IyRkogobMPrpJW/IPKEiojKIuvNoNv4CDR6ybeVjHOJMb9wi62rXo+CzUsW0Y4jPOX/OykAm5vrNOhQhw0aaBcv5XVv8BRX hugo@Hugos-MacBook-Pro.local"
resp = apiclient.registerSSHKeyPair(rsk)
key_name = resp.name
print "Uploaded key %s with fingerprint %s" % (key_name, resp.fingerprint)

# Create Network
lno = listNetworkOfferings.listNetworkOfferingsCmd()
lno.name="DefaultIsolatedNetworkOfferingWithSourceNatService"
resp = apiclient.listNetworkOfferings(lno)
offering = resp[0]

cn = createNetwork.createNetworkCmd()
cn.name = "test_isolated"
cn.displaytext = "Test Isolated"
cn.networkofferingid = offering.id
cn.zoneid = zone.id
network = apiclient.createNetwork(cn)

# Create Instance
lt = listTemplates.listTemplatesCmd()
lt.name = "tiny Linux"
lt.templatefilter="all"
resp = apiclient.listTemplates(lt)
template = resp[0]

lso = listServiceOfferings.listServiceOfferingsCmd()
lso.name = "tinyOffering"
resp = apiclient.listServiceOfferings(lso)
serviceOffering = resp[0]

dv = deployVirtualMachine.deployVirtualMachineCmd()
dv.zoneid = zone.id
dv.templateid=template.id
dv.serviceofferingid=serviceOffering.id
dv.networkids.append(network.id)
dv.keypair=key_name
machine = apiclient.deployVirtualMachine(dv)
print repr(machine)
