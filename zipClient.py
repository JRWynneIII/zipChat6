#!/usr/bin/env python

import sys

cmdList = []

def main():
    print("ZipChat6 -- Version 0.01")
    #enter command mode
    populateCommands()
    commandMode()

def commandMode():
    cmd = input(">> ")
    parseCmd(cmd)
    commandMode()


def parseCmd(cmd):
    for item in cmdList:
        if (cmd == item):
            possibles = globals().copy()
            possibles.update(locals())
            method = possibles.get(item)()

def populateCommands():
    cmdList.append("connect")
    cmdList.append("exit")
    cmdList.append("help")
    cmdList.append("disconnect")


def help():
    print("\nAvailible commands:")
    for item in cmdList:
        print(item)
    print("\n")

def exit():
    sys.exit()



main()
