#!/bin/bash
#---------------------
#这个脚本先foreach scp拷贝到所有服务器，然后foreach kill来运行
#参数
#1).NAME:匹配的进程名字
#后续改进： 来加上列表，可以遍历jar包名然后检查进程运行
#处理逻辑：
#获取要运行的jar包的名字，截取到第一个-之前的字符串，然后ps -ef查找看服务存在不？如果存在且大于1个则只保留一个，不存在则启动，
#
NAME=$1
echo $NAME
shortname=${NAME%%-*}
logfile=$shortname
echo "shortname is $shortname"
ps -ef |grep -E 'java|python'| grep $shortname|grep -v grep|grep -v sh
count=`ps -ef |grep -E 'java|python'| grep $shortname|grep -v grep|wc -l`
echo "there is $count $shortname process"
if [ $count -gt 0 ];then
    pid=`ps -ef |grep -E 'java|python'|grep $shortname|grep -v grep|awk '{print $2}'`
    echo "killed all $shortname id ：$pid"
    kill -9 $pid
else
    echo "$NAME process is not running."
fi

