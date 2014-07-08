#!/usr/bin/python

import urllib
import os
import sys
import xml.dom.minidom
import re
import base64
import hmac
import hashlib
import httplib
import time
import marvin
import json
import urllib
import urllib2
import logging

from marvin.cloudstackConnection import cloudConnection
from marvin.cloudstackException import cloudstackAPIException
from marvin.cloudstackAPI import *
from marvin import cloudstackAPI

from CSUtils import *

utils = CSUtils()  
conn = utils.getConnection()


# Query Zone
lz = listZones.listZonesCmd()
lz.available = True
resp = conn.marvinRequest(lz)
zone = resp[0]

# Create Network
lno = listNetworkOfferings.listNetworkOfferingsCmd()
lno.name="DefaultIsolatedNetworkOfferingWithSourceNatService"
resp = conn.marvinRequest(lno)
offering = resp[0]

cn = createNetwork.createNetworkCmd()
cn.name = "test_isolated"
cn.displaytext = "Test Isolated"
cn.networkofferingid = offering.id
cn.zoneid = zone.id
resp = conn.marvinRequest(cn)
network = resp.network

# Create Instance
lt = listTemplates.listTemplatesCmd()
lt.name = "tiny Linux"
lt.templatefilter="all"
resp = conn.marvinRequest(lt)
template = resp[0]

lso = listServiceOfferings.listServiceOfferingsCmd()
lso.name = "tinyOffering"
resp = conn.marvinRequest(lso)
serviceOffering = resp[0]

dv = deployVirtualMachine.deployVirtualMachineCmd()
dv.zoneid = zone.id
dv.templateid=template.id
dv.serviceofferingid=serviceOffering.id
dv.networkids.append(network.id)
resp = conn.marvinRequest(dv)
print repr(resp)

