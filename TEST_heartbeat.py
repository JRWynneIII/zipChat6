#!/usr/bin/env python
import zipChat6
import threading
import socket
import time
import netifaces as ni

def getAddr():
        me=ni.ifaddresses('tun0')[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", 10009, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        return tup

hbServ = zipChat6.heartbeatServer()
hbClient = zipChat6.heartbeatClient()
addressServ = zipChat6.zServer()
ipList = []
ipList.append(getAddr())
hbClient.start(10009)
hbServ.start(10009,ipList)
