# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     MakeBOUND.csv
# Source Name:   MakeBOUND.csv.py
# Min Version:   ArcGIS 9.2
# Max Version:   ArcGIS 9.3
# Required Argumuments: - An existing planning unit shapefile
# Requirements:         - An existing planning unit shapefile, ArcInfo Workstation installation
# Description:  
# Usage: 
# ----------------------------------------------------------------------------------------------------------------

import csv, arcgisscripting, sys, os, traceback, random, math

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def AddMsgAndPrint(message):
    gp.AddMessage(message)
    print message
    return 0

def GetBaseName(inFileName, theExtension):
    if len(inFileName.split("\\")) > len(inFileName.split("/")):
        inlist = inFileName.split("\\")
    else:
        inlist = inFileName.split("/")
    final_Name = inlist[len(inlist) - 1]
    # Sanitize extension, in case user left it off, i.e. typed directly with no extension
    final_Name2 = final_Name.replace(theExtension,"")
    #final_Name = final_Name2 + theExtension
    return final_Name

def GetPath(inFileName):
    print inFileName
    print len(inFileName.split("\\"))
    print len(inFileName.split("/"))
    if len(inFileName.split("\\")) > len(inFileName.split("/")):
        inlist = inFileName.split("\\")
    else:
        inlist = inFileName.split("/")

    print inlist
    del inlist[len(inlist) - 1]
    path = "\\".join(inlist)
    return path    

# -------------------------------------------
# BEGIN
# -------------------------------------------
# Create the Geoprocessor object
gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    pufile = sys.argv[1]
    puField = sys.argv[2]
    outbnd = sys.argv[3]    
    #outspp = sys.argv[4]

    scratchworkspace = GetPath(Final_Pus)

    outFile = open(outbnd,'wb')

    # set vars for aml
    ## TO DO
    sFN = scratchworkspace + os.sep + ??
    sFN.stripfile

    aFN = (av.GetProject.GetWorkDir.GetName + "\bound.aml").AsFileName

    covFN = av.GetProject.GetWorkDir.MakeTmp("pu","")
    covFN2 = av.GetProject.GetWorkDir.MakeTmp("pus","")
    typeID = "TYPE" + Date.Now.GetHours.AsString + Date.Now.GetMinutes.AsString + Date.Now.GetSeconds.AsString

    tFN = (av.GetProject.GetWorkDir.GetName + "\tmp.txt").AsFileName
    tFile = LineFile.Make(tFN,#FILE_PERM_WRITE)
    tFile.WriteElt("id1,id2,boundary")
    tFile.Flush
    tFile.Close

    covFN = scratchworkspace + os.sep + "pu"
    covFN2 = scratchworkspace + os.sep + "pu2"
    typeID = "TYPE" + str(int(time.time() * 10))

    # Write the aml
    outFile.write("/* $Id: mk_bnd.aml,v 1.3 2003/12/15 01:59:06 uqwroche Exp $")
    outFile.write("/*")
    outFile.write("/* Calculate MARXAN boundary data.")
    outFile.write("/*")
    outFile.write("/* Created: 2002-09-12")
    outFile.write("/* Author: Wayne A. Rochester")
    outFile.write("/*")
    outFile.write("/* AML entry")
    outFile.write("")
    outFile.write("/* &args pucov pufld")
    outFile.write(("&setvar pucov = ") + (covFN2)) 
    outFile.write(("&setvar pufld = ") + (puField))
    outFile.write("")
    outFile.write("&if %:program% <> ARC &then")
    outFile.write("  &return &warning Get into ARC.")
    outFile.write("")
    outFile.write(("SHAPEARC ") + puFN + (" ") + covFN + (" ") + typeID) 
    outFile.write(("CLEAN ") + covFN + (" # .001 .001 poly"))
    outFile.write(("REGIONPOLY ") + covFN + (" ") + covFN2 + (" ") + typeID + (" ") + typeID + (".SAFE"))
    outFile.write("")
    outFile.write("&if [null %pufld%] &then")
    outFile.write("  &return &warning USAGE: [entryname %aml$file% -noext] ~")
    outFile.write("<pu-cover> <pu-code-field>")
    outFile.write("")
    outFile.write("/* Arc attribute table generation")
    outFile.write("&setvar tmpcov = [scratchname -directory]")
    outFile.write("copy %pucov% %tmpcov%")
    outFile.write("build %tmpcov% arc")
    outFile.write("")
    outFile.write("/* Boundary data extraction")
    outFile.write("")
    outFile.write("&setvar tmptab = [scratchname -info]")
    outFile.write("")
    outFile.write("pullitems %tmpcov%.aat %tmptab% lpoly# rpoly# length")
    outFile.write("")
    outFile.write("tables")
    outFile.write("additem %tmptab% pu_code1 4 9 b # rpoly#")
    outFile.write("additem %tmptab% pu_code2 4 9 b # pu_code1")
    outFile.write("")
    outFile.write("select %tmptab%")
    outFile.write("alter length,arc_len,9,f,0,,")
    outFile.write("")
    outFile.write("relate add")
    outFile.write("rochl")
    outFile.write("%tmpcov%.pat")
    outFile.write("info")
    outFile.write("lpoly#")
    outFile.write("%tmpcov%#")
    outFile.write("ordered")
    outFile.write("ro")
    outFile.write("~")
    outFile.write("")
    outFile.write("relate add")
    outFile.write("rochr")
    outFile.write("%tmpcov%.pat")
    outFile.write("info")
    outFile.write("rpoly#")
    outFile.write("%tmpcov%#")
    outFile.write("ordered")
    outFile.write("ro")
    outFile.write("~")
    outFile.write("")
    outFile.write("reselect rochl//%pufld% <= rochr//%pufld%")
    outFile.write("calculate pu_code1 = rochl//%pufld%")
    outFile.write("calculate pu_code2 = rochr//%pufld%")
    outFile.write("nselect")
    outFile.write("calculate pu_code1 = rochr//%pufld%")
    outFile.write("calculate pu_code2 = rochl//%pufld%")
    outFile.write("")
    outFile.write("relate drop")
    outFile.write("rochl")
    outFile.write("rochr")
    outFile.write("~")
    outFile.write("")
    outFile.write("quit")
    outFile.write("")
    outFile.write("kill %tmpcov%")
    outFile.write("")
    outFile.write("&if [exists bnd.dat -info] &then")
    outFile.write("  killinfo bnd.dat")
    outFile.write("")
    outFile.write("frequency %tmptab% bnd.dat")
    outFile.write("pu_code1")
    outFile.write("pu_code2")
    outFile.write("end")
    outFile.write("arc_len")
    outFile.write("end")
    outFile.write("")
    outFile.write("killinfo %tmptab%")
    outFile.write("")
    outFile.write("tables")
    outFile.write("dropitem bnd.dat case# frequency")
    outFile.write("select bnd.dat")
    outFile.write("alter arc_len,bnd_len,9,,0,,")
    outFile.write("reselect pu_code1 = 0")
    outFile.write("calculate pu_code1 = pu_code2")
    outFile.write("quit")
    outFile.write(" ")
    outFile.write("tables")
    outFile.write("select bnd.dat")
    outFile.write(("unload ") + (sFN.GetName) + ("\bndtmp.csv delimited init"))
    outFile.write("quit")
    outFile.write(("&system copy /Y ") + (tFN.GetName) + (" + ") + (sFN.GetName) + ("\bndtmp.csv") + (" ") + (bFN.GetName))
    outFile.write("kill %pucov% all")
    outFile.write(("kill ") + (covFN.GetName) + (" all"))
    outFile.write("&return")

    outFile.Flush
    outFile.Close
    outFile = nil
