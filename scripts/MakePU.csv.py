# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     MakePU.csv
# Source Name:   MakePU.csv.py
# Version:       ArcGIS 9.2 and 9.3
# Required Argumuments: - An Input Feature Class
#                       - An output csv file name
# Requirements:         - Input feature class must be polygon otherwise script will exit with error 
# Description:  
# Usage: 
# ----------------------------------------------------------------------------------------------------------------

# Import system modules
import csv, sys, os, arcgisscripting, traceback

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

# -------------------------------------------
# BEGIN
# -------------------------------------------
# Create the Geoprocessor object
gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    # Get parameters
    Target_FC = sys.argv[1]
    OutputFileName = sys.argv[2]
    Puid = sys.argv[3]
    Cost = sys.argv[4]
    Status = sys.argv[5]
    Prob = sys.argv[6]
    Xfield = sys.argv[7]
    Yfield = sys.argv[8]    
    
    desc = gp.describe(Target_FC)
    dft = desc.ShapeType
    dft2 = dft.lower()
    if dft2 != "polygon":
        gp.AddError("ERROR: Input feature class must be of type polygon. Select a polygon shapefile or coverage and try again.")
        sys.exit("ERROR: Input feature class must be of type polygon. Select a polygon shapefile or coverage and try again.")

    # puid field type check, bail if not number
    typeErr = "false"
    theField = FindField(Puid, Target_FC)
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

    # Get final name from text
    Output_Name = GetBaseNameFromParameter(OutputFileName, ".csv")

    # Get scratch workspace from input dirs
    inCatalogPath = desc.CatalogPath
    scratchworkspace = GetScratchFromFeatureClass(inCatalogPath)

    # Get temp variables
    OutputCSV = scratchworkspace + "\\" + Output_Name
    header = []
    good_fields = []

    # Get good fields from params    
    good_fields.append(Puid)
    header.append("id")
    if Cost != "#":
        good_fields.append(Cost)
        header.append("cost")
    if Status != "#":
        good_fields.append(Status)
        header.append("status")
    if Prob != "#":
        good_fields.append(Prob)
        header.append("prob")
    if (Xfield != "#") and (Yfield != "#"):
        good_fields.append(Xfield)
        good_fields.append(Yfield)
        header.append("xloc")
        header.append("yloc")

    # -------------------------------------------
    # Export to csv
    # -------------------------------------------
    fields = gp.ListFields(Target_FC)
    
    output = open(OutputCSV,'wb')
    linewriter = csv.writer(output, delimiter=',')
    AddMsgAndPrint("Writing header...")
    linewriter.writerow(header)
    AddMsgAndPrint("...done writing header...")
    #output.close

    #output = open(OutputCSV,'wb')
    #linewriter = csv.writer(output, delimiter=',')
    AddMsgAndPrint("Writing table...")
            
    # Cursor for table body            
    cursor = gp.SearchCursor(Target_FC)
    row = cursor.Next()

    # Loop iterates over table body, writes lines and rows
    i = 0
    while row:
        line = []
        d = {} #new dictionary
        #try:                       #9.2 and below
        fields.Reset()
        field = fields.Next()
        while field:
            if field.Name in good_fields:
                value = row.GetValue(field.Name)
                if field.Name == Puid: # cast this one as integer
                    value = int(value)
                    
                #line.append(value)
                d[field.Name] = value
            field = fields.Next()
            
        #except:                    #9.3 and above
        #    if field.Name in good_fields:
        #        for field in fields:
        #            value = row.GetValue(field.Name)
        #            if field.Name == Puid:
        #                value = int(value) # cast this one as integer
        #            line.append(value)

        for fieldname in good_fields:
            line.append(d[fieldname])
        linewriter.writerow(line) 
        i = i + 1
        del line
        row = cursor.Next()

    del cursor
    output.close()
    AddMsgAndPrint("...done writing table body for " + str(i) + " planning units...")
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
