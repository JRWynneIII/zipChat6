#!/usr/bin/env python

import zipChat6
import time
serv = zipChat6.zServer()
c = zipChat6.zClient(serv.getIP6Addr())
output = c.listen()
print(repr(output.decode()))
