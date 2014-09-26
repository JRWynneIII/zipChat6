#!/usr/bin/env python

import threading
import socket
import time
import hashlib
import netifaces as ni
import numpy

class zServer:
    def __init__(self,port=10008,proto="UDP"):
        self.port = port
        self.protocol = proto
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")
 
        me=ni.ifaddresses('tun0')[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", 10009, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        self.addrTup = tup

    def getIP6Addr(self):
        return self.addrTup

    def Send(self,destination,port,data):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.sendto(data,destination)
        except Exception as e:
            print("Error: ", e)

class zClient:
    def __init__(self):
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
    
    def listen(self,address,port):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.bind(address)
            while True:
                data, recvFrom = s.recvfrom(1024)
                return data, recvFrom
        except Exception as e:
            print("Error: ", e)


class heartbeatServer:
    def __init__(self):
        self.port = 10009
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")
    
    def getAddr(self):
        me=ni.ifaddresses('tun0')[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", 10009, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        return tup

    def start(self,port,ipList):
        t = threading.Thread(target=self.beat, args=(port,ipList,))
        t.start()

    def build_heartbeat_packet(self,serv):
        try:
            packet = []
            packet.append(serv.getIP6Addr())
            tmp = list(packet[0])
            packet[0] = tmp[0]
            #Put more info for the packet here
            return packet
        except Exception as e:
            print("Error: ", e);

    #CHANGE TO UDP
    def broadcast(self,data,iplist):
        try:
            print("Sending beat...")
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            for ip in iplist:
                packet = numpy.array(data)
                s.sendto(packet.tostring(),ip)

        except Exception as e:
            print("Error: ", e)

    def beat(self,port,ipList):
        while True:
            serv = zServer()
            #dat = "1.2.3.4".encode()
            dat = self.build_heartbeat_packet(serv)
            self.broadcast(dat,ipList)
            time.sleep(5)         #Wait 2 minutes until next beat




class heartbeatClient:
    def __init__(self):
        self.port = 10009
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")
        
    def getAddr(self):
        me=ni.ifaddresses('tun0')[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        return tup

    def updateHeartbeat(self, data, address):
        print("Heartbeat recieved from: ", address, data.decode())

    def getBeat(self, port):
        try:
            while True:
                print("Listening")
                client = zClient()
                #print("Heartbeat recieved from: ", addr, output.decode())
                output, addr = client.listen(self.getAddr(),10009)
                self.updateHeartbeat(output, addr)
        except Exception as e:
            print("Error: ", e)

    def start(self,port):
        t = threading.Thread(target=self.getBeat,args=(port,))
        t.start()

