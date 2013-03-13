# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     Assign Status
# Source Name:   AssignStatus.py
# Version:       Developed in ArcGIS 9.2 and tested in both 9.2 and 9.3
# Required Arguments:   - 
#                       - 
# Requirements:         - Projection must be defined. 
#                         
# Description:  
#
# Parameters:
#               1.
#               2.
#               3.
#               4.
# Usage: MakePUs: 
# TO DO:
# ----------------------------------------------------------------------------------------------------------------
# Import system modules
import sys, os, arcgisscripting, traceback, random

def FindField(Item,Table):
    # Return -1 if Item is not found within the table, otherwise return 0.
    iFoundFlg = -1
    fields = gp.ListFields(Table)
    try: #9.2
        fields.Reset()
        field = fields.Next()
        while field:
            AddMsgAndPrint("Field.name: " + field.Name.lower())
            AddMsgAndPrint("Item: " + Item.lower())            
            if field.Name.lower() == Item.lower():
                iFoundFlg = 0
                break 
            field = fields.next()
    except: #9.3
        for field in fields:
             if field.Name.lower() == Item.lower():
                iFoundFlg = 0
                continue            
    return field

def AddMsgAndPrint(message):
    gp.AddMessage(message)
    print message
    return 0

def GetBaseNameFromParameter(inFileName, theExtension):
    if len(inFileName.split("\\")) > len(inFileName.split("/")):
        inlist = inFileName.split("\\")
    else:
        inlist = inFileName.split("/")
    final_Name = inlist[len(inlist) - 1]
    # Sanitize extension, in case user left it off, i.e. typed directly with no extension
    final_Name2 = final_Name.replace(theExtension,"")
    final_Name = final_Name2 + theExtension
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

# ------------------------------------------------------------------------------------
# BEGIN
# ------------------------------------------------------------------------------------
# Create the Geoprocessor object
gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    Target_PUs = sys.argv[1]
    Overlay_status = sys.argv[2]
    Status_value = sys.argv[3][0]
    bool_clear = sys.argv[4]
    bool_del = sys.argv[5]

    covs = []
    covs.append(Overlay_status)
    covs.append(Target_PUs)
    x = 1

    # Spatial reference checks...    
    for cov in covs:
        desc = gp.describe(cov)
        dft = desc.ShapeType
        dft2 = dft.lower()
        # Check if polygon ...
        if dft2 != "polygon":
            gp.AddError("ERROR: Input and overlay feature classes must be of type polygon. Select a polygon shapefile or coverage and try again.")
            sys.exit("ERROR: Input and overlay feature classes must be of type polygon. Select a polygon shapefile or coverage and try again.")

        # Check if input is projected and bail if undefined...
        ggSR = "false"
        aSR = desc.SpatialReference
        if aSR.Name == "Unknown":
            gp.AddError("ERROR: You must define a spatial reference for the input and overlay shapefile. Define projection and try again.")
            sys.exit("ERROR: You must define a spatial reference for the input and overlay shapefile. Define projection and try again.")
        elif aSR.Name[:3] == "GCS":
            ggSR = "true"
        elif aSR.Type == "Geographic":
            ggSR = "true"

        # keep track of first SR, compare to each subsequent, bail if mismatch
        if x == 1:
            theSR = aSR.Name
            x += 1
        if x > 1:
            theSR_new = aSR.Name
            if theSR_new != theSR:
                gp.AddError("ERROR: Spatial references for input and status features do not match. Project to common spatial reference and try again.")
                sys.exit("ERROR: Spatial references for input and status features do not match. Project to common spatial reference and try again.")
            
    # Get scratch workspace from input dirs
    inCatalogPath = desc.CatalogPath
    scratchworkspace = GetScratchFromFeatureClass(inCatalogPath)

    # Define temp outputs
    baseLyr = str(random.randint(1,100000)) + ".lyr"
    TmpLyr = scratchworkspace + "\\" + baseLyr
    saveLyr = scratchworkspace + "\\" + str(random.randint(1,100000)) + "aaaLayer.lyr"
    baseTarget_PUs = GetBaseNameFromParameter(Target_PUs, ".shp")

    AddMsgAndPrint("Begin geoprocessing...")

    # Find status    
    if gp.ListFields(Target_PUs,"status").Next():
        statusField = "status"
    elif gp.ListFields(Target_PUs,"Status").Next():
        statusField = "Status"
    elif gp.ListFields(Target_PUs,"STATUS").Next():
        statusField = "STATUS"
    else:
        statusField = "false"

    # Add and delete status field 
    if bool_clear == "true": # if user wants to clear
        if statusField != "false":   # delete any existing field named status
            AddMsgAndPrint("Clearing existsing status field from planning units...")
            gp.DeleteField_management(Target_PUs, statusField)
            # At this point no field named "status" exists except if bool_clear == "false"
            # which escapes above
        AddMsgAndPrint("Adding new status field to planning units...") # true false and true true
        statusField = "STATUS" # reset no matter what 
        fields = gp.addfield(Target_PUs, statusField, "SHORT", "1")
    if bool_clear == "false" and statusField == "false": # false false: user says don't delete
                                                         # but field does not exist
                                                         # will throw error later  
        AddMsgAndPrint("Adding new status field to planning units...")
        statusField = "STATUS" # reset no matter what
        fields = gp.addfield(Target_PUs, statusField, "SHORT", "1")
    #@ false true see below
 
    # Select by feature
    AddMsgAndPrint("Begin select by feature...")
    gp.MakeFeatureLayer(Target_PUs, TmpLyr)
    if bool_clear == "false":
        theExp = "\"STATUS\" = 0"
        AddMsgAndPrint("No clear expression: " + theExp)
        gp.SelectLayerByAttribute(TmpLyr, "NEW_SELECTION",  theExp)
        gp.SelectLayerByLocation(TmpLyr, "intersect", Overlay_status, "#", "SUBSET_SELECTION")
    else: # bool_clear == "true"
        gp.SelectLayerByLocation(TmpLyr, "intersect", Overlay_status, "#", "NEW_SELECTION")
    AddMsgAndPrint("...finished select by feature...")

    # Join result back to original pus
    #if ggSR == "true":
    #    Target_PUs_delete = Target_PUs #reference to projected to delete
    #    Target_PUs = Target_PUs_orig #reset to original planning units

    # Make feature layer on disk (may not be necessary, but works)
    gp.SaveToLayerFile_management(TmpLyr, saveLyr)

    # Calculate on selection
    expression = Status_value
    AddMsgAndPrint("Expression: " + expression)
    calcField = "STATUS"
    AddMsgAndPrint("Calculate field: " + calcField)
    gp.CalculateField_management(saveLyr, calcField, expression, "VB", "#")
 
    # Delete temp files and clean up
    if bool_del == "true":
        #gp.Delete(TmpOut)
        #gp.Delete(DissolveOut)
        gp.Delete(TmpLyr)
        gp.Delete(saveLyr)
        #if ggSR == "true":
        #    gp.Delete(Target_PUs_delete)
        #    gp.Delete(Overlay_cost)
        AddMsgAndPrint("Deleted temp files...")

    AddMsgAndPrint("Script complete")    

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
    