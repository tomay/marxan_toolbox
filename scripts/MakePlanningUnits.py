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

def CalculateOrigin(dataset):
    ext = gp.describe(dataset).extent
    coords = ext.split(" ")
    return coords[0] + " " + coords[1]

def CalculateUR(dataset):
    ext = gp.describe(dataset).extent
    coords = ext.split(" ")
    return coords[2] + " " + coords[3]

def CalculateHeight(width):
    import math
    return float(width) * math.sqrt(3)

def UpdateOrigin(origin, width, height, factor):
    coords = origin.split(" ")
    xcoord = float(coords[0])
    ycoord = float(coords[1])
    return str(xcoord + float(width) * factor) + " " + str(ycoord + float(height) * factor)

def GetYAxisCoords(origin, opposite):
    origin_coords = origin.split(" ")
    xcoord_origin = float(origin_coords[0])
    corner_coords = opposite.split(" ")
    ycoord_opposite = float(corner_coords[1])
    return str(xcoord_origin) + " " + str(ycoord_opposite) 

def GetCols(origin, width, opposite):
    coords = origin.split(" ")
    x_origin = float(coords[0])
    coords = opposite.split(" ")
    x_opposite = float(coords[0])
    return int((x_opposite - x_origin) / int(width))

def CalculateArea(height):
    import math
    sideLength =float(height) / math.sqrt(3)
    area = 2.598076211 * pow(sideLength, 2)
    return area

def AddMsgAndPrint(message):
    gp.AddMessage(message)
    print message
    return 0

def GetWorkspaceType(dataset):
    import os
    desc = gp.describe(os.path.dirname(dataset))
    return desc.workspacetype

def GetLocalDataBaseType(dataset):
    import os
    desc = gp.describe(dataset)
    gdb = os.path.dirname(dataset)
    if gdb.find("mdb") <> -1:
        return "personal"
    else:
        return "file"       

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
    # Check for ArcInfo license
    if ((gp.checkproduct ("arcinfo")).lower() == "available") or ((gp.checkproduct ("arcinfo")).lower() == "alreadyinitialized"):
        gp.setproduct("arcinfo")
    else:
        gp.AddError("ERROR: ArcInfo license level required for these geoprocessing functions. Exiting...")
        sys.exit("ERROR: ArcInfo license level required for these geoprocessing functions. Exiting...")
    
    # Get the parameters.
    Input_Area_of_Interest = sys.argv[1]
    Final_Pus = sys.argv[2]
    Hexagons_Bool = sys.argv[3]
    Width = int(sys.argv[4])
    Width_Square = Width
    #Reference_Grid = sys.argv[5]
    Reference_Grid = "#" #To DO: clean

    # Check if input is projected and bail if undefined...
    desc = gp.Describe(Input_Area_of_Interest)
    ggSR = "false"
    aSR = desc.SpatialReference
    if aSR.Name == "Unknown":
        gp.AddError("ERROR: Spatial reference is undefined for input shapefile. Define projection and try again.")
        sys.exit("ERROR: Spatial reference is undefined for input shapefile. Define projection and try again.")
    elif aSR.Name[:3] == "GCS":
        ggSR = "true"
    elif aSR.Type == "Geographic":
        ggSR = "true"

    if Reference_Grid == "#": # only relevant if not using ref grid
        # If GCS but different datum than WGS 84, also bail
        if ggSR == "true":
            if aSR.DatumName <> "D_WGS_1984":
                gp.AddError("ERROR: Unsupported datum. Only WGS 1984 supported. Try again.")
                sys.exit("ERROR: Unsupported datum. Only WGS 1984 supported. Try again.")

    # Check if grid param exists
    if Reference_Grid == "#":
        gridExists = "false"
    if gp.exists(Reference_Grid):
        gridExists = "true"
        
    # Get final pus name from text
    Final_Pus_Name = GetBaseNameFromParameter(Final_Pus, ".shp")    
    
    # Get scratch workspace from input dirs
    inCatalogPath = desc.CatalogPath
    scratchworkspace = GetPath(Final_Pus)
 
    # Simply to sanitize Final_Pus name, in case user types it in directly
    # TO DO: If full path given, don't strip and add to scratch workspace...
    Final_Pus = scratchworkspace + "\\" + Final_Pus_Name
    AddMsgAndPrint("workspace: " + scratchworkspace)
    AddMsgAndPrint("Final pus: " + Final_Pus)

    # temporary variables    
    Fishnet_1 = scratchworkspace + "\\" + "Fishnet1.shp"
    Fishnet_2 = scratchworkspace + "\\" + "Fishnet2.shp"
    Fishnet_Label_1 = scratchworkspace + "\\" + "Fishnet1_label.shp"
    Fishnet_Label_2 = scratchworkspace + "\\" + "Fishnet2_label.shp"
    Appended_Points_Name = "hex_points"
    Appended_Points = scratchworkspace + "\\" + "hex_points" + str(random.randint(1,100000)) + ".shp"
    Output_theissen = scratchworkspace + "\\" + "hex" + str(random.randint(1,100000)) + ".shp"
    Final_Hex = scratchworkspace + "\\" + Final_Pus_Name.replace(".shp","_hex.shp")
    in_Field = "puid"
    # randomize name to help with gp.FeatureToPolygon_management bug
    Fishnet_Ln = scratchworkspace + "\\" + "squares" + str(random.randint(1,100000)) + ".shp"
    Fishnet_Sq = scratchworkspace + "\\" + "final_squares" + str(random.randint(1,100000)) + ".shp"
    Input_Projected = scratchworkspace + "\\" + "input_projected" + str(random.randint(1,100000)) + ".shp"

    #------------------------------------------------------
    # Project input shape only if input geographic
    #   and no reference grid, otherwise gg input ok
    #------------------------------------------------------
    useProjected = "false"
    if gridExists == "false": 
        if ggSR == "true":
            useProjected = "true"
            outCs = "PROJCS['World_Cylindrical_Equal_Area',GEOGCS['GCS_WGS_1984', \
                    DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]], \
                    PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]], \
                    PROJECTION['Cylindrical_Equal_Area'],PARAMETER['False_Easting',0.0], \
                    PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0], \
                    PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"
            gp.project_management(Input_Area_of_Interest, Input_Projected, outCs)

    #------------------------------------------------------
    # Clone Input_Area_of_Interest
    #------------------------------------------------------    
    if useProjected == "true":
        Input_Copy = Input_Projected
    else:
        Input_Copy = Input_Area_of_Interest

    #------------------------------------------------------
    # Pre-process if reference grid
    #------------------------------------------------------ 
    if gridExists == "true":
        AddMsgAndPrint("Starting convert on reference grid...")
        InRaster = Reference_Grid
        outPt = scratchworkspace + "\\" + "tmpPt" + str(random.randint(1,100000)) + ".shp"
        outRaster = scratchworkspace + "\\" + "tmpRas" + str(random.randint(1,10000))
        intRaster = scratchworkspace + "\\" + "intRas" + str(random.randint(1,10000))
        expression = "int(" + InRaster + ")"
        gp.SingleOutputMapAlgebra_sa(expression, intRaster) # convert to integer
        gp.RasterToPoint_conversion(intRaster, outPt) # convert to point
        #gp.Extent = Reference_Grid
        #gp.CellSize = Reference_Grid
        #AddMsgAndPrint("Cell size: " + cellsize)
        gp.PointToRaster_conversion(outPt, "POINTID", outRaster, "#", "#", Reference_Grid) # point to raster
        gp.RasterToPolygon_conversion(outRaster, Fishnet_Sq, "NO_SIMPLIFY") # raster to polygon 
        # set to false even if user selected
        Hexagons_Bool = "false"
        gp.delete(outPt)
        gp.delete(outRaster)
        gp.delete(intRaster)
        AddMsgAndPrint("...completed convert on reference grid")

    # Set output filename list
    outFiles = [Final_Pus]
    if Hexagons_Bool == "true":
        outFiles.append(Final_Hex)

    #------------------------------------------------------
    # Hexagons
    #------------------------------------------------------
    if Hexagons_Bool == "true":
        # Process: Calculate Value (Width)...
        Height = CalculateHeight(Width)

        # Invert the height and width so that the flat side of the hexagon is on the bottom and top
        tempWidth = Width
        Width = Height
        Height = tempWidth
        
        # Process: Create Extent Information...
        ll = CalculateOrigin(Input_Copy)
        Origin = UpdateOrigin(ll, Width, Height, -2.0)
        ur = CalculateUR(Input_Copy)
        Opposite_Corner = UpdateOrigin(ur, Width, Height, 2.0) 
        #AddMsgAndPrint("LL Origin: " + ll)
        #AddMsgAndPrint("UR: " + ll)
        
        # Process: Calculate Value (Origin)...
        newOrigin = UpdateOrigin(Origin, Width, Height, 0.5)

        # Process: Calculate Value (Opposite Corner)...
        newOpposite_Corner = UpdateOrigin(Opposite_Corner, Width, Height, 0.5)

        # Process: Calculate Value (Y Axis 1)...
        Y_Axis_Coordinates1 = GetYAxisCoords(Origin, Opposite_Corner)
        
        # Process: Create Fishnet...
        gp.CreateFishnet_management(Fishnet_1, Origin, Y_Axis_Coordinates1, Width, Height, "0", "0", Opposite_Corner, "LABELS", "")
        AddMsgAndPrint("Created fishnet 1...")
        
        # Process: Calculate Value (Y Axis 2)...
        YAxis_Coordinates2 = GetYAxisCoords(newOrigin, newOpposite_Corner)
        #AddMsgAndPrint("YAxis_Coordinates2: " + YAxis_Coordinates2)

        # Process: Calculate Value (Number of Columns)...
        Number_of_Columns = GetCols(Origin, Width, Opposite_Corner)
        #AddMsgAndPrint("Number_of_Columns: " + str(Number_of_Columns))

        # Process: Create Fishnet (2)...
        gp.CreateFishnet_management(Fishnet_2, newOrigin, YAxis_Coordinates2, Width, Height, "0", "0", newOpposite_Corner, "LABELS", "")
        AddMsgAndPrint("Created fishnet 2...")

        # Process: Merge...
        fcstr = str(Fishnet_Label_1) + ';' + str(Fishnet_Label_2)
        #print fcstr
        gp.Merge(fcstr, Appended_Points, '#')
        AddMsgAndPrint("Merged fishnets...")
        
        # Process: Create Thiessen Polygons...
        gp.CreateThiessenPolygons_analysis(Appended_Points, Output_theissen, "ONLY_FID")
        AddMsgAndPrint("Created Vornoi polygons...")

    #------------------------------------------------------
    # Squares
    #------------------------------------------------------
    if gridExists == "false":
        # Set local extent variables
        sqLL = CalculateOrigin(Input_Copy)
        sqUR = CalculateUR(Input_Copy)
        # Buffer UR by one pixel
        aa = str(float(sqUR.split(" ")[0]) + float(Width_Square))
        bb = str(float(sqUR.split(" ")[1]) + float(Width_Square))
        sqUR = aa + " " + bb

        # Get Y-axis coordinate, same x with y = y + Width
        y2 = sqLL.split(" ")[1]
        y2flt = float(y2)
        y2flt2 = y2flt + float(Width_Square)
        sqLL2 = sqLL.split(" ")[0] + " " + str(y2flt2)

        # Process: Create the square fishnet lines
        gp.CreateFishnet_management(Fishnet_Ln, sqLL, sqLL2, Width_Square, Width_Square, "0", "0", sqUR, "NO_LABELS", "")
        AddMsgAndPrint("Made fishnet...")

        # Process: Convert lines to polygons (requires ArcInfo license)    
        gp.FeatureToPolygon_management(Fishnet_Ln, Fishnet_Sq)
        AddMsgAndPrint("Made polygons...")
        gp.Delete(Fishnet_Ln)
        AddMsgAndPrint("Created fishnet squares...")

    #------------------------------------------------------
    # Select by input
    #------------------------------------------------------
    # Necssary for SelectLayerByLocation
    tmpOutLyr = "Output_square_lyr" + str(random.randint(1,10000))
    gp.MakeFeatureLayer(Fishnet_Sq, tmpOutLyr)
    print "Made temp feature layer"
    gp.SelectLayerByLocation(tmpOutLyr, "intersect", Input_Copy)
    print "Done with selection"
    gp.CopyFeatures(tmpOutLyr, Final_Pus)
    print "Done with copy features"

    if Hexagons_Bool == "true":
        # Necssary for SelectLayerByLocation
        tmpOutLyr2 = "Output_theissen_lyr" + str(random.randint(1,10000))
        gp.MakeFeatureLayer(Output_theissen, tmpOutLyr2)
        print "Made temp feature layer"
        gp.SelectLayerByLocation(tmpOutLyr2, "intersect", Input_Copy)
        print "Done with selection"
        gp.CopyFeatures(tmpOutLyr2, Final_Hex)
        print "Done with copy features"

    #------------------------------------------------------
    # Add fields
    #------------------------------------------------------
    # Process: Calculate Polygon ID's...
    # Use the ListFields function to return a list of fields that matches
    #  the name of in_Field. This is a wildcard match. Since in_Field is an
    #  exact string (no wildcards like "*"), only one field should be returned,
    #  exactly matching the input field name.
    if Hexagons_Bool == "false":
        fields = gp.ListFields(Final_Pus, in_Field)
    else:
        fields = gp.ListFields(Final_Pus, in_Field)
        fields2 = gp.ListFields(Final_Hex, in_Field)

    # If ListFields returned anything, the Next operator will fetch the
    #  field. We can use this as a Boolean condition.
    if Hexagons_Bool == "false":
        field_found = fields.Next()
    else: # Hexagons_Bool == "true"
        field_found = fields.Next()
        field_found2 = fields2.Next()

    if not field_found:
        AddMsgAndPrint("Adding puid field to squares...")
        fields = gp.addfield(Final_Pus, in_Field, "LONG", "10")
    if Hexagons_Bool == "true":
        if not field_found2:
            AddMsgAndPrint("Adding puid field to hex...")
            fields2 = gp.addfield(Final_Hex, in_Field, "LONG", "10")

    # ---------------
    # Add IDs to pus
    # ---------------
    for outf in outFiles:
        # Square PU loop
        # Cursor for table body
        AddMsgAndPrint("Calculating planning unit id (puid)...")
        rows = gp.UpdateCursor(outf)
        row = rows.Next()
        n = 1

        # Iterates through attribute table
        AddMsgAndPrint("Iterating rows...")
        while row:
            row.PUID = n
            rows.UpdateRow(row)
            row = rows.Next()
            n += 1
        del rows
        # calc Area only if no ref grid
        if gridExists == "false":
            gp.AddField_management(outf, "Area", "DOUBLE")
            gp.CalculateField_management(outf, "Area", "float(!SHAPE.AREA!)", "PYTHON")
    
    AddMsgAndPrint("Calculated areas and ID's...")

    #------------------------------------------------------
    # If GCS was input; project result back to gg; otherwise projectdefine
    #------------------------------------------------------    
    if useProjected == "true":
        z = 1
        for outf in outFiles:
            AddMsgAndPrint("Reprojecting results...")
            gp.DefineProjection_management(outf,outCs) # define as equal area
            tmpOut = outf.replace(".shp","") + str(z) + ".shp"
            gp.project_management(outf, tmpOut, aSR) # project back to GG
            # delete old, copy new to old, delete new
            gp.Delete(outf)
            gp.CopyFeatures(tmpOut, outf)
            gp.Delete(tmpOut)
            z += 1
        gp.Delete(Input_Projected)
    else:
        for outf in outFiles:
            AddMsgAndPrint("Defining projection for results...")
            gp.DefineProjection_management(outf,aSR) # define same as input
        
    # ---------------
    # Delete files
    # ---------------
    AddMsgAndPrint("Deleting temporary files...")
    # Delete
    if Hexagons_Bool == "true":
        gp.Delete(Fishnet_1)
        gp.Delete(Fishnet_2)
        gp.Delete(Fishnet_Label_1)
        gp.Delete(Fishnet_Label_2)
        gp.Delete(Appended_Points)
        gp.Delete(Output_theissen)
    gp.Delete(Fishnet_Sq)

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

