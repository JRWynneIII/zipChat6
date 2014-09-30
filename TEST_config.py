#!/usr/bin/env python3

import zipChat6

config = zipChat6.configData()

print(config.getInterface())
print(config.getHeartbeatOutPort())
print(config.getHeartbeatInPort())
print(config.getKnownIPList())
IP = config.getIPFromName('Jake')
print(IP)
print(config.getIPFromName('jakeVPS'))
print(config.getNameFromIP(IP))
