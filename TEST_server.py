#!/usr/bin/env python

import zipChat6
import time

serv = zipChat6udp.zServer()
serv.Send(serv.getIP6Addr(),10008,"HeeeEEEElllOOOOO".encode())
time.sleep(5)
