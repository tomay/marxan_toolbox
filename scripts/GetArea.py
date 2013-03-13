# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     
# Source Name:   
# Min Version:   ArcGIS 9.2
# Max Version:   ArcGIS 9.3
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

# -------------------------------------------
# BEGIN
# -------------------------------------------
# Create the Geoprocessor object
gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    gp.workspace = sys.argv[1]
    output = sys.argv[2]
    diss = sys.argv[3]
    scratch = sys.argv[4]
    skip_check = sys.argv[5]
    doDel = sys.argv[6]

    pattern = "*.shp"
    i = 0
    files = [] # Get full path of desired grids or shapes into simple list
    datasets = gp.ListFeatureClasses("", "POLYGON")

    ggSR = "false"
    DoExit = "false"
    if skip_check == "false":
        AddMsgAndPrint("Checking spatial reference of input...")
        
        datasets.Reset()
        dataset = datasets.next()
        msg = "shapefiles"
        while dataset:
            desc = gp.Describe(dataset)
            if i == 0:
                aSR = desc.SpatialReference
                if aSR.Name[:3] == "GCS":
                    ggSR = "true"
                elif aSR.Type == "Geographic":
                    ggSR = "true"
            bSR = desc.SpatialReference
            if pattern == "*.shp":
                if dataset[len(dataset)-4:] == ".shp":
                    if i == 0:
                        if aSR.name != bSR.name: # spatial ref of first grid does not match pus
                            DoExit = "true"
                            Err = "ERROR: Spatial reference of pus does not match spatial reference of one or more polys. Exiting..."                       
                            gp.AddError("ERROR: Spatial reference of pus does not match spatial reference of one or more polys. Exiting...")
                            sys.exit("ERROR: Spatial reference of pus does not match spatial reference of one or more polys. Exiting...")                        
                        elif bSR.Name == "Unknown": # spatial ref of first grid does not match pus
                            DoExit = "true"
                            Err = "ERROR: Spatial reference undefined for one or more polys. Exiting..."
                            gp.AddError("ERROR: Spatial reference undefined for one or more polys. Exiting...")
                            sys.exit("ERROR: Spatial reference undefined for one or more polys. Exiting...")
                        elif ggSR == "true":
                            if bSR.DatumName <> "D_WGS_1984":
                                DoExit = "true"
                                Err = "ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again."
                                gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
                                sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.") 
                    elif i > 0:
                        if bSR.name != SR_save:
                            AddMsgAndPrint("data " + dataset)
                            AddMsgAndPrint("bsr " + bSR.name)
                            AddMsgAndPrint("SR_save " + SR_save)
                            DoExit = "true"
                            Err = "ERROR: Spatial reference of one or more polys do not match. Exiting..."
                            gp.AddError("ERROR: Spatial reference of one or more polys do not match. Exiting...")
                            sys.exit("ERROR: Spatial reference of one or more polys do not match. Exiting...")
                        elif ggSR == "true":
                            if bSR.DatumName <> "D_WGS_1984":
                                DoExit = "true"
                                Err = "ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again."
                                gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
                                sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
                    file = gp.workspace + os.sep + dataset
                    AddMsgAndPrint("Got: " + file + " ok")
                    files.append(file)
                    i = i + 1
                    SR_save = bSR.name
                dataset = datasets.next()

        AddMsgAndPrint(str(i) + " " + msg + " found...")

        if ggSR == "true":
            outCs = "PROJCS['World_Cylindrical_Equal_Area',GEOGCS['GCS_WGS_1984', \
                    DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]], \
                    PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]], \
                    PROJECTION['Cylindrical_Equal_Area'],PARAMETER['False_Easting',0.0], \
                    PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0], \
                    PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"

    outfile = open(output,'wb')
    #linewriter = csv.writer(outfile, delimiter=',')
    AddMsgAndPrint("Writing header...")
    outfile.write("Species,Area\r\n")
    outfile.flush
    AddMsgAndPrint("...done writing header...")

    AddMsgAndPrint("Getting areas...")
    spid = 0 # counter for species
    if skip_check == "true":
        datasets.Reset()
        dataset = datasets.next()
        while dataset:
            file = gp.workspace + os.sep + dataset
            files.append(file)
            dataset = datasets.next()
    for sFile in files:
        base_name = GetBaseName(sFile,".shp")
        dissolveOut = scratch + os.sep + "diss" + str(random.randint(1,100000)) + ".shp"
        if ggSR == "true":
            sFile2 = sFile.replace(".shp", "_pr" + str(random.randint(1,10000)) + ".shp")
            gp.project_management(sFile, sFile2, outCs)
            sFile_orig = sFile # switch probably not needed
            sFile = sFile2

        # Check for dissolve field and add if missing
        dafields = gp.ListFields(sFile, diss)
        field_found = dafields.Next()
        if not field_found:
            AddMsgAndPrint("Adding dissolve field...")
            sFile2 = scratch + os.sep + base_name.replace("shp","") + "_copy" + str(random.randint(1,10)) + ".shp"
            #AddMsgAndPrint(sFile2)
            gp.copy_management(sFile,sFile2,"Shapefile")
            dissFld = "DISS" + str(random.randint(1,10))
            gp.addfield(sFile2,dissFld,"LONG")
            diss = dissFld # switch
            sFile = sFile2 # switch
        
        AddMsgAndPrint("Dissolving " + base_name + "...")
        gp.Dissolve_management(sFile, dissolveOut, diss)
        areaFld = "AREA" + str(random.randint(1,10))
        gp.AddField_management(dissolveOut, areaFld, "DOUBLE")
        AddMsgAndPrint("Summing area for " + base_name + "...")
        gp.CalculateField_management(dissolveOut, areaFld, "float(!SHAPE.AREA!)", "PYTHON")

        fields = gp.ListFields(dissolveOut)
        cursor = gp.SearchCursor(dissolveOut)
        AddMsgAndPrint("Writing area to output for " + base_name + "...")
        row = cursor.Next()
        while row:              # should only be one row after dissolve...
            area = row.GetValue(areaFld)  
            row = cursor.Next()               
        del cursor
        if doDel == "true":
            AddMsgAndPrint("Deleting temp files...")
            gp.Delete(dissolveOut)
            if ggSR == "true":
                gp.Delete(sFile) # the projected copy
            if not field_found:
                gp.Delete(sFile2) # the copy with diss field added
        areastr = ('%.5f' % (area,)).rstrip('0').rstrip('.')
        outfile.write(base_name + "," + areastr + "\r\n")
        outfile.flush
        spid = spid + 1
        AddMsgAndPrint("..done species " + base_name + "...")
    outfile.close        

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
