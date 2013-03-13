# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     MakePlanningUnits
# Source Name:   MakePlanningUnits.py
# Version:       Developed in ArcGIS 9.2 and tested in both 9.2 and 9.3
# Required Argumuments: - An Input Feature Class
#                       - Width of Hexagon
# Requirements:         - Projection must be defined. If data is unprojected (or appears to be),
#                         script will create pus in equal area
#                       - ArcInfo license level
# Description:  The tool creates a square or (optionally) hexagonal polygon feature class and gives the
#               resulting "planning unit" polygons an area and ID. Options: Make hexagons in addition to planning unit
#               squares; use a reference grid to make planning units (hexagons will not be made); intersect with cost
#               surface(s) [1 or 2]
# Usage: MakePUs: <Input_Area_of_Interest> <Output_Hexagonal_Polygons> {Hexagons} <Height_of_PU> 
#               {Reference_Grid} {Cost1} {Cost2}
# ----------------------------------------------------------------------------------------------------------------

# Import system modules
import sys, os, arcgisscripting, traceback, random

def SpatialChecks(datasets,doRaster):
    Err = ""; i = 0; GgSR = "false"; aSR = "Unknown" # initial values
    result = ["pass", Err, GgSR, aSR]
    datasets.Reset()
    dataset = datasets.next()
    while dataset:
        #AddMsgAndPrint("Run: " + str(i) + ". Error: " + Err)  
        desc = gp.describe(dataset)
        bSR = desc.SpatialReference
        if (doRaster == "true"):
            ext = desc.extent
            meanx = desc.MeanCellWidth
            datatype = gp.GetRasterProperties(dataset, "VALUETYPE")
            #AddMsgAndPrint("valuetype: " + str(int(datatype)))
            if str(int(datatype)) != "1":
                Err = "ERROR: Only integer grids supported. Exiting..."
        if i == 0:
            aSR = bSR; result[3] = aSR
            if aSR.Name == "Unknown":
                GgSR = "unknown"
                Err = "ERROR: Spatial reference undefined for one or more input files. Exiting..."
            if aSR.Name[:3] == "GCS":
                GgSR = "true"
            if aSR.Type == "Geographic":
                GgSR = "true"
            if GgSR == "true":
                if bSR.DatumName <> "D_WGS_1984":
                    Err = "ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again." 
        elif i > 0:
            #AddMsgAndPrint("bSR.name: " + bSR.name);AddMsgAndPrint("SR_save start: " + SR_save)
            if doRaster == "true":
                if ext != Ext_save:
                    Err = "ERROR: Grid extents do not match. Exiting..."
                if meanx != Meanx_save:
                    Err = "ERROR: Grid cells do not match. Exiting..."
            if bSR.name != SR_save:
                AddMsgAndPrint("Failed on: " + dataset)
                AddMsgAndPrint("b: " + bSR.name)
                AddMsgAndPrint("SR: " + SR_save)
                Err = "ERROR: Spatial reference of one or more input files does not match, or is undefined. Exiting..."
            if GgSR == "true":
                if bSR.DatumName <> "D_WGS_1984":
                    Err = "ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again."
        i = i + 1
        if (doRaster == "true"):
            Ext_save = ext
            Meanx_save = meanx
        SR_save = bSR.name
        #AddMsgAndPrint("SR_save end: " + SR_save)
        if (Err != ""):
            AddMsgAndPrint("Failed on: " + dataset)
            AddMsgAndPrint("b: " + bSR.name)
            AddMsgAndPrint("SR: " + SR_save)
            result[0] = "fail"
            break
        dataset = datasets.next()
    result[1] = Err
    result[2] = GgSR
    return result

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
# Create the Geoprocessor object and settings
gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    # Check for spatial license
    if gp.CheckExtension("spatial") != "Available":
        gp.AddError("ERROR: Spatial analyst extension not found. Exiting...")
        sys.exit("ERROR: Spatial analyst extension not found. Exiting...")
    else:
        gp.CheckoutExtension("spatial")
    
    # Get the parameters.
    in_grids = sys.argv[1]
    Final_Pus = sys.argv[2]
        
    # Get final pus name from text
    Final_Pus_Name = GetBaseNameFromParameter(Final_Pus, ".shp")    
    gp.workspace = in_grids
    tmpdir = gp.workspace + os.sep + "tmpgp" + str(random.randint(1,1000000))
    os.mkdir(tmpdir)
 
    # Simply to sanitize Final_Pus name, in case user types it in directly with no path
    if len(Final_Pus.split("\\")) == len(Final_Pus.split("/")):
        Final_Pus = gp.workspace + os.sep + Final_Pus_Name
    AddMsgAndPrint("workspace: " + gp.workspace)
    AddMsgAndPrint("tmp dir: " + tmpdir)
    AddMsgAndPrint("Final pus: " + Final_Pus)

    # Get datasets
    datasets = gp.ListDatasets("", "RASTER")
    
    # Run spatial checks to make sure grids match
    AddMsgAndPrint("Starting spatial checks...")
    spatialCheckResults = SpatialChecks(datasets, "true")
    if spatialCheckResults[0] == "fail":
        gp.AddError(spatialCheckResults[1])
        sys.exit(spatialCheckResults[1])
    AddMsgAndPrint("...spatial checks complete...")
    GgSR = spatialCheckResults[2]
    aSR = spatialCheckResults[3]
    AddMsgAndPrint("Geographic: " + GgSR)

    # Make list of files
    files = []
    datasets.Reset()
    dataset = datasets.next()
    while dataset:
        file = gp.workspace + os.sep + dataset
        AddMsgAndPrint("Got: " + file + " ok")
        files.append(file)
        dataset = datasets.next()

    #------------------------------------------------------
    # Grid process
    #------------------------------------------------------ 
    AddMsgAndPrint("Processing grids...")
    x = 0
    for gFile in files:

        max = gp.GetRasterProperties(gFile, "MAXIMUM")
        if x == 0:
            inGrid = gp.createscratchname("","","RASTER",tmpdir)
            rm = "NoData NoData 0; 0 0 0; 1 " + str(int(max)) + " 1"
            gp.Reclassify_sa(gFile, "Value", rm, inGrid, "NODATA")
        if x > 0:
            inGrid2 = gp.createscratchname("","","RASTER",tmpdir)
            rm = "NoData NoData 0; 0 0 0; 1 " + str(int(max)) + " 1"
            gp.Reclassify_sa(gFile, "Value", rm, inGrid2, "NODATA")
            outRaster = gp.createscratchname("","","RASTER",tmpdir)
            expression = "(" + inGrid + " + " + inGrid2 + ")"
            gp.SingleOutputMapAlgebra_sa(expression, outRaster)
            tmpRaster = gp.createscratchname("","","RASTER",tmpdir)
            gp.CopyRaster_management(outRaster, tmpRaster)
            gp.delete(outRaster)
            gp.delete(inGrid)
            gp.delete(inGrid2)
            inGrid = tmpRaster
        x = x + 1
        AddMsgAndPrint("...done with grid " + str(x) + "...")

    AddMsgAndPrint("Making final grid...")
    finalGd = gp.createscratchname("","","RASTER",tmpdir)
    max2 = gp.GetRasterProperties(inGrid, "MAXIMUM")
    remap = "NoData NoData NoData; 0 0 NoData; 1 " + str(int(max2)) + " 1"
    AddMsgAndPrint("Reclass final grid...")
    gp.Reclassify_sa(inGrid, "Value", remap, finalGd, "DATA")
    gp.delete(inGrid)

    AddMsgAndPrint("...done with grids...")    

    #------------------------------------------------------
    # Convert to point, grid, then poly
    #------------------------------------------------------
    tmpPoint = tmpdir + os.sep + "tmpPoint" + str(random.randint(1,10000)) + ".shp"
    tmpGd = tmpdir + os.sep + "tmpGd" + str(random.randint(1,1000))
    AddMsgAndPrint("Making points...")
    gp.RasterToPoint_conversion(finalGd, tmpPoint)
    AddMsgAndPrint("Making grid...")
    gp.PointToRaster_conversion(tmpPoint, "POINTID", tmpGd, "#", "#", finalGd)
    AddMsgAndPrint("Making final polygon...")
    gp.RasterToPolygon_conversion(tmpGd, Final_Pus, "NO_SIMPLIFY")
    gp.delete(finalGd)    

    #------------------------------------------------------
    # Project input shape only if input geographic
    #   and no reference grid, otherwise gg input ok
    #------------------------------------------------------
    if GgSR == "true": # change spatial reference to EA
        aSR_orig = aSR
        outCS = "PROJCS['World_Cylindrical_Equal_Area',GEOGCS['GCS_WGS_1984', \
                DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]], \
                PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]], \
                PROJECTION['Cylindrical_Equal_Area'],PARAMETER['False_Easting',0.0], \
                PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0], \
                PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"

        tmpProj = Final_Pus.replace(".shp","_pr.shp")
        tmp = tmpProj.replace(".shp","tmp.shp")
        gp.MakeFeatureLayer(Final_Pus,"lyr") 
        gp.SelectLayerByAttribute("lyr","NEW_SELECTION","\"ID\" = 1")
        gp.CopyFeatures("lyr",tmp)
        gp.project_management(tmp, tmpProj, outCS)
        descrb = gp.describe(tmpProj)
        aSR = descrb.SpatialReference

    #------------------------------------------------------
    # Add fields
    #------------------------------------------------------
    AddMsgAndPrint("Adding area and puid fields to new planning units...")
    gp.addfield(Final_Pus, "PUID", "LONG", "10")
    gp.AddField_management(Final_Pus, "Area", "DOUBLE")

    AddMsgAndPrint("Calculating planning unit ids (PUID) and areas...")
    rows = gp.UpdateCursor(Final_Pus, "", aSR) # sets cursor to spatial reference of inputs
                                               # technically the last SR from the input grids
                                               # or if GG, the SR from the projection
    row = rows.Next()
    n = 1

    # Iterates through attribute table
    AddMsgAndPrint("Iterating rows...")
    while row:
        row.PUID = n
        feat = row.GetValue("Shape")
        row.SetValue("Area", feat.area)

        rows.UpdateRow(row)
        row = rows.Next()
        n += 1
                
    del rows

    AddMsgAndPrint("Defining projection for results...")
    if GgSR == "true":
        gp.DefineProjection_management(Final_Pus, aSR_orig) 
    else:
        gp.DefineProjection_management(Final_Pus, aSR)

    AddMsgAndPrint("Calculated areas and ID's...")

    # ---------------
    # Delete files
    # ---------------
    AddMsgAndPrint("Deleting temporary files...")
    # Delete
    gp.delete(tmpPoint)
    gp.delete(tmpGd)
    if GgSR == "true":
        gp.delete(tmpProj)
        gp.delete(tmp)

    try:    
        os.remove(tmpdir + os.sep + "info" + os.sep + "arc.dir")
        os.rmdir(tmpdir + os.sep + "info")
        os.remove(tmpdir + os.sep + "log")
        os.rmdir(tmpdir) ## must be empty
    except:
        AddMsgAndPrint("Could not delete temp directory: " + tmpdir)

    AddMsgAndPrint("Script is complete")    

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

