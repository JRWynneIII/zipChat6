#!/usr/bin/env python

import zipChat6
import time
serv = zipChat6.zServer()

serv.Send('HELLOOOOO'.encode())
time.sleep(5)
