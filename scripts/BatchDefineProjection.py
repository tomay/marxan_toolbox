import sys, os, arcgisscripting, traceback

def AddMsgAndPrint(message):
    gp.AddMessage(message)
    print message
    return 0 

gp = arcgisscripting.create()
gp.overwriteoutput = 1

try:
    # Get the parameters.
    gp.workspace = sys.argv[1]
    pattern = sys.argv[3]
    sr = sys.argv[2]
    #AddMsgAndPrint(pattern) ## TO DO: NOT WORKING
    #gp.workspace = r"C:\atom\python\shapes\test_shapes" ## TO DO: NOT WORKING

    # MANUAL FIX WORKS
    ## WHAT? IS IT BECAUSE sys.argv[3] and [2] were reversed? I fixed above 7/29/2011
    pattern = "*.shp"
    sr = "PROJCS['laborde_wcs_2000',GEOGCS['GCS_Tananarive_1925',DATUM['D_Tananarive_1925',SPHEROID['International_1924',6378388.0,297.0]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Hotine_Oblique_Mercator_Azimuth_Natural_Origin'],PARAMETER['False_Easting',1113136.3146],PARAMETER['False_Northing',2882900.7279],PARAMETER['Scale_Factor',0.9995],PARAMETER['Azimuth',18.9],PARAMETER['Longitude_Of_Center',46.43722917],PARAMETER['Latitude_Of_Center',-18.9],UNIT['Meter',1.0]]"

    # find only specified features or datasets
    if pattern == "*.shp":
        datasets = gp.ListFeatureClasses("", "POLYGON")
    elif pattern == "RASTER":
        datasets = gp.ListDatasets("", "RASTER")

    datasets.Reset()
    dataset = datasets.next()
    z = 0
    while dataset:
        z = z + 1
        dataset = datasets.next()

    i = 1
    datasets.Reset()
    dataset = datasets.next()
    while dataset:
        AddMsgAndPrint("Defining: " + dataset + ". (" + str(i) + " of " + str(z) + ")")
        gp.defineprojection_management(dataset,sr)
        i = i + 1
        dataset = datasets.next()
    AddMsgAndPrint("Done")    

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
    


    


    


print "done"

