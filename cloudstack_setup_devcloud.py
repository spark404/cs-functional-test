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

config = {
    'management_server' : 'localhost',
    'hypervisor_type' : 'XenServer',
    'primarystorage' : 'mccdxpl2_primary'
}
  

utils = CSUtils()  
conn = utils.getConnection()

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
   resp = conn.marvinRequest(listconfig)
   for item in resp:
      if item.name == "host":
         if item.value == "10.200.23.18":
            print "OK, host is correct"
         else:
            print "Incorrect host setting, updating configuration"
            updateConf = updateConfiguration.updateConfigurationCmd()
            for key,value in configuration.iteritems():
               updateConf.name = key
               updateConf.value = value
               try:
                  resp = conn.marvinRequest(updateConf)
                  print "Set " + key + " to " + str(value)
               except urllib2.HTTPError, e:
                  print "updateConfigurationCmd failed to set " + key + " : " + str(e.msg)  
               
except urllib2.HTTPError, e:
   print "listConfigurationsCmd Failed : " + str(e.msg)
   exit()
            
zoneCmd = createZone.createZoneCmd()
zoneCmd.name         = "MCCDZone"
zoneCmd.networktype  = "Advanced"
zoneCmd.dns1         = "8.8.8.8"
zoneCmd.dns2         = "8.8.8.4"
zoneCmd.internaldns1 = "192.168.56.1"
zoneCmd.domain       = "devcloud.local"
zoneCmd.localstorageenabled = "true"
zoneCmd.guestcidraddress = "10.1.1.1/24"

try:
   resp = conn.marvinRequest(zoneCmd)
   zone = resp.zone
   print "Zone " + zone.name + " created"
except urllib2.HTTPError, e:
   print "createZoneCmd Failed : " + str(e.msg)

# Setup physical network for Management and Public
physNetCmd = createPhysicalNetwork.createPhysicalNetworkCmd()
physNetCmd.name      = "DevCloud Mgmt"
physNetCmd.zoneid    = zone.id
physNetCmd.isolationmethods = [ "VLAN" ]
try:
   resp = conn.marvinRequest(physNetCmd)
   physNetManagement = resp.physicalnetwork
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

# Add traffic type Management
addTrafficTypeCmd = addTrafficType.addTrafficTypeCmd()
addTrafficTypeCmd.physicalnetworkid = physNetManagement.id
addTrafficTypeCmd.traffictype = "Management"
addTrafficTypeCmd.xennetworklabel = "xenbr0"
try:
    resp = conn.marvinRequest(addTrafficTypeCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

# Add traffic type Public
addTrafficTypeCmd.traffictype = "Public"
addTrafficTypeCmd.xennetworklabel = "xenbr1"
try:
    resp = conn.marvinRequest(addTrafficTypeCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

updatePhysNet = updatePhysicalNetwork.updatePhysicalNetworkCmd();
updatePhysNet.id = physNetManagement.id
updatePhysNet.state = "Enabled"
try:
    resp = conn.marvinRequest(updatePhysNet)
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
   resp = conn.marvinRequest(physNetCmd)
   physNetGuest = resp.physicalnetwork
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

# Add guest traffic label
addTrafficTypeCmd.physicalnetworkid = physNetGuest.id
addTrafficTypeCmd.traffictype = "Guest"
addTrafficTypeCmd.xennetworklabel = "xenbr0"
try:
    resp = conn.marvinRequest(addTrafficTypeCmd)
except urllib2.HTTPError, e:
   print "createPhysicalNetworkCmd Failed : " + str(e.msg)

updatePhysNet = updatePhysicalNetwork.updatePhysicalNetworkCmd();
updatePhysNet.id = physNetGuest.id
updatePhysNet.state = "Enabled"
try:
    resp = conn.marvinRequest(updatePhysNet)
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
    resp = conn.marvinRequest(createVlan)
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
createPod.gateway = "192.168.56.1"
createPod.netmask = "255.255.255.0"
try:
    resp = conn.marvinRequest(createPod)
    pod = resp.pod
except urllib2.HTTPError, e:
   print "createPodCmd Failed : " + str(e.msg)
print "Pod " + pod.name + " created"

# Add secondary storage
addSecondary = addSecondaryStorage.addSecondaryStorageCmd()
addSecondary.zoneid = zone.id
addSecondary.url    = "nfs://192.168.56.10/opt/storage/secondary"
try:
    resp = conn.marvinRequest(addSecondary)
    secstor = resp.secondarystorage
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
		resp = conn.marvinRequest(addCluster)
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
		resp = conn.marvinRequest(addXen)
		xenhosts = resp
	except urllib2.HTTPError, e:
	   print "addCluster Failed : " + str(e.msg)
	for xenbox in xenhosts:
	   print "XenServer " + xenbox.name + " added to cluster " + xencluster.name


listVR = listVirtualRouterElements.listVirtualRouterElementsCmd()
confVR = configureVirtualRouterElement.configureVirtualRouterElementCmd()
confVR.enabled = True
try:
    resp = conn.marvinRequest(listVR)
    for vrnsp in resp:
        confVR.id = vrnsp.id
        conn.marvinRequest(confVR)
except urllib2.HTTPError, e:
   print "configureVirtualRouterElementCmd Failed : " + str(e.msg)

listILB = listInternalLoadBalancerElements.listInternalLoadBalancerElementsCmd()
confILB = configureInternalLoadBalancerElement.configureInternalLoadBalancerElementCmd()
confILB.enabled = True
try:
    resp = conn.marvinRequest(listILB)
    for ilbnsp in resp:
        confILB.id = ilbnsp.id
        conn.marvinRequest(confILB)
except urllib2.HTTPError, e:
   print "configureInternalLoadBalancerElement Failed : " + str(e.msg)

listNsp = listNetworkServiceProviders.listNetworkServiceProvidersCmd()
updateNsp = updateNetworkServiceProvider.updateNetworkServiceProviderCmd()
try:
    resp = conn.marvinRequest(listNsp)
    for nsp in resp:
       if nsp.name in [ "VirtualRouter", "VpcVirtualRouter", "InternalLbVm" ] :
           updateNsp.id    = nsp.id
           updateNsp.state = "Enabled"
           resp = conn.marvinRequest(updateNsp)
           nsp = resp.networkserviceprovider
           print "Network Service Provider " + nsp.name + " is " + nsp.state
except urllib2.HTTPError, e:
   print "updateNetworkServiceProviderCmd Failed : " + str(e.msg)

# Enable Zone
updZone = updateZone.updateZoneCmd()
updZone.id = zone.id
updZone.allocationstate = "Enabled"
try:
     resp = conn.marvinRequest(updZone)
     nvpdev = resp.niciranvpdevice
except urllib2.HTTPError, e:
      print "updateZoneCmd Failed : " + str(e.msg)
print "Zone " + zone.name + " is Enabled"



