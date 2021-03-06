#!/usr/bin/env python3

import threading
import socket
import time
import hashlib
import netifaces as ni
import numpy
import configparser
import zipChat6

#
#   Class's methods to return data from zc.conf
#   
class configData:
    def __init__(self, confFile="zc.conf"):
        self.confFile = confFile

    def getInterface(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        return config['INTERFACE']['interface']

    def getHeartbeatOutPort(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        return config['UDP']['heartbeat_out']

    def getHeartbeatInPort(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        return config['UDP']['heartbeat_in']

    def getKnownIPList(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        ipList = config['KNOWN_IP']['ips'].split(',')
        return ipList

    def getIPFromName(self,name):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        return config['NAME_IP'][name]

    def getNameFromIP(self,IP):
        try:
            config = configparser.ConfigParser()
            config.read(self.confFile)
            nameList = config['NAME_IP']
            for name in nameList:
                if nameList[name] == IP:
                    return name
            raise Exception("IP not found!")
        except Exception as e:
            print("Error: ", e)

    def getConnectionOut(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        return config['TCP']['connection_out']

    def getConnectionIn(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        return config['TCP']['connection_in']
        
configureData = zipChat6.configData()

#
#   Base server class. 
#   Defaults to the UDP protocol and port 10008 unless otherwise specified
#
class zServer:
    def __init__(self,port=10008,proto="UDP"):
        self.port = port
        self.protocol = proto
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")
 
        me=ni.ifaddresses(configureData.getInterface())[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", port, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        self.addrTup = tup
    
    #Returns the IPv6 Address that was found when the constructor (__init__) was run
    def getIP6Addr(self):
        return self.addrTup

    #Sends `data` to the specified port and address (destination); UDP
    def Send(self,destination,port,data):
        try:
            if self.protocol == "TCP":
                self.__sendTcp(destination,port,data)
            elif self.protocol == "UDP":
                s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                s.sendto(data,destination)
            else:
                raise Exception("Protocol not supported")
        except Exception as e:
            print("Error: ", e)

    def __sendTcp(self, destination, port, data):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.bind(self.getIP6Addr())
            s.listen(1) #Listen for a connection
            c, addr = s.accept()    #Accept the connection. returns its address and the connection object
            c.send(data)        #Since we've handshake'd we can send the data
            c.close()   #close it out when its done
        except Exception as e:
            print("Error: ", e)

#
#   Base client class
#   Defaults to UDP protocol
#
class zClient:
    def __init__(self, proto="UDP"):
        self.protocol = proto
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
    
    #UDP listener. 
    def listen(self,address,port):
        try:
            if self.protocol == "TCP":
                return self.__listenTcp(address,port)
            elif self.protocol == "UDP":
                s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                s.bind(address)
                while True:
                    data, recvFrom = s.recvfrom(1024)
                    return data, recvFrom
            else:
                raise Exception("Protocol not supported")
        except Exception as e:
            print("Error: ", e)
    
    def __listenTcp(self, address, port):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.connect(address)
            output = s.recv(4096)
            s.close()
            return output
        except Exception as e:
            print("Error: ", e)


#
#   Heartbeat Server will send out a "i'm alive/online" signal every 2 minutes. 
#   The data sent can include things like status messages and should end in a checksum 
#   of the "packet". Checksum not yet implemented.
#   Heartbeat is sent out on port 10009
#
class heartbeatServer:
    def __init__(self):
        self.port = configureData.getHeartbeatOutPort()
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")

    #Gets the IPv6 address of the 'tun0' (CJDNS) device
    def __getAddr(self):
        me=ni.ifaddresses(configureData.getInterface())[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", 10009, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        return tup

    #Starts the heartbeat on a seperate thread. Will send out heartbeat packet to every IP in `ipList`
    def start(self,ipList):
        port = int(self.port)
        t = threading.Thread(target=self.__beat, args=(port,ipList,))
        t.start()

    #Builds the heartbeat packet to be sent
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

    #Loops through `ipList` and sends out the built packet to each IP in the list
    def __broadcast(self,data,iplist,s):
        try:
            print("Sending beat...")
            for ip in iplist:
                packet = numpy.array(data)
                s.sendto(packet.tostring(),ip)

        except Exception as e:
            print("Error: ", e)

    #Encapsulates the "beat". Initializes the zServer, builds the packet, broadcasts it, then waits 2 minutes until next iteration. 
    def __beat(self,port,ipList):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        while True:
            serv = zServer()
            dat = self.build_heartbeat_packet(serv)
            self.__broadcast(dat,ipList,s)
            time.sleep(5)         #Wait 2 minutes until next beat

#
#   The heartbeat client.
#   Recieves the heartbeat and launches the method that deals with the recieved data
#
class heartbeatClient:
    def __init__(self):
        self.port = configureData.getHeartbeatInPort()
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")

    #Gets the IPv6 address of the CJDNS device        
    def __getAddr(self):
        me=ni.ifaddresses(configureData.getInterface())[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        return tup
    
    #Function that gets called when a "beat" is recieved
    def __updateHeartbeat(self, data, address):
        addressList = list(address)
        addr = addressList[0]
        sender = configureData.getNameFromIP(addr)
        if sender == None:
            sender == address
        print("Heartbeat recieved from: ", sender)

    #Listens for the heartbeat
    def getBeat(self, port):
        try:
            while True:
                print("Listening")
                client = zClient()
                output, addr = client.listen(('',port),port)
                self.__updateHeartbeat(output, addr)
        except Exception as e:
            print("Error: ", e)

    #Starts the client on a seperate thread
    def start(self):
        port = int(self.port)
        t = threading.Thread(target=self.getBeat,args=(port,))
        t.start()

class ConnectionListener:
    def __init__(self):
        self.port = configureData.getConnectionIn()
        self.client = zClient()

    def start(self):
        port = int(self.port)
        t = threading.Thread(target=self.__listen,args=(port,))
        t.start()

    def __launchConnection(self,data,address):
        print(data.decode()," from ", address)

    def __listen(self,port):
        data, address = self.client.listen(('',port),port)
        self.__launchConnection(data, address)

class Connection:
    def __init__(self,name):
        self.name = name
        self.server = zServer(configureData.getConnectionOut(),"TCP")
        
