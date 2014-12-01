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

config = {
    'management_server' : 'localhost',
    'hypervisor_type' : 'XenServer',
    'primarystorage' : 'mccdxpl2_primary'
}
  

utils = CSUtils()  
conn = utils.getConnection()
apiclient = CloudStackAPIClient(conn)

configuration = {
   'cpu.overprovisioning.factor'     : 10,
   'mem.overprovisioning.factor'     : 10,
   'storage.overprovisioning.factor' : 4,
   'expunge.delay'                   : 120,
   'expunge.interval'                : 60,
   'network.gc.interval'             : 60,
   'network.gc.wait'                 : 120
   }

listconfig = listConfigurations.listConfigurationsCmd()
try:
   resp = apiclient.listConfigurations(listconfig)
   for item in resp:
      if item.name == "cpu.overprovisioning.factor":
         if item.value == configuration["cpu.overprovisioning.factor"]:
            print "OK, host is correct"
         else:
            print "Incorrect configuration"
            updateConf = updateConfiguration.updateConfigurationCmd()
            for key,value in configuration.iteritems():
               updateConf.name = key
               updateConf.value = value
               try:
                  resp = apiclient.updateConfiguration(updateConf)
                  print "Set " + key + " to " + str(value)
               except urllib2.HTTPError, e:
                  print "updateConfigurationCmd failed to set " + key + " : " + str(e.msg)  
               
except urllib2.HTTPError, e:
   print "listConfigurationsCmd Failed : " + str(e.msg)
   exit()
            
zoneCmd = createZone.createZoneCmd()
zoneCmd.name         = "MCCDZone5"
zoneCmd.networktype  = "Advanced"
zoneCmd.dns1         = "8.8.8.8"
zoneCmd.dns2         = "8.8.8.4"
zoneCmd.internaldns1 = "192.168.56.2"
zoneCmd.domain       = "devcloud.local"
zoneCmd.localstorageenabled = "true"
zoneCmd.guestcidraddress = "10.1.1.1/24"

try:
   zone = apiclient.createZone(zoneCmd)
   print "Zone " + zone.name + " created"
except urllib2.HTTPError, e:
   print "createZoneCmd Failed : " + str(e.msg)

# Setup physical network for Management and Public
physNetCmd = createPhysicalNetwork.createPhysicalNetworkCmd()
physNetCmd.name      = "DevCloud Mgmt"
physNetCmd.zoneid    = zone.id
physNetCmd.isolationmethods = [ "VLAN" ]
try:
   physNetManagement = apiclient.createPhysicalNetwork(physNetCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

# Add traffic type Management
addTrafficTypeCmd = addTrafficType.addTrafficTypeCmd()
addTrafficTypeCmd.physicalnetworkid = physNetManagement.id
addTrafficTypeCmd.traffictype = "Management"
addTrafficTypeCmd.xennetworklabel = "xenbr0"
try:
    resp = apiclient.addTrafficType(addTrafficTypeCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

# Add traffic type Public
addTrafficTypeCmd.traffictype = "Public"
addTrafficTypeCmd.xennetworklabel = "xenbr1"
try:
    resp = apiclient.addTrafficType(addTrafficTypeCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

updatePhysNet = updatePhysicalNetwork.updatePhysicalNetworkCmd();
updatePhysNet.id = physNetManagement.id
updatePhysNet.state = "Enabled"
try:
    resp = apiclient.updatePhysicalNetwork(updatePhysNet)
except urllib2.HTTPError, e:
   print "updatePhysicalNetworkCmd Failed : " + str(e.msg)

print "Physical network " + physNetManagement.name + " created for Management and Public traffic"

# Setup physical network for Guest traffic
physNetCmd = createPhysicalNetwork.createPhysicalNetworkCmd()
physNetCmd.name      = "DevCloud Guest"
physNetCmd.zoneid    = zone.id
physNetCmd.isolationmethods = [ "VLAN" ]
physNetCmd.vlan      = "100-300"
try:
   physNetGuest = apiclient.createPhysicalNetwork(physNetCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

# Add guest traffic label
addTrafficTypeCmd.physicalnetworkid = physNetGuest.id
addTrafficTypeCmd.traffictype = "Guest"
addTrafficTypeCmd.xennetworklabel = "xenbr0"
try:
    resp = apiclient.addTrafficType(addTrafficTypeCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

updatePhysNet = updatePhysicalNetwork.updatePhysicalNetworkCmd();
updatePhysNet.id = physNetGuest.id
updatePhysNet.state = "Enabled"
try:
    resp = apiclient.updatePhysicalNetwork(updatePhysNet)
except urllib2.HTTPError, e:
   print "updatePhysicalNetworkCmd Failed : " + str(e.msg)

print "Physical network " + physNetGuest.name + " created for Guest traffic"

# Add public network ip range
createVlan = createVlanIpRange.createVlanIpRangeCmd()
createVlan.zoneid  = zone.id
createVlan.gateway = "10.0.2.1"
createVlan.netmask = "255.255.255.0"
createVlan.startip = "10.0.2.100" 
createVlan.endip   = "10.0.2.150"
createVlan.forvirtualnetwork = True
try:
    resp = apiclient.createVlanIpRange(createVlan)
    vlan = resp.vlan
except urllib2.HTTPError, e:
   print "createVlanIpRangeCmd Failed : " + str(e.msg)
print "Vlan for public internet created on vlanid " + vlan.vlan

# Add Pod
createPod = createPod.createPodCmd()
createPod.name    = "Pod"
createPod.zoneid  = zone.id
createPod.startip = "192.168.56.100"
createPod.endip   = "192.168.56.119"
createPod.gateway = "192.168.56.2"
createPod.netmask = "255.255.255.0"
try:
    pod = apiclient.createPod(createPod)
except urllib2.HTTPError, e:
   print "createPodCmd Failed : " + str(e.msg)
print "Pod " + pod.name + " created"

# Add secondary storage
addSecondary = addSecondaryStorage.addSecondaryStorageCmd()
addSecondary.zoneid = zone.id
addSecondary.url    = "nfs://192.168.56.9/export/secondary"
try:
    secstor = apiclient.addSecondaryStorage(addSecondary)
except urllib2.HTTPError, e:
   print "addCluster Failed : " + str(e.msg)
print "Secondary storage added : " + secstor.name

if (config.get('hypervisor_type') == "XenServer") :
	# Add XenCluster
	addCluster = addCluster.addClusterCmd()
	addCluster.clustername = "XenCluster"
	addCluster.clustertype = "CloudManaged"
	addCluster.hypervisor  = "XenServer"
	addCluster.podid       = pod.id
	addCluster.zoneid      = zone.id
	try:
		resp = apiclient.addCluster(addCluster)
		xencluster = resp[0]
	except urllib2.HTTPError, e:
	   print "addCluster Failed : " + str(e.msg)
	print "Cluster " + xencluster.name + " created for " + xencluster.hypervisortype + " hypervisors"


	# Add Xen Host (Pool)
	addXen = addHost.addHostCmd()
	addXen.hypervisor = "XenServer"
	addXen.zoneid     = zone.id
	addXen.podid      = pod.id
	addXen.clusterid  = xencluster.id
	addXen.url        = "http://192.168.56.11"
	addXen.username   = "root"
	addXen.password   = "password"
	try:
		xenhosts = apiclient.addHost(addXen)
	except urllib2.HTTPError, e:
	   print "addCluster Failed : " + str(e.msg)
	for xenbox in xenhosts:
	   print "XenServer " + xenbox.name + " added to cluster " + xencluster.name


listVR = listVirtualRouterElements.listVirtualRouterElementsCmd()
confVR = configureVirtualRouterElement.configureVirtualRouterElementCmd()
confVR.enabled = True
try:
    resp = apiclient.listVirtualRouterElements(listVR)
    for vrnsp in resp:
        confVR.id = vrnsp.id
        apiclient.configureVirtualRouterElement(confVR)
except urllib2.HTTPError, e:
   print "configureVirtualRouterElementCmd Failed : " + str(e.msg)

listILB = listInternalLoadBalancerElements.listInternalLoadBalancerElementsCmd()
confILB = configureInternalLoadBalancerElement.configureInternalLoadBalancerElementCmd()
confILB.enabled = True
try:
    resp = apiclient.listInternalLoadBalancerElements(listILB)
    for ilbnsp in resp:
        confILB.id = ilbnsp.id
        apiclient.configureInternalLoadBalancerElement(confILB)
except urllib2.HTTPError, e:
   print "configureInternalLoadBalancerElement Failed : " + str(e.msg)

listNsp = listNetworkServiceProviders.listNetworkServiceProvidersCmd()
updateNsp = updateNetworkServiceProvider.updateNetworkServiceProviderCmd()
try:
    resp = apiclient.listNetworkServiceProviders(listNsp)
    for nsp in resp:
       if nsp.name in [ "VirtualRouter", "VpcVirtualRouter", "InternalLbVm" ] :
           updateNsp.id    = nsp.id
           updateNsp.state = "Enabled"
           nsp = apiclient.updateNetworkServiceProvider(updateNsp)
           print "Network Service Provider " + nsp.name + " is " + nsp.state
except urllib2.HTTPError, e:
   print "updateNetworkServiceProviderCmd Failed : " + str(e.msg)

# Enable Zone
updZone = updateZone.updateZoneCmd()
updZone.id = zone.id
updZone.allocationstate = "Enabled"
try:
     zone = apiclient.updateZone(updZone)
except urllib2.HTTPError, e:
      print "updateZoneCmd Failed : " + str(e.msg)
print "Zone " + zone.name + " is Enabled"



