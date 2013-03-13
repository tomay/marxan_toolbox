# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     CalculateCost
# Source Name:   CalculateCost.py
# Version:       Developed in ArcGIS 9.2 and tested in both 9.2 and 9.3
# Required Argumuments: 
# Requirements:         - Projection must be defined.
# Description:  
# Parameters:
#               1.
#               2.
#               3.
#               4.
# Usage: 
# TO DO:
# ----------------------------------------------------------------------------------------------------------------
# Import system modules
import sys, os, arcgisscripting, traceback, random

def FindField(Item,Table):
    fields = gp.ListFields(Table)
    try: #9.2
        fields.Reset()
        field = fields.Next()
        while field:
            #AddMsgAndPrint("Field.name: " + field.Name.lower())
            #AddMsgAndPrint("Item: " + Item.lower())            
            if field.Name.lower() == Item.lower():
                AddMsgAndPrint("Found " + field.Name)
                AddMsgAndPrint("Field type: " + field.type)
                return field
                break 
            field = fields.next()
    except: #9.3
        for field in fields:
             if field.Name.lower() == Item.lower():
                return field
                break            

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
    Pu_Field = sys.argv[2]
    Overlay_cost = sys.argv[3]
    Cost_field = sys.argv[4]
    Cost_out = sys.argv[5]
    analysis_type = sys.argv[6]
    bool_del = sys.argv[7]

    # TO DO: Check for existence of same named cost field in input PUs. This will lead to errors
    # because union will produce GRIDCODE_1 for the union field... best to bail
    aFields = gp.ListFields(Target_PUs, Cost_field)
    field_found = aFields.Next()
    if field_found:
        gp.AddError("ERROR: Selected cost field <" + Cost_field + "> exists in planning units feature class. This will produce error calculating from intersection. Change name of field and try again.")
        sys.exit("ERROR: Selected cost field <" + Cost_field + "> exists in planning units feature class. This will produce error calculating from intersection. Change name of field and try again.")

    covs = []
    covs.append(Overlay_cost)
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
                gp.AddError("ERROR: Spatial references for input and cost features do not match. Project to common spatial reference and try again.")
                sys.exit("ERROR: Spatial references for input and cost features do not match. Project to common spatial reference and try again.")
                    
        # If GCS but different datum than WGS 84, also bail
        if ggSR == "true":
            if aSR.DatumName <> "D_WGS_1984":
                gp.AddError("ERROR: Unsupported datum found. Only WGS 1984 supported. Try again.")
                sys.exit("ERROR: Unsupported datum found. Only WGS 1984 supported. Try again.")

    # Cost field type check, bail if not number
    typeErr = "false"
    theField = FindField(Cost_field, Overlay_cost)
    #AddMsgAndPrint("Field type: " + theField.type)
    if theField.type.lower() == "string":
        typeErr = "true"
    if theField.type.lower() == "text":
        typeErr = "true"
    if theField.type.lower() == "date":
        typeErr = "true"
    if theField.type.lower() == "blob":
        typeErr = "true"
    if theField.type.lower() == "geometry":
        typeErr = "true"
    if typeErr == "true":
        gp.AddError("ERROR: Cost/prob field must be numeric type. Select a numeric field and try again.")
        sys.exit("ERROR: Cost/prob field must be numeric type. Select a numeric field and try again.")

    # Get scratch workspace from input dirs
    inCatalogPath = desc.CatalogPath
    scratchworkspace = GetScratchFromFeatureClass(inCatalogPath)

    # Define temp outputs
    TmpOut = scratchworkspace + "\\" + str(random.randint(1,100000)) + "tmpUnion.shp"
    baseDissolve1 = str(random.randint(1,10000)) + "tDs1.shp"
    baseDissolve = str(random.randint(1,10000)) + "tDs.shp"
    costDissolve = str(random.randint(1,10000)) + "cDs.shp"
    DissolveOut1 = scratchworkspace + "\\" + baseDissolve1
    DissolveOut = scratchworkspace + "\\" + baseDissolve
    DissolveCost = scratchworkspace + "\\" + costDissolve
    #DissolveOut = r"c:\atom\python\shapes\tmpDissolve.shp"
    baseLyr = str(random.randint(1,100000)) + ".lyr"
    TmpLyr = scratchworkspace + "\\" + baseLyr
    saveLyr = scratchworkspace + "\\" + "aaaLayer" + str(random.randint(1,100000)) + ".lyr"
    baseTarget_PUs = GetBaseNameFromParameter(Target_PUs, ".shp")

    AddMsgAndPrint("Begin geoprocessing...")
  
    # If GCS project input and overlay to Equal Area
    if ggSR == "true":
        AddMsgAndPrint("Begin projecting...")
        for cov in covs:
            useProjected = "true"
            outCs = "PROJCS['World_Cylindrical_Equal_Area',GEOGCS['GCS_WGS_1984', \
                    DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]], \
                    PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]], \
                    PROJECTION['Cylindrical_Equal_Area'],PARAMETER['False_Easting',0.0], \
                    PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0], \
                    PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"
            cov2 = cov.replace(".shp", "_pr.shp")
            gp.project_management(cov, cov2, outCs)
            if cov == Target_PUs: # switch ref to projected
                Target_PUs_orig = Target_PUs
                Target_PUs = cov2
            if cov == Overlay_cost:
                Overlay_cost = cov2
        AddMsgAndPrint("...projection complete...")
        AddMsgAndPrint("pus projected to: " + Target_PUs)
        AddMsgAndPrint("cost projected to: " + Overlay_cost)

    # Step 1 dissolve on pu id
    AddMsgAndPrint("Start dissolve on pufield...")
    #sums = SumFieldName + " SUM"
    #AddMsgAndPrint("Expression: " + sums)
    gp.Dissolve_management(Target_PUs, DissolveOut1, Pu_Field)
    AddMsgAndPrint("...finished dissolve pus...")
    Target_PUs = DissolveOut1 # switch
    # dissolve cost too
    # 6/23/2011: Dissolving cost has the effect of making huge areas with the same cost value. If dissolve, should these costs
    # be summed across the joined polygons? Why dissolve cost in the first place?
    # commented out the following three lines
    #gp.Dissolve_management(Overlay_cost, DissolveCost, Cost_field)
    #AddMsgAndPrint("...finished dissolve cost...")
    #Overlay_cost = DissolveCost # Switch

    # Add temp area field to PUs and delete after script
    # TO DO: test if exists, and rename if nec.
    AddMsgAndPrint("Begin calculate area...")
    tmpAreaField = "puAr" + str(random.randint(1,1000))
    tmpAreaField2 = "cstAr" + str(random.randint(1,1000))
    gp.AddField_management(Target_PUs, tmpAreaField, "FLOAT", "25", "4")
    gp.CalculateField_management(Target_PUs, tmpAreaField, "float(!SHAPE.AREA!)", "PYTHON")
    gp.AddField_management(Overlay_cost, tmpAreaField2, "FLOAT", "25", "4")
    gp.CalculateField_management(Overlay_cost, tmpAreaField2, "float(!SHAPE.AREA!)", "PYTHON")
    AddMsgAndPrint("...finished calculating area...")

    # Union
    AddMsgAndPrint("Begin union...")
    fcstr = str(Target_PUs) + ';' + str(Overlay_cost)
    gp.intersect_analysis(fcstr, TmpOut, "ALL", 0.0001)
    AddMsgAndPrint("...finished union...")

    # Calculate areas
    AddMsgAndPrint("Start calculating areas on union...")
    # TO DO: test if any of these field names exist already
    # and gen another name if they do
    AreaFieldName = "af" + str(random.randint(1,10000))
    SumFieldName = "sm" + str(random.randint(1,1000))
    gp.AddField_management(TmpOut, AreaFieldName, "FLOAT", "25", "4")
    gp.AddField_management(TmpOut, SumFieldName, "FLOAT", "25", "4")
    gp.CalculateField_management(TmpOut, AreaFieldName, "float(!SHAPE.AREA!)", "PYTHON")
    #expression = "[" + AreaFieldName + "] * [" + Cost_field + "]"
    # TO DO: Select area > 0 to avoid div by 0 error, shouldn't happen (due to intersect) but just in case
    # Area weighted average. Polygon fraction (union poly area/cost poly area) X cost attribute value
    #                        ((part/whole) * value)
    # This is fixed now..
    if analysis_type == "Sum total in planning unit":
        AddMsgAndPrint("Selected: Sum total in planning unit")
        # (Area of poly part / Area of original whole cost unit) * cost of whole cost unit
        expression = "([" + AreaFieldName + "] / [" + tmpAreaField2 + "]) * [" + Cost_field + "]"
    if analysis_type == "Percent in planning unit (0-1)":
        AddMsgAndPrint("Selected: Percent in planning unit (0-1)")
        # (area of poly part / area of planning unit) * cost (=1)
        expression = "([" + AreaFieldName + "] / [" + tmpAreaField + "]) * [" + Cost_field + "]"
    #if analysis_type == "Mean in planning unit"):
        #expression = "([" + AreaFieldName + "] / [" + tmpAreaField + "]) * [" + Cost_field + "]"
    
    AddMsgAndPrint("Expression: " + expression)
    gp.CalculateField_management(TmpOut, SumFieldName, expression, "VB", "")
    AddMsgAndPrint("...finished calculating areas...")
    
    # Disolve result and sum
    AddMsgAndPrint("Start dissolve...")
    sums = SumFieldName + " SUM"
    AddMsgAndPrint("Expression: " + sums)
    gp.Dissolve_management(TmpOut, DissolveOut, Pu_Field, sums)
    AddMsgAndPrint("...finished dissolve...")

    # Join result back to original pus
    AddMsgAndPrint("Joining...")
    if ggSR == "true":
        Target_PUs_delete = Target_PUs #reference to projected to delete
        Target_PUs = Target_PUs_orig #reset to original planning units

    # Add or delete cost field 
    fields = gp.ListFields(Target_PUs, Cost_out)
    # If ListFields returned anything, the Next operator will fetch the field, as a Boolean condition.
    field_found = fields.Next()
    # BECAUSE EXISTING FIELD OF SAME NAME COULD BE WRONG SIZE OR TYPE, BEST TO DELETE
    if field_found:
        AddMsgAndPrint("Deleting existing cost/prob field...")
        gp.DeleteField_management(Target_PUs, Cost_out)
        AddMsgAndPrint("Adding new cost/prob field to planning units...")
        fields = gp.addfield(Target_PUs, Cost_out, "FLOAT", "25", "4")
    else: 
        AddMsgAndPrint("Adding cost/prob field to planning units...")
        fields = gp.addfield(Target_PUs, Cost_out, "FLOAT", "25", "4")

    # calc new field to 0
    AddMsgAndPrint("Calculating new field to 0...")
    express = "0"
    gp.CalculateField_management(Target_PUs, Cost_out, express, "VB", "")
    AddMsgAndPrint("...done calculating new field to 0...")

    # Process: Make Layer to work with AddJoin
    gp.addindex(DissolveOut, Pu_Field, "#") # index to boost performance?
    gp.addindex(Target_PUs, Pu_Field, "#")
    gp.MakeFeatureLayer_management(Target_PUs, TmpLyr)
    ## gp.AddJoin_management(TmpLyr, Pu_Field, DissolveOut, Pu_Field, "INNER")
    gp.AddJoin_management(TmpLyr, Pu_Field, DissolveOut, Pu_Field, "KEEP_COMMON")
    AddMsgAndPrint("...indexed and joined...")

    # Make feature layer on disk
    ## Not using for now. Does not work
    ## AddMsgAndPrint("Saving layer...")
    ##gp.SaveToLayerFile_management(TmpLyr, saveLyr)

    # For very large selections (> 20000 rows) below may be affected by
    # http://resources.arcgis.com/content/kbase?fa=articleShow&d=22668 (registry fix to increase performance)
    # and in 9.2, the following bug in calculate_field
    # http://forums.esri.com/Thread.asp?c=93&f=1727&t=213148
    # which may be fixed by changing "affinity" of ArcGIS.exe process so that it only uses one processer

    # Select non-null rows and calculate
    selExp = "\"" + baseDissolve.replace(".shp","") + "." + Pu_Field.lower() + "\"" + " IS NOT NULL"
    AddMsgAndPrint("Select expression: " + selExp)
    gp.SelectLayerByAttribute_management(TmpLyr, "NEW_SELECTION", selExp)
    count = gp.GetCount_management(TmpLyr)
    AddMsgAndPrint("Rows selected: " + str(count))
    expression = "[" + baseDissolve.replace(".shp","") + ".SUM_" + SumFieldName + "]"
    AddMsgAndPrint("Expression: " + expression)
    calcField = baseTarget_PUs.replace(".shp","") + "." + Cost_out.upper()
    AddMsgAndPrint("Calculate field: " + calcField)
    gp.CalculateField_management(TmpLyr, calcField, expression, "VB", "")
    AddMsgAndPrint("...finished calculate on join field...")
 
    # Delete temp files and clean up
    gp.RemoveJoin(TmpLyr, baseDissolve.replace(".shp","")) 
    if ggSR == "false":
        AddMsgAndPrint("Begin delete temp field...")
        gp.DeleteField_management(Target_PUs, tmpAreaField)
    if bool_del == "true":
        AddMsgAndPrint("Begin delete temp files...")
        gp.Delete(TmpOut)
        gp.Delete(DissolveOut)
        gp.Delete(TmpLyr)
        gp.Delete(DissolveCost)
        gp.Delete(DissolveOut1)
        ## gp.Delete(saveLyr)
        if ggSR == "true":
            AddMsgAndPrint("Delete " + sys.argv[1].replace(".shp", "_pr.shp"))
            AddMsgAndPrint("Delete " + sys.argv[3].replace(".shp", "_pr.shp")) 
            gp.Delete(sys.argv[1].replace(".shp", "_pr.shp"))
            gp.Delete(sys.argv[3].replace(".shp", "_pr.shp"))
        AddMsgAndPrint("...deleted temp files...")

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
    
