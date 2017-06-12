#!/bin/bash
list_file=$1
behavior=$2
file=$3
echo "behavior is $behavior"
cat $list_file | while read line
do
  host_ip=`echo $line | awk '{print $1}'`
  echo "$host_ip"
  if [ $behavior = "scp" ];then
    echo "scp copy file"
    expect scp.exp $host_ip $file
  elif [ $behavior = "ssh" ];then
    echo "ssh execute command expect  ssh_send_check_and_run_jar.exp $host_ip $file "
    expect  ssh_send_check_and_run_jar.exp $host_ip $file
  elif [ $behavior = "sshwar" ];then
    expect  ssh_send_check_and_run_war.exp $host_ip $file
  elif [ $behavior = "py" ];then 
    expect python.exp $host_ip $file
  elif [ $behavior = "kill" ];then 
    expect  kill_processid.exp $host_ip $file  
  elif [ $behavior = "check" ];then 
    expect  check_run_count.exp $host_ip
  elif [ $behavior = "restart" ];then
    expect  restart.exp $host_ip
  elif [ $behavior = "userdefine" ];then
    expect  userdefine.exp $host_ip
  elif [ $behavior = "pip" ];then
    expect  pip3install.exp $host_ip
  elif [ $behavior = "duh" ];then
    expect  duh.exp $host_ip
  elif [ $behavior = "pillow" ];then
    expect  pillow.exp $host_ip
  elif [ $behavior = "dellog" ];then
    expect  dellog.exp $host_ip
  elif [ $behavior = "aptgetins" ];then
    expect  aptgetpil.exp $host_ip
  elif [ $behavior = "apttes-orc" ];then
    expect  apttes-orc.exp $host_ip
  elif [ $behavior = "free" ];then
    expect  free.exp $host_ip
  elif [ $behavior = "mkdir" ];then
    expect  mkdir.exp $host_ip
  elif [ $behavior = "etchost" ];then
    expect  etchost.exp $host_ip
  elif [ $behavior = "rmjar" ];then
    expect  rmjar.exp $host_ip
  elif [ $behavior = "ssh1" ];then
    expect  ssh_send_check_and_run_jar1.exp $host_ip
  else
    expect apt_get_install.exp $host_ip
  fi  
done
