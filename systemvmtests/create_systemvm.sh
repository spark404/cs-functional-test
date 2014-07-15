#!/bin/bash

VBOXMNG="/usr/bin/VBoxManage"

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
                  --medium /Users/hugo/VirtualBox\ VMs/templates/systemvm64template-unknown-xen-vpctoolkit.vhd \
                  --mtype multiattach

$VBOXMNG storageattach cs-systemvm \
                  --storagectl ctl0 \
                  --port 1 \
                  --type dvddrive \
                  --medium /Users/hugo/VirtualBox\ VMs/templates/systemvm.iso

$VBOXMNG modifyvm cs-systemvm \
                  --nic1 hostonly \
                  --hostonlyadapter1 "vboxnet0"

$VBOXMNG setextradata cs-systemvm \
                  "VBoxInternal/Devices/pcbios/0/Config/DmiOEMVBoxRev" "cmdline:console=hvc0 vpccidr=172.16.0.0/16 domain=devcloud.local dns1=8.8.8.8 dns2=8.8.8.4 template=domP name=r-8-VM eth0ip=192.168.56.30 eth0mask=255.255.255.0 type=vpcrouter disable_rp_filter=true"
