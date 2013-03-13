# ----------------------------------------------------------------------------------------------------------------
# Tool Name:
# Source Name:
# Min Version:
# Max Version:
# Required Argumuments: -
# Requirements:         -
# Description:
# Usage:
# ----------------------------------------------------------------------------------------------------------------

import csv, arcgisscripting, sys, os, traceback, random, math, string

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

def GetScratchFromFeatureClass(catalogPath):
    # Get scratch workspace from input dirs
    if len(inCatalogPath.split("\\")) > len(inCatalogPath.split("/")):
        dirlist = inCatalogPath.split("\\")
    else:
        dirlist = inCatalogPath.split("/")
    n = 0
    scratchwp = ""
    if dirlist[len(dirlist) - 1] == "polygon": # case coverage
        z = 2
    elif dirlist[len(dirlist) - 1] == "arc":
        z = 2
    else:
        z = 1 # case shapefile
    for dir in dirlist:
        # break one or two dir before last, if shape/cov
        if n + z == len(dirlist):
            break
        if n == 0: # start condition
            scratchwp = dir
        else:
            scratchwp = scratchwp + "\\" + dir
        n += 1
    return scratchwp

# -------------------------------------------
# BEGIN
# -------------------------------------------
# Create the Geoprocessor object

gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    # Get parameters from input
    PUs = sys.argv[1]
    Pu_field = sys.argv[2]
    Marxan_result = sys.argv[3]
    Marxan_field = sys.argv[4]
    Out_layer = sys.argv[5]

    # Setup
    # Get scratch workspace from input dirs
    desc = gp.describe(PUs)
    inCatalogPath = desc.CatalogPath
    scratchworkspace = GetScratchFromFeatureClass(inCatalogPath)

    # Join input table to PUs
    AddMsgAndPrint("Joining result to planning units...")

    # Make temp Layer to hold output
    #baseLyr = str(random.randint(1,100000)) + ".lyr"
    #TmpLyr = scratchworkspace + "\\" + baseLyr

    gp.MakeFeatureLayer_management(PUs, Out_layer)
    gp.AddJoin_management(Out_layer, Pu_field, Marxan_result, Marxan_field, "KEEP_COMMON")
    AddMsgAndPrint("...indexed and joined...")

    # Display result as new layer
    # IF Geoprocessing properties set "display results" this will add result to display by default
    AddMsgAndPrint("Results saved to output layer name you selected, and will be added to view according to your geoprocessing properties.")

except:
    # get the traceback object
    tb = sys.exc_info()[2]
    # tbinfo contains the line number that the code failed on and the code from that line
    tbinfo = traceback.format_tb(tb)[0]
    # concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
            str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
    # generate a message string for any geoprocessing tool errors
    msgs = "GP ERRORS:\n" + gp.GetMessages(2) + "\n"

    # return gp messages for use with a script tool
    gp.AddError(msgs)
    gp.AddError(pymsg)

    # print messages for use in Python/PythonWin
    print msgs
    print pymsg
