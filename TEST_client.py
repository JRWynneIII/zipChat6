#!/usr/bin/env python

import zipChat6
import time

serv = zipChat6udp.zServer()
c = zipChat6udp.zClient()
output, addr = c.listen(serv.getIP6Addr(),10008)
print(output.decode(), "From: ", addr)
