# coding=utf-8
__author__ = "Gareth Coles"

"""
Various utilities for use with the Teamspeak protocol.
This file could change as the ServerQuery spec is updated.
"""


def unescape(instr):
    instr = str(instr)
    instr = instr.replace("\\s", " ")
    instr = instr.replace("\\n", "\n")
    instr = instr.replace("\\r", "\r")
    instr = instr.replace("\\t", "\t")
    instr = instr.replace("\\p", "|")
    instr = instr.replace("\\a", "\7")
    instr = instr.replace("\\b", "\8")
    instr = instr.replace("\\f", "\12")
    instr = instr.replace("\\v", "\11")
    instr = instr.replace("\\/", "/")
    instr = instr.replace("\\\\", "\\")
    return instr


def escape(instr):
    instr = str(instr)
    instr = instr.replace("\\", "\\\\")
    instr = instr.replace(" ", "\\s")
    instr = instr.replace("\n", "\\n")
    instr = instr.replace("\r", "\\r")
    instr = instr.replace("\t", "\\t")
    instr = instr.replace("|", "\\p")
    instr = instr.replace("\7", "\\a")
    instr = instr.replace("\8", "\\b")
    instr = instr.replace("\12", "\\f")
    instr = instr.replace("\11", "\\v")
    instr = instr.replace("/", "\\/")
    return instr
