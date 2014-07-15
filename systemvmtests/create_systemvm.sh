#!/bin/bash

VBOXMNG="/usr/bin/VBoxManage"
ROUTERIP=192.168.56.30

$VBOXMNG createvm --name "cs-systemvm" \
                  --ostype "Ubuntu_64" \
                  --groups "/cloudstack" \
                  --register
                 
$VBOXMNG storagectl cs-systemvm \
                  --name "ctl0" \
                  --add sata 

$VBOXMNG storageattach cs-systemvm \
                  --storagectl "ctl0" \
                  --port 0 \
                  --type hdd \
                  --medium /Users/hugo/VirtualBox\ VMs/templates/systemvm64template-vpc-toolkit-hugo-xen.vhd \
                  --mtype multiattach

$VBOXMNG storageattach cs-systemvm \
                  --storagectl ctl0 \
                  --port 1 \
                  --type dvddrive \
                  --medium /Users/hugo/VirtualBox\ VMs/templates/systemvm.iso

$VBOXMNG modifyvm cs-systemvm \
                  --nic1 hostonly \
                  --hostonlyadapter1 "vboxnet0" \
                  --memory 256

$VBOXMNG setextradata cs-systemvm \
                  "VBoxInternal/Devices/pcbios/0/Config/DmiOEMVBoxRev" "cmdline:console=hvc0 vpccidr=172.16.0.0/16 domain=devcloud.local dns1=8.8.8.8 dns2=8.8.8.4 template=domP name=r-8-VM eth0ip=$ROUTERIP eth0mask=255.255.255.0 type=vpcrouter disable_rp_filter=true"

$VBOXMNG startvm cs-systemvm

while ! ssh -p 3922 -o ConnectTimeout=2 root@${ROUTERIP} /opt/cloud/bin/get_template_version.sh | grep -q -v CloudStack ; do
  sleep 3
done

echo executing get_template_version.sh
ssh -p 3922 root@${ROUTERIP} /opt/cloud/bin/get_template_version.sh

$VBOXMNG controlvm cs-systemvm poweroff

sleep 2 

$VBOXMNG unregistervm cs-systemvm --delete
