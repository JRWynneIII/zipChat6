#!/usr/bin/env python

import threading
import socket
import time

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
