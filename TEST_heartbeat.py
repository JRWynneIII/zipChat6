#!/usr/bin/env python3
import zipChat6
import threading
import socket
import time
import netifaces as ni

hbServ = zipChat6.heartbeatServer()
hbClient = zipChat6.heartbeatClient()
addressServ = zipChat6.zServer()
ipList = []
ipList.append(("fc71:9ec4:384e:85e2:dffb:307:3e8e:a3b8",10010))
hbClient.start()
hbServ.start(ipList)
