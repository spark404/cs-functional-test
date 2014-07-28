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
machine = apiclient.deployVirtualMachine(dv)
print repr(machine)
