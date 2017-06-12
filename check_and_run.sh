#!/bin/bash：
#---------------------
#这个脚本先foreach scp拷贝到所有服务器，然后foreach ssh来运行
#参数
#1).NAME：要运行的jar包名称
#后续改进： 来加上列表，可以遍历jar包名然后检查进程运行
#处理逻辑：
#获取要运行的jar包的名字，截取到第一个-之前的字符串，然后ps -ef查找看服务存在不？如果存在且大于1个则只保留一个，不存在则启动，
#
NAME=$1
echo $NAME
shortname=${NAME%%-*}
extension=${NAME##*.}
manipulate="java -jar "
if [ $extension = "py" ];then
    manipulate="python3 "
fi
echo "shortname is $shortname"
runcount=`ps -ef |grep -E "java|python"|grep -v grep|grep -v sh|wc -l`
if [ $runcount -lt 10 ];then
  count=`ps -ef |grep -E "java|python"| grep $shortname|grep -v grep|grep -v sh|wc -l`
  echo "there is $count $shortname process"
  if [ $count -gt 1 ];then
    pid=`ps -ef |grep -E "java|python"|grep $shortname|grep -v "grep"|awk 'NR>1{print $2}'`
    echo "killed $pid"
    kill -9 $pid
  elif [ $count -eq 1 ];then
      echo "Only 1 $shortname process is running,"
  else
      echo "$NAME process is not running,execute nohup $manipulate $NAME > log/${shortname}.log &"
      cd ~/jar
      if [ ! -d "log" ]; then
        mkdir log
      fi
      `nohup $manipulate  $NAME > log/${shortname}.log &`
      ps -ef |grep -E 'java|python'
  fi
else
    echo "there is already more than 10 process running! Please don't run more!!!"
fi
