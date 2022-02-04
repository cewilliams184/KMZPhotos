#KMLPhotosCombined
#Author: Chantel Williams
#Dec 2020

""" Objective: Adds photos taken in field to photopoint locations in a
    KML/KMZ file for delivery to client. The photo point taken with the
    gps unit and the coordinates of the photo must be within a distance defined by the user. """

#Example Inputs: D:\GIS\Python\KMLPhotos True D:\GIS\Python\KMLPhotos\Shapefiles\PhotoPoint.shp D:\GIS\Python\KMLPhotos\GPSphotos D:\GIS\Python\KMLPhotos\Scratch KMZwithPhotos.kmz 10 Join_Count,TARGET_FID,OBJECTID_1,Datafile,BUFF_DIST,ORIG_FID,Shape_Leng,Shape_Area

#import system modules
import sys, arcpy, os, csv
from  os import path
arcpy.env.overwriteOutput = True

#Set workspace
workplace = arcpy.env.workspace = arcpy.GetParameterAsText(0)


#User Inputs
PhotoPoints = arcpy.GetParameterAsText(1)#points collected with gps units
Path2Photos = arcpy.GetParameterAsText(3) # photos taken with geospatial information
OutputFilePath = arcpy.GetParameterAsText(4)
KMZOutputName = arcpy.GetParameterAsText(5) #KMZ output name
JoinBuffer = arcpy.GetParameterAsText(6) #the distance from gps point that the location where the photo was taken will be searched
Fields2Remove = arcpy.GetParameterAsText(7) # list of fields that should be removed from final kml file. Values should be seperated by commas
GPSPointsTaken = arcpy.GetParameterAsText(2) #Ask if gps points were collected along with photos with geospatial information or not; if no points will not be buffered or joined
Export2KMZ = arcpy.GetParameterAsText(8) #Ask if the user wants the map exported to a KMZ.

#checks to see if gdb exists. If it exists, it's deleted and a new gdb is created
GDB = os.path.join(OutputFilePath, "KMLPhotos.gdb")
if arcpy.Exists(GDB):
    arcpy.Delete_management(GDB)
#create gdb in workplace
GDB = arcpy.CreateFileGDB_management(OutputFilePath, "KMLPhotos.gdb")


#Outputs
Photo2Points= os.path.join(str(GDB), "Photo2Points") # Points created from photo's lat/longs
PhotoText= os.path.join(OutputFilePath, "PhotoText.csv") #csv used to join photos file path with photo points collected in field
JoinedPhotoPoints= os.path.join(OutputFilePath, "JoinedPhotoPoints.shp") # spatially joined photo points and points created from photos lat/long output which contains all attributes from both files.
JoinedPhotosCSV= os.path.join(OutputFilePath,"JoinedPhotos.csv") # csv of joined photo points attribute table


#Define function printArc; which shows message in Interactive Window and IDE
def printArc(message):
    '''Print messge for Script Tool and standard output'''
    print (message)
    arcpy.AddMessage(message)

#Convert geotagged photos to points
arcpy.GeoTaggedPhotosToPoints_management(Path2Photos, Photo2Points)

#export attributes to csv
arcpy.CopyRows_management(Photo2Points,PhotoText)

# if gps points were taken.... from Buffer photos to spatial join
if GPSPointsTaken == True:
    #Buffer Photo Points (points collected with a gps unit by 5 ft in order to perform spatial join between point taken by the gps unit and point created from photo's coordinate data)
    GPSPhotoBuffer = os.path.join(str(GDB), "GPSPhotoBuffer")
    arcpy.Buffer_analysis(PhotoPoints, GPSPhotoBuffer, "{0} Feet".format(JoinBuffer)) 

    #Do a spatial join to associate Photo points (Collected in the field) with points created from photo data
    arcpy.SpatialJoin_analysis(Photo2Points, GPSPhotoBuffer, JoinedPhotoPoints, join_type="KEEP_COMMON")

else:
    JoinedPhotoPoints= Photo2Points

#Add field with that will hold html code to display image in the kmz
arcpy.management.AddField(JoinedPhotoPoints, 'Image', 'TEXT', field_length=254)

#Delete extra field not needed in final kml file
if GPSPointsTaken == True:
    RemovedFields = Fields2Remove.split(",")
    for i in RemovedFields:
        field ="!{0}!".format(i)
        arcpy.management.DeleteField(JoinedPhotoPoints, i)
else:
    printArc('No Fields to remove')

#Field calculate with html code
htmlcodeA = expression="""' <img style="max-width:500px;" src="{0}"><html xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:msxsl="urn:schemas-microsoft-com:xslt"> '.format(!Name!)"""


# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "JoinedPhotoPoints"
arcpy.CalculateField_management(in_table=JoinedPhotoPoints, field="Image", expression=htmlcodeA, expression_type="PYTHON_9.3", code_block="")



#Check if script is run inside arcmap or stand alone script
if os.path.splitext(os.path.basename(sys.executable))[0].lower() !='python':
    #run mapping module
    mxd = arcpy.mapping.MapDocument('CURRENT')
    #List data frame
    for df in arcpy.mapping.ListDataFrames(mxd):
        dfs=df.name
        printArc(df.name)
        
    #Create PhotoPoint spatially joined layer object
    PhotosJoinlyrObj= arcpy.mapping.Layer(JoinedPhotoPoints)
    printArc(PhotosJoinlyrObj)
        
    #Export layer to csv
    arcpy.CopyRows_management(JoinedPhotoPoints, JoinedPhotosCSV)

    #KMZ output name and filepath combined
    KMZfileName = str(KMZOutputName) + '.kmz'
    KMZOutput = os.path.join(OutputFilePath, KMZfileName)
  
    #Add layer to the map
    arcpy.mapping.AddLayer(df, PhotosJoinlyrObj)

    #Save Map so layer will be added to kmz export
    mxd.save()
    mxdname = str(mxd.filePath)
# Option to export map to kmz
if Export2KMZ == True:
    #Export mxd to KMZ -> Execute MapToKML
    #Use the ListFiles method to identify all layer files in workspace
    for mxd in arcpy.ListFiles('*.mxd'):
        #Set Local Variables
        dataFrame = 'Layers'
        clamped = 'ABSOLUTE'
        for scale in range (10000, 30001, 10000):
            #Execute MapToKML
            arcpy.MapToKML_conversion(mxdname, dataFrame, KMZOutput, ignore_zvalue=clamped)         
    else:
        printArc('You are in a script:)')

else:
    printArc('The map is ready to be modified before export to KMZ')
