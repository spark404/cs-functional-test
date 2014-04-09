#!/usr/bin/python

from CSUtils import *
import json
import time
import sys

utils = CSUtils()  
conn = utils.getConnection()

listsvm = listSystemVms.listSystemVmsCmd()

count = 40
while count > 0 :
  # Sleep 15 seconds
  time.sleep(15)
  count = count - 1
  ssvm = None

  # Check if we have an ssvm
  print "Looking for systemvm of type secondarystoragevm"
  try:
   resp = conn.marvinRequest(listsvm)
   if resp == None or len(resp) == 0 :
     continue
   for svm in resp:
     if svm.systemvmtype == "secondarystoragevm":
       if not svm.state == "Running" : 
         print "SSVM has state " + svm.state + " waiting for it to become Running"
       else :
         ssvm = svm
  except urllib2.HTTPError, e:
     print "Cmd Failed : " + str(e.msg)

  if ssvm :
    print "Found " + ssvm.name
    print "Determining state"
  
    listhosts = listHosts.listHostsCmd()
    listhosts.name = ssvm.name
    
    try:
       resp = conn.marvinRequest(listhosts)
       if len(resp) == 1 :
          ssvmstate = resp[0]
       else :
          continue
           
    except urllib2.HTTPError, e:
       print "Cmd Failed : " + str(e.msg)
    
    if ssvmstate.state == "Up":
      print "SSVM " + ssvm.name + " is " + ssvm.state + " and the agent is " + ssvmstate.state
      break
    else :
      print "SSVM Agent not yet Up, current state is  " + ssvmstate.state

if count == 0 :
    sys.exit(1)
