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
    clipshp = sys.argv[2]
    outfolder = sys.argv[3]

    # find only specified features or datasets
    datasets = gp.ListRasters("", "GRID")
    AddMsgAndPrint("Counting...")
    datasets.Reset()
    dataset = datasets.next()
    z = 0
    while dataset:
        z = z + 1
        dataset = datasets.next()
    AddMsgAndPrint("Found " + str(z) + " grids")

    i = 1
    datasets.Reset()
    dataset = datasets.next()
    while dataset:
        AddMsgAndPrint("Clipping: " + dataset + ". (" + str(i) + " of " + str(z) + ")")
        gp.ExtractByMask_sa(dataset, clipshp, outfolder + os.sep + dataset)
        i = i + 1
        dataset = datasets.next()
    AddMsgAndPrint("Done with all grids")    

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