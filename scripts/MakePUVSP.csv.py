# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     MakePUVSP.csv
# Source Name:   MakePUVSP.csv.py
# Min Version:   ArcGIS 9.2
# Max Version:   ArcGIS 9.3
# Required Argumuments: - An Input Feature Class representing planning units
#                       - An Input folder containing conservation features
#                       - An output csv file name
# Requirements:         - Input feature class must be polygon with unique IDs
#                       - Spatial Analyst license if using grids
# Description:  
# Usage: 
# ----------------------------------------------------------------------------------------------------------------

# Import system modules
import csv, sys, os, arcgisscripting, traceback, random

def AddMsgAndPrint(message):
    gp.AddMessage(message)
    print message
    return 0

# -------------------------------------------
# BEGIN
# -------------------------------------------
# Create the Geoprocessor object
gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    gp.workspace = sys.argv[1]
    pattern = sys.argv[2]
    pus = sys.argv[3]
    puid = sys.argv[4]
    output = sys.argv[5]
    conv = sys.argv[6]
    doDel = sys.argv[7]

    # temp variables
    puid = puid.upper()
    if pattern == "RASTER":
        if gp.CheckExtension("spatial") != "Available":
            gp.AddError("ERROR: Spatial analyst extension not found. Exiting...")
            sys.exit("ERROR: Spatial analyst extension not found. Exiting...")
        else:
            gp.CheckoutExtension("spatial")
        
    # Check if input is projected and bail if undefined...
    pudesc = gp.Describe(pus)
    ggSR = "false"
    aSR = pudesc.SpatialReference
    if aSR.Name == "Unknown":
        gp.AddError("ERROR: You must define a spatial reference for the planning unit shapefile. Define projection and try again.")
        sys.exit("ERROR: You must define a spatial reference for the planning unit shapefile. Define projection and try again.")
    elif aSR.Name[:3] == "GCS":
        ggSR = "true"
    elif aSR.Type == "Geographic":
        ggSR = "true"

    # If GCS but different datum than WGS 84, also bail
    if ggSR == "true":
        if aSR.DatumName <> "D_WGS_1984":
            gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
            sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")        

    # find only specified features or datasets
    if pattern == "*.shp":
        datasets = gp.ListFeatureClasses("", "POLYGON")
        msg = "shapefiles"
    elif pattern == "RASTER":
        datasets = gp.ListDatasets("", "RASTER")
        msg = "grids"

    i = 0
    files = [] # Get full path of desired grids or shapes into simple list
    DoExit = "false"
    #try: #9.2
    datasets.Reset()
    dataset = datasets.next()
    while dataset:
        desc = gp.Describe(dataset)
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

        elif pattern == "RASTER":
            # check raster extents
            ext = desc.extent
            meanx = desc.MeanCellWidth
            if i == 0:
                if aSR.name != bSR.name: # spatial ref of first grid does not match pus
                    DoExit = "true"
                    Err = "ERROR: Spatial reference of pus does not match spatial reference of one or more grids. Exiting..."                       
                    gp.AddError("ERROR: Spatial reference of pus does not match spatial reference of one or more grids. Exiting...")
                    sys.exit("ERROR: Spatial reference of pus does not match spatial reference of one or more grids. Exiting...")                        
                elif bSR.Name == "Unknown": # spatial ref of first grid does not match pus
                    DoExit = "true"
                    Err = "ERROR: Spatial reference undefined for one or more grids. Exiting..."
                    gp.AddError("ERROR: Spatial reference undefined for one or more grids. Exiting...")
                    sys.exit("ERROR: Spatial reference undefined for one or more grids. Exiting...")
                elif ggSR == "true":
                    if bSR.DatumName <> "D_WGS_1984":
                        DoExit = "true"
                        Err = "ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again."
                        gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
                        sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.") 
            elif i > 0:
                if ext != Ext_save:
                    DoExit = "true"
                    Err = "ERROR: Grid extents do not match. Exiting..."
                    gp.AddError("ERROR: Grid extents do not match. Exiting...")
                    sys.exit("ERROR: Grid extents do not match. Exiting...")
                elif meanx != Meanx_save:
                    DoExit = "true"
                    Err = "ERROR: Grid cells do not match. Exiting..."
                    gp.AddError("ERROR: Grid cells do not match. Exiting...")
                    sys.exit("ERROR: Grid cells do not match. Exiting...")
                elif bSR.name != SR_save:
                    DoExit = "true"
                    Err = "ERROR: Spatial reference of one or more grids do not match. Exiting..."
                    gp.AddError("ERROR: Spatial reference of one or more grids do not match. Exiting...")
                    sys.exit("ERROR: Spatial reference of one or more grids do not match. Exiting...")
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
            Ext_save = ext
            Meanx_save = meanx
            #SR_save = bSR.name
        dataset = datasets.next()
            
    #except: #9.3
    #    if DoExit == "true":
    #        sys.exit(Err)
    #    for dataset in datasets:
    #        if pattern == "*.shp": 
    #            if dataset[len(dataset)-4:] == ".shp":
    #                file = gp.workspace + os.sep + dataset
    #                files.append(file)
    #                i = i + 1
    #        elif pattern == "RASTER":
    #            desc = gp.Describe(dataset)
    #            ext = desc.extent
    #            meanx = desc.MeanCellWidth
    #            bSR = desc.SpatialReference
    #            if i == 0:
    #                if aSR.name != bSR.name: # spatial ref of first grid does not match pus
    #                    DoExit = "true"
    #                    Err = "ERROR: Spatial reference of pus does not match spatial reference of one or more grids. Exiting..."
    #                    gp.AddError("ERROR: Spatial reference of pus does not match spatial reference of one or more grids. Exiting...")
    #                    sys.exit("ERROR: Spatial reference of pus does not match spatial reference of one or more grids. Exiting...")                        
    #                elif bSR.name == "Unknown": 
    #                    DoExit = "true"
    #                    Err = "ERROR: Spatial reference undefined for one or more grids. Exiting..."
    #                    gp.AddError("ERROR: Spatial reference undefined for one or more grids. Exiting...")
    #                    sys.exit("ERROR: Spatial reference undefined for one or more grids. Exiting...")
    #                elif ggSR == "true":
    #                    if bSR.DatumName <> "D_WGS_1984":
    #                        DoExit = "true"
    #                        Err = "ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again."
    #                        gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
    #                        sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
    #            if i > 0:
    #                if ext != Ext_save:
    #                    gp.AddError("ERROR: Grid extents do not match. Exiting...")
    #                    sys.exit("ERROR: Grid extents do not match. Exiting...")
    #                if meanx != Meanx_save:
    #                    gp.AddError("ERROR: Grid cells do not match. Exiting...")
    #                    sys.exit("ERROR: Grid cells do not match. Exiting...")
    #                elif bSR.name != SR_save:
    #                    gp.AddError("ERROR: Spatial reference of one or more grids do not match. Exiting...")
    #                    sys.exit("ERROR: Spatial reference of one or more grids do not match. Exiting...")
    #                elif ggSR == "true":
    #                    if bSR.DatumName <> "D_WGS_1984":
    #                        gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.")
    #                        sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported for GCS. Try again.") 
    #            
    #            file = gp.workspace + os.sep + dataset
    #            files.append(file)
    #            Ext_save = ext
    #            Meanx_save = meanx
    #            SR_save = bSR.name
    #            i = i + 1
    AddMsgAndPrint(str(i) + " " + msg + " found...")

    if ggSR == "true":
        AddMsgAndPrint("Begin projecting planning units...")
        outCs = "PROJCS['World_Cylindrical_Equal_Area',GEOGCS['GCS_WGS_1984', \
                DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]], \
                PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]], \
                PROJECTION['Cylindrical_Equal_Area'],PARAMETER['False_Easting',0.0], \
                PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0], \
                PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"
        pus2 = pus.replace(".shp", "_pr" + str(random.randint(1,10000)) + ".shp")
        AddMsgAndPrint("pus2: " + pus2)
        gp.project_management(pus, pus2, outCs)
        AddMsgAndPrint("...finished projecting planning units...")
        pus_orig = pus # switch probably not needed
        pus = pus2

        AddMsgAndPrint("...projection complete...")
        AddMsgAndPrint("pus projected to: " + pus)

    # Look for field named area in pus; add if not found; update
    AddMsgAndPrint("Updating area field...")
    fields = gp.ListFields(pus, "AREA")
    field_found = fields.Next()
    if not field_found:
        AddMsgAndPrint("Adding area field to pus...")
        gp.AddField_management(pus, "AREA", "DOUBLE")
    gp.CalculateField_management(pus, "AREA", "float(!SHAPE.AREA!)", "PYTHON")
    AddMsgAndPrint("...area calc complete...")

    ## Setup output csv file
    ## TO DO: strip output and construct file name given potential for full path, file only, no extension, etc.
    OutputCSV = gp.workspace + os.sep + output
    header = ["species","id","amount"]
    good_fields = [puid, "AREA"]
    AddMsgAndPrint("Good fields 1: " + good_fields[0])
    AddMsgAndPrint("Good fields 2: " + good_fields[1])    
    
    outfile = open(OutputCSV,'wb')
    linewriter = csv.writer(outfile, delimiter=',')
    AddMsgAndPrint("Writing header...")
    linewriter.writerow(header)
    AddMsgAndPrint("...done writing header...")

    spid = 0 # counter for species
    
    # if shape
    if pattern == "*.shp":    
        for sFile in files:
            tmpOut = gp.workspace + os.sep + "intr" + str(random.randint(1,100000)) + ".shp"
            dissolveOut = gp.workspace + os.sep + "diss" + str(random.randint(1,100000)) + ".shp"
            spid = spid + 1
            if ggSR == "true":
                sFile2 = sFile.replace(".shp", "_pr" + str(random.randint(1,10000)) + ".shp")
                gp.project_management(sFile, sFile2, outCs)
                sFile_orig = sFile # switch probably not needed
                sFile = sFile2
            fcstr = str(pus) + ';' + str(sFile)
            gp.intersect_analysis(fcstr, tmpOut, "ALL", 0.0001)
            # Process: dissolve on pu field, then add area, then get cursor on dissolve table
            gp.Dissolve_management(tmpOut, dissolveOut, puid)
            areaFld = "AREA" + str(random.randint(1,10))
            gp.AddField_management(dissolveOut, areaFld, "DOUBLE")
            gp.CalculateField_management(dissolveOut, areaFld, "float(!SHAPE.AREA!)", "PYTHON")
            good_fields[1] = areaFld # replace name of area field to search for
            #AddMsgAndPrint("area field: " + areaFld)
            #AddMsgAndPrint("pu field: " + puid)
            #AddMsgAndPrint("gf1: " + good_fields[0])
            #AddMsgAndPrint("gf2: " + good_fields[1])           

            # -------------------------------------------
            # Export to csv -- shapes
            # -------------------------------------------                    
            # Cursor for table body
            fields = gp.ListFields(dissolveOut)
            cursor = gp.SearchCursor(dissolveOut)
            row = cursor.Next()

            # Loop iterates over table body, writes lines and rows
            i = 0
            while row:
                line = []
                # first add value for that species
                line.append(spid)
                try:                       #9.2 and below
                    fields.Reset()
                    field = fields.Next()
                    while field:
                        if field.Name.upper() in good_fields:
                            value = row.GetValue(field.Name)
                            if field.Name.upper() == puid: # cast this one as integer
                                value = int(value)
                            line.append(value)
                        field = fields.Next()
                except:                    #9.3 and above
                    if field.Name.upper() in good_fields:
                        for field in fields:
                            value = row.GetValue(field.Name)
                            if field.Name.upper() == puid:
                                value = int(value) # cast this one as integer
                            line.append(value)
                linewriter.writerow(line)
                i = i + 1
                del line
                row = cursor.Next()

            del cursor
            if doDel == "true":
                gp.Delete(tmpOut)
                gp.Delete(dissolveOut)
                if ggSR == "true":
                    gp.Delete(sFile) # the projected copy
            AddMsgAndPrint("...done writing " + str(i) + " occurrences for species id " + str(spid) + "...")
            
    # If grid, convert pu to point
    if pattern == "RASTER":
        fields = gp.ListFields(pus)
        # Make pu layer to use in subsequent steps
        puLyr = "puLyr" + str(random.randint(1,100000))
        gp.MakeFeatureLayer(pus, puLyr) # Make pu layer
        for gFile in files:
            spid = spid + 1
            gPoints = gp.workspace + os.sep + "gpoints" + str(random.randint(1,100000)) + ".shp"
            gPointLyr = "gPtLyr" + str(random.randint(1,100000))
            #gdLyr = "gdLyr" + str(random.randint(1,1000))
            outGd = "x" + str(random.randint(1,1000))
            #gp.MakeRasterLayer_management(gFile, gdLyr, "\"VALUE\" = 1")
            Where_clause = "Value = 1"
            gp.ExtractByAttributes_sa(gFile, Where_clause, outGd)
            gp.RasterToPoint_conversion(outGd, gPoints)
            if ggSR == "true":
                gPoints2 = gPoints.replace(".shp", "_pr" + str(random.randint(1,10000)) + ".shp")
                gp.project_management(gPoints, gPoints2, outCs)
                gPoints_orig = gPoints # switch 
                gPoints = gPoints2
            gp.MakeFeatureLayer_management(gPoints, gPointLyr)
            # Select all spp points that overlap the planning units
            gp.SelectLayerByLocation_management(puLyr, "intersect", gPointLyr)

            # -------------------------------------------
            # Export to csv -- RASTER
            # -------------------------------------------                    
            # Cursor for table body            
            cursor = gp.SearchCursor(puLyr)
            row = cursor.Next()

            # Loop iterates over table body, writes lines and rows
            i = 0
            while row:
                line = []
                # first add value for that species
                line.append(spid)
                try:                       #9.2 and below
                    fields.Reset()
                    field = fields.Next()
                    while field:
                        if field.Name.upper() in good_fields:
                            #AddMsgAndPrint("field: " + field.Name)
                            value = row.GetValue(field.Name)
                            if field.Name.upper() == puid: # cast this one as integer
                                value = int(value)
                            line.append(value)
                        field = fields.Next()
                except:                    #9.3 and above
                    if field.Name.upper() in good_fields:
                        for field in fields:
                            value = row.GetValue(field.Name)
                            if field.Name.upper() == puid:
                                value = int(value) # cast this one as integer
                            line.append(value)
                linewriter.writerow(line)
                i = i + 1
                del line
                row = cursor.Next()

            del cursor
            #outfile.close()
            if doDel == "true":
                gp.Delete(gPoints)
                gp.Delete(gPointLyr)
                gp.Delete(outGd)
                if ggSR == "true":
                    gp.Delete(gPoints_orig)
            AddMsgAndPrint("...done writing " + str(i) + " occurrences for species id " + str(spid) + "...")
    outfile.close()
    # conv matrix
    if conv != "#":
        AddMsgAndPrint("Converting from spp order to pu order...")
        batFile = open(gp.workspace + os.sep + "conv_bat.bat", "w")
        batFile.write(conv + " 2 " + OutputCSV + " " + OutputCSV.replace(".csv","_conv.csv"))
        batFile.close()
        os.system(batFile.name)
        AddMsgAndPrint("...done converting from spp order to pu order...")

    if doDel == "true":
        if ggSR == "true":
            gp.Delete(pus2)
        if conv != "#":
            os.remove(batFile.name)
    AddMsgAndPrint("...done writing table body for all planning units...")
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

    
