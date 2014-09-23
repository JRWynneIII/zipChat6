#!/usr/bin/env python

import threading
import socket
import time
import hashlib

class zServer:
    def __init__(self):
        self.port=10008
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")
 
        entry0 = addrs[0]
        self.fullAddr = entry0
        self.sockaddr = entry0[-1]
    
    def getIP6Addr(self):
        return self.sockaddr
    
    def getAddress(self):
        return self.fullAddr

    def Send(self,data):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.bind(self.sockaddr)
            s.listen(1) #The number refers to how many connections are kept "busy" until they're outright refused
            c, addr = s.accept() #Found a connection! accept it
            c.send(data)
            c.close() #Close the connection
        except Exception as e:
            print("Error: ", e)
        
        

class zClient:
    def __init__(self, toAddress):
        self.remote = toAddress
        self.port = 10008
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")

    def listen(self):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.connect(self.remote)
            output = s.recv(4096)    #recv buffer is 4096. No idea if its bytes, kbytes or what. docs didn't specify
            s.close()
            return output
        except Exception as e:
            print("Error: ", e)


class heartBeatServer:
    def __init__(self):
        self.port = 10008

    #This is the only function that needs to be called
    def start(self,port,ipList):
        t = threading.Thread(target=toThread, args=(port,ipList))
        t.daemon = True
        t.start()

    #All these methods need to be private but i don't know how
    def toThread(self,port,ipList)
        while 1:
            serv = zServer()
            data = build_heartbeat_packet()
            broadcast(data,ipList)
            time.sleep(10)

    def build_heartbeat_packet(serv):
        packet = []
        packet[0] = serv.getAddress()
        #Put more info for the packet here
        packet[-1] = hashlib.sha224(packet).hexdigest()
        return packet

    def broadcast(self,data,iplist):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            for ip in iplist:
                s.listen(1)
                connection, remoteAddress = s.accept()
                if ip == remoteAddress:
                    connection.send(data)
                else:
                    connection.send("") #SET HEARTBEAT CLIENT TO RETRY IF IT GETS EMPTY DATA PACKET

        except Exception as e:
            print("Error: ", e)
            
class heartBeatClient:
    def __init__(self):
        self.port = 10008
    
    #This is the only function that needs to be public/called
    def start(self,port,ipList):
        t = threading.Thread(target=clientThread,args=(port, ipList))
        t.daemon = True
        t.start()

    #Again this function should be private buT I DONT 'KNOW HOW IN PYTHON
    def clientThread(self,port,ipList):
        while 1:
            for ip in ipList:
                successful = False
                count = 0
                while not successful:
                    count += 1
                    client = zClient(ip)
                    output = client.listen()
                    if output != "":
                        successful = True
                    else:
                        successful = False
                    #try to get a successful connection 100 times else timeout
                    if count > 100:
                        break
            time.sleep(10)

