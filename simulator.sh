#!/bin/bash

export MAVEN_OPTS="-Xmx2048m -XX:MaxPermSize=512m"
export SCRIPT_LOCATION='/home/spark/git-workdir/cs-functional-test'
export DEVCLOUD=192.168.56.94
export HYPERVISOR=192.168.56.234
export PATH=/usr/local/bin:$PATH


args=`getopt npb $*`
if [ $? != 0 ] 
then
  echo $0 [-p] [-b]
  echo  specify -p to stop after preparing the test environment
  echo  specify -b to build cloudstack before starting the test cycle
  echo  specify -n to activate the noredist profile
  exit
fi

set -- $args
for i do
  case $i in
  -p)
    PREPARE=1
    ;;
  -b)
    BUILD=1
    ;;
  -n)
    NOREDIST=" -Dnoredist "
    ;;
  esac
done

if [ ! -z "${BUILD}" ]
 then
  echo Building CloudStack
  mvn -Psystemvm,developer -Dsimulator ${NOREDIST} clean install
fi

echo Cleanup from previous runs
rm -f vmops.log
rm -f jetty-console.out

echo Fix database host
sed -i"" -e 's/^DBHOST=.*/DBHOST='${DEVCLOUD}'/' build/replace.properties

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
mvn -P developer -Dsimulator ${NOREDIST} -Ddeploydb -pl developer 
mvn -P developer -pl developer -Ddeploydb-simulator

echo Start CloudStack
mvn -P systemvm -Dsimulator ${NOREDIST} -pl :cloud-client-ui jetty:run > jetty-console.out 2>&1 &
SERVER_PID=$!

echo Check for initialization of the management server
COUNTER=0
while [ "$COUNTER" -lt 44 ] ; do
    if grep -q 'Management server node 127.0.0.1 is up' jetty-console.out ; then
        break
    fi
    sleep 5
    COUNTER=$(($COUNTER+1))
done

if grep -q 'Management server node 127.0.0.1 is up' jetty-console.out ; then
   echo Started OK pid ${SERVER_PID}
   sleep 20
   
   python tools/marvin/marvin/deployDataCenter.py -i setup/dev/advanced.cfg

   /usr/local/bin/nosetests-2.7 --with-marvin --marvin-config=../cs-functional-test/simulator.cfg --with-xunit --xunit-file=xunit.xml -a tags=advanced,required_hardware=false --zone=Sandbox-simulator --hypervisor=simulator -w test/integration/smoke
fi


mvn -P systemvm -pl :cloud-client-ui jetty:stop
sleep 30
kill -KILL $SERVER_PID

