# ----------------------------------------------------------------------------------------------------------------
# Tool Name:     MakeSPECIES.csv
# Source Name:   MakeSPECIES.csv.py
# Min Version:   ArcGIS 9.2
# Max Version:   ArcGIS 9.3
# Required Argumuments: - An existing PUVSP.csv file in species order
# Requirements:         - An existing PUVSP.csv file in species order
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
    pufile = sys.argv[1]
    gp.workspace = sys.argv[2]
    pattern = sys.argv[3]    
    outspp = sys.argv[4]
    spfVal = sys.argv[5]
    targ_perc = sys.argv[6]
    targ_param = sys.argv[7]
    targ_type = ""
    targ_log = ""

    if targ_perc != "#":
        targ_type = "Percent"
        targ_log = targ_perc 
        targ_perc = float(targ_perc)

    if targ_param != "#":
        targ_type = "Target varies by area"
        targ_log = targ_param
        targ_params = targ_param.split(",")
        n = 0
        for t in targ_params:
            #AddMsgAndPrint(t)
            e = is_number(t)
            if e == "false":
                gp.AddError("ERROR: Parameters must be numeric. Exiting...")
                sys.exit("ERROR: Parameters must be numeric. Exiting...")            
        # local variables
        #eul = 2.7182818284590452353602874713527
        eul = 2.718281828
        rminS = targ_params[0]  # threshold for 100% 
        rmaxS = targ_params[1]  # threshold for min (e.g. 10%)
        aminS = targ_params[2]  # minimum asymptote
        tmaxS = targ_params[3]  # maximum range size (accepts 0)
        # cast all to float
        rmin = float(rminS)
        rmax = float(rmaxS)
        amin = float(aminS)/100 # convert to percent
        tmax = float(tmaxS)

    # find only specified features or datasets
    if pattern == "*.shp":
        datasets = gp.ListFeatureClasses("", "POLYGON")
        msg = "shapefiles"
    elif pattern == "RASTER":
        datasets = gp.ListDatasets("", "RASTER")
        msg = "grids"

    i = 0
    files = [] # Get full path of desired grids or shapes into simple list
    datasets.Reset()
    dataset = datasets.next()
    while dataset:
        if pattern == "*.shp":
            if dataset[len(dataset)-4:] == ".shp":
                #file = gp.workspace + os.sep + dataset
                dataset = dataset.replace(".shp","")
                files.append(dataset)
                i = i + 1
        elif pattern == "RASTER":
            #file = gp.workspace + os.sep + dataset
            files.append(dataset)
            i = i + 1
        dataset = datasets.next()
    AddMsgAndPrint(str(i) + " " + msg + " found...")

    puread = open(pufile, "r")
    outfile = open(outspp,'wb')
    l = outspp.split(os.sep)
    l[-1] = "range.csv"
    rangefile = open(string.join(l,os.sep),'wb')
    l[-1] = "log.txt"
    logfile = open(string.join(l,os.sep),'wb')

    i = 0; area = 0.00000; x = 0; z = 0
    amount_index = 0; pu_index = 0; spec_index = 0; target = 0.0
    ## for line in puread.readlines():
    # Not necessary to call .readlines, and this opens entire file in memory
    # It is possible to directly iterate the file, File is iterable
    for line in puread:    
        fields = line.split(",")
        # use header to find spid and amount fields
        if i == 0:
            #header = line
            for field in fields:
                if field == "id":
                    pu_index = x
                if field == "species":
                    spec_index = x
                if field.strip() == "amount":
                    amount_index = x
                x = x + 1
            #line = "sp_id" + "," + "name" + "," + "amount\n"
            line = "id" + "," + "type" + "," + "target" + "," + "spf" + "," + "target2" + "," + "sepdistance" + "," + "sepnum" + "," + "name" + "," + "targetocc\n"
            outfile.write(line) 
            outfile.flush
            rangefile.write("species_id,species_name,total_range\n")
            rangefile.flush
            spp_save = "1" # TO DO assumes sppid always starts with 1 ? WHAT if not?
        if i > 0:
            if fields[spec_index] == spp_save: # curr sppid == previous sppid
                area = area + float(fields[amount_index])
                spp_save = fields[spec_index]
                
            else:
                writerangeline = spp_save + "," + files[z] + "," + str(area) + "\n"
                if targ_perc != "#":
                    target = area * (targ_perc / 100)
                else:
                    if area <= rmin:
                        #AddMsgAndPrint(str(area) + " is less than " + str(rmin))
                        target = area # 100% target
                                       
                    elif area <= (rmax/eul):
                        target = area * (1 + ((amin-1) * ((math.log(area))-(math.log(rmin)))/((math.log(rmax))-(math.log(rmin)))))
                    else:
                        target = (amin * area) - (((rmax/eul) * (amin - 1))/((math.log(rmax))-(math.log(rmin))))
                    ## check if result exceeds specified Max Target Are
                    if (tmax > 0) and (target >= tmax):
                        target = tmax
                line = spp_save + "," + "0" + "," + str(target) + "," + str(spfVal) + "," + "0.0" + "," + "0.0" + "," + "0" + "," + files[z] + "," + "0\n"
                AddMsgAndPrint("Species: " + files[z] + ", Total area: " + str(area))
                outfile.write(line)
                outfile.flush
                rangefile.write(spp_save + "," + files[z] + "," + str(area) + "\n")
                rangefile.flush
                area = float(fields[amount_index]) # new species, new area total from 0
                z = z + 1
                spp_save = fields[spec_index]

        i = i + 1 # row counter

    # final line
    if targ_perc != "#":
        target = area * (targ_perc / 100)
    else:
        if area <= rmin:
            target = area # 100%
        elif area <= (rmax/eul):
            target = area * (1 + ((amin-1) * ((math.log(area))-(math.log(rmin)))/((math.log(rmax))-(math.log(rmin)))))
        else:
            target = (amin * area) - (((rmax/eul) * (amin - 1))/((math.log(rmax))-(math.log(rmin)))) 
        ## check if result exceeds specified Max Target Are
        if (tmax > 0) and (target >= tmax):
            target = tmax

    line = spp_save + "," + "0" + "," + str(target) + "," + str(spfVal) + "," + "0.0" + "," + "0.0" + "," + "0" + "," + files[z] + "," + "0\n"
    outfile.write(line)
    outfile.flush
    outfile.close
    rangefile.write(spp_save + "," + files[z] + "," + str(area) + "\n")
    rangefile.flush
    rangefile.close
    logfile.write("Species: " + spp_save + "\n")
    logfile.write("Target params type: " + targ_type + "\n")
    logfile.write("Target params: " + targ_log)
    logfile.flush
    logfile.close

    AddMsgAndPrint("Script is complete")  

# TO DO: Write log, range files
    
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
