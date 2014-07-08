#!/bin/bash

export MAVEN_OPTS="-Xmx2048m -XX:MaxPermSize=512m"
export SCRIPT_LOCATION='/Users/hugo/Dropbox/CloudStack/Python scripts/'
export DEVCLOUD=192.168.56.10
export DEVCLOUD_VBOX=DevCloud2
export HYPERVISOR=192.168.56.11
export HYPERVISOR_VBOX=DevCloudXen6.2

rm -f vmops.log
rm -f jetty-console.out

VBoxManage startvm ${DEVCLOUD_VBOX}
if [ $? -ne 0 ]
then
  echo Failed to start ${DEVCLOUD_VBOX}
fi

VBoxManage startvm ${HYPERVISOR_VBOX}
if [ $? -ne 0 ]
then
  echo Failed to start ${HYPERVISOR_VBOX}
fi

echo Fix database host
sed -i "" -e 's/^DBHOST=.*/DBHOST='${DEVCLOUD}'/' build/replace.properties

echo Waiting for database server to become available
COUNT=0
ssh -o BatchMode=true root@${DEVCLOUD} exit
RETVAL=$?
while [ $RETVAL -ne 0 ]
do
    sleep 1
    echo Trying to connect to ${DEVCLOUD}
    ssh -o BatchMode=true root@${DEVCLOUD} exit
    RETVAL=$?
done

echo Update the database
mvn -P developer -Ddeploydb -pl developer 

echo Waiting for xen server to become available
COUNT=0
ssh -o BatchMode=true root@${HYPERVISOR} exit
RETVAL=$?
while [ $RETVAL -ne 0 ]
do
    sleep 1
    echo Trying to connect to ${HYPERVISOR}
    ssh -o BatchMode=true root@${HYPERVISOR} exit
    RETVAL=$?
done

echo Clean the xenserver
sleep 15
python "${SCRIPT_LOCATION}"/xapi_cleanup_xenservers.py http://${HYPERVISOR} root password

echo Start CloudStack
mvn -P systemvm -pl :cloud-client-ui jetty:run > jetty-console.out 2>&1 &
SERVER_PID=$!

# Check for initialization of the management server
COUNTER=0
while [ "$COUNTER" -lt 34 ] ; do
    if grep -q 'Management server node 127.0.0.1 is up' jetty-console.out ; then
        break
    fi
    sleep 5
    COUNTER=$(($COUNTER+1))
done


if grep -q 'Management server node 127.0.0.1 is up' jetty-console.out ; then
   echo Started OK
   sleep 20
   echo Provisioning CloudStack with devcloud zone
   python "${SCRIPT_LOCATION}"/cloudstack_setup_devcloud.py
   python "${SCRIPT_LOCATION}"/cloudstack_checkssvmalive.py
   sleep 30
   python "${SCRIPT_LOCATION}"/cloudstack_test_basic_instance.py
fi


if [ "$1" == "preponly" ] ; then
   echo "CloudStack running with PID $SERVER_PID"
   exit
fi

mvn -P systemvm -pl :cloud-client-ui jetty:stop
sleep 30
kill -KILL $SERVER_PID

echo Shutting down test servers
ssh -o BatchMode=true root@${HYPERVISOR} poweroff
sleep 20
ssh -o BatchMode=true root@${DEVCLOUD} poweroff
