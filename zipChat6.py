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

    def getConnectionPortRange(self):
        config = configparser.ConfigParser()
        config.read(self.confFile)
        low = config['GP_PORTS']['low'] 
        high = config['GP_PORTS']['high'] 
        return low, high
        
configureData = zipChat6.configData()

#
#   Base server class. 
#   Defaults to the UDP protocol and port 10008 unless otherwise specified
#
class zServer:
    def __init__(self,proto="UDP"):
        self.port = configureData.getConnectionOut()
        self.protocol = proto
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
 
        if len(addrs) == 0:
            raise Exception("there is no IPv6 address configured for localhost")
 
        me=ni.ifaddresses(configureData.getInterface())[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
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
    def Send(self,destination,data,port=None):
        if port == None:
            port = self.port
        #Check for different port than the config file
        if port != self.port:
            destination = list(destination)
            destination[1] = port
            destination = tuple(destination)

        try:
            if self.protocol == "TCP":
                self.__sendTcp(destination,port,data)
            elif self.protocol == "UDP":
                s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                s.sendto(data,destination)
            else:
                raise Exception("Protocol not supported")
        except Exception as e:
            print("ServerSendError: ", e)

    def __sendTcp(self, destination, port, data):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.bind(self.getIP6Addr())
            s.listen(1) #Listen for a connection
            c, addr = s.accept()    #Accept the connection. returns its address and the connection object
            c.send(data)        #Since we've handshake'd we can send the data
            c.close()   #close it out when its done
        except Exception as e:
            print("TCPSendError: ", e)

#
#   Base client class
#   Defaults to UDP protocol
#
class zClient:
    def __init__(self, proto="UDP"):
        self.protocol = proto
        self.port = configureData.getConnectionIn()
        if not socket.has_ipv6:
            raise Exception("The local machine has no IPv6 support enabled")
        me=ni.ifaddresses(configureData.getInterface())[10][0]['addr']
        addrs = socket.getaddrinfo("localhost", self.port, socket.AF_INET6, 0, socket.SOL_TCP)
        tup = addrs[0]
        tup = tup[-1]
        tup = list(tup)
        tup[0] = me
        tup = tuple(tup)
        self.addr = tup
    
    #UDP listener. 
    def listen(self,address=None,port = None):
        if port == None:
            port = self.port
        if address == None:
            address = self.addr
        if port != self.port:
            address = list(address)
            address[1] = port
            address = tuple(address)

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
            print("ClientListenError: ", e)
    
    def __listenTcp(self, address, port):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.connect(address)
            output = s.recv(4096)
            s.close()
            return output
        except Exception as e:
            print("TCPClientListenError: ", e)


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
            print("HeartbeatPacketBuilderError: ", e);

    #Loops through `ipList` and sends out the built packet to each IP in the list
    def __broadcast(self,data,iplist,s):
        try:
            print("Sending beat...")
            for ip in iplist:
                packet = numpy.array(data)
                s.sendto(packet.tostring(),ip)

        except Exception as e:
            print("HeartbeatBroadcastError: ", e)

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
            print("HeartbeatListenError: ", e)

    #Starts the client on a seperate thread
    def start(self):
        port = int(self.port)
        t = threading.Thread(target=self.getBeat,args=(port,))
        t.start()

#
#   Start the ConnectionListener when the heartbeat server/client is started. This
#   Listens for incoming connections (I.E. Conversations)
#
class ConnectionListener:
    def __init__(self):
        self.port = configureData.getConnectionIn()
        self.client = zClient()
        self.UDPserver = zServer()
        self.outPort = configureData.getConnectionOut()
        self.inPort = configureData.getConnectionIn()
        self.lowPort, self.highPort = configureData.getConnectionPortRange()
        self.usedPorts = []
        self.usedPorts.append(self.outPort)
        self.usedPorts.append(self.inPort)
        self.usedPorts.append(self.lowPort)

    def start(self):
        port = int(self.port)
        t = threading.Thread(target=self.__listen,args=(port,))
        t.start()

    def getFreePort(self):
        try:
            lastPort = int(self.usedPorts[-1])
            if (lastPort + 1) > int(self.highPort):
                raise Exception("No Availible Ports!")
                return None
            else:
                self.usedPorts.append((lastPort + 1))
                return self.usedPorts[-1]
        except Exception as e:
            print("ConnectionPortError: ", e)

    def __launchConnection(self,data,address):
        data = data.decode()
        data = data.split(' ')
        name = data[1]
        if data[0] == "CR":
            print(data," from ", address)
            addrlist = list(address)
            addr = addrlist[0]
            print(addr)
            time.sleep(0.2)
            self.UDPserver.Send((addr,int(self.outPort)),("ACK " + str(self.getFreePort())).encode())
            #self.UDPserver.Send((addr,int(self.outPort)),int(self.outPort), ("ACK "+ str(self.getFreePort())).encode())
            #Do TCP stuff. Start TCP listener and server



    def __listen(self,port):
        try:
            while True:
                data, address = self.client.listen(port = port)
                self.__launchConnection(data, address)
        except Exception as e:
            print("ConnectionListenerError: ", e)

#
#   This is what initiates and carries on the connection/converstaion
#
class Connection:
    def __init__(self,name):
        self.name = name
        self.UDPserver = zServer()
        self.UDPclient = zClient()
        self.TCPserver = zServer("TCP")
        self.TCPclient = zClient("TCP")
        self.outPort = int(configureData.getConnectionOut())
        self.inPort = int(configureData.getConnectionIn())
        self.lowPort, self.highPort = configureData.getConnectionPortRange()
        self.usedPorts = []
        self.usedPorts.append(self.outPort)
        self.usedPorts.append(self.inPort)
        self.usedPorts.append(self.lowPort)

    def getFreePort(self):
        try:
            lastPort = int(self.usedPorts[-1])
            if (lastPort + 1) > int(self.highPort):
                raise Exception("No Availible Ports!")
                return None
            else:
                self.usedPorts.append((lastPort + 1))
                return self.usedPorts[-1]
        except Exception as e:
            print("ConnectionPortError: ", e)

        
        
    def connect(self, isResponse=False):
        ipToConnectTo = configureData.getIPFromName(self.name)
        #self.UDPserver.Send((ipToConnectTo,int(self.inPort)),int(self.inPort), ("CR "+ str(self.getFreePort())).encode())
        self.UDPserver.Send((ipToConnectTo,int(self.inPort)), ("CR " + str(self.getFreePort())).encode())
        data, address = self.UDPclient.listen(port = self.outPort)   #Wait for ack from connectionListener. ConnectionListener will send free port
        data = data.decode()
        data = data.split(' ')
        print(data, "From", address)

        #
        #   TODO:   NOW THAT ACK AND CR IS SOMEWHAT IMPLEMENTED, YOU NEED TO TAKE A BREAK FROM THIS AND MAKE SURE ALL PORTS ARE LINED
        #   UP CORRECTLY. 
        #   
        #
        #   Peer1                   Peer2
        #
        # out     |==============>| in
        # in      |<==============| out
        # UDPout  |==============>| UDPin 
        # UDPin   |<==============| UDPout
        #




        #   
        #   To establist a connection with a peer:
        #
        #   UDP:out |[CR (port)] ===========>| UDP:in
        #   UDP:in  |<===========[ACK (port)]| UDP:out
        #           |                        | 
        #           | Once recieve port numb-|
        #           | ers are exchanged,     |
        #           | Connection moves to TCP|
        #           | and to ports > 20001   |
        #           |                        |
        #   TCP:out |=======================>| TCP:in
        #   TCP:in  |<=======================| TCP:out
        #
