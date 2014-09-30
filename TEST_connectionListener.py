#!/usr/bin/env python3

import zipChat6
import threading
import time

listener = zipChat6.ConnectionListener()
server = zipChat6.zServer(10012)
listener.start()
time.sleep(2)
con = zipChat6.Connection("jake")
while True:
    print("connecting")
    con.connect()
    time.sleep(5)

