import arcpy
import os
arcpy.env.overwriteOutput = True
gdbSalida = r'D:\OneDrive - MITMA\Documentos\ArcGIS\Projects\MyProject6\MyProject6.gdb'
arcpy.env.workspace = gdbSalida

rutaSHPSMundo = r'D:\OneDrive - MITMA\Escritorio\Proyectos\geosapiens\juegoRelieve\Relieve España_Act20241122\Relieve España'
salida = r'D:\OneDrive - MITMA\Escritorio\Proyectos\geosapiens\juegoRelieve\relieveFinal\espana_comunidades'
arcpy.env.workspace = rutaSHPSMundo
listaSHP = arcpy.ListFeatureClasses()
print(listaSHP)

for archivo in listaSHP:
    print(archivo)
    cordillerasMundo = arcpy.management.SelectLayerByAttribute(archivo, 'NEW_SELECTION', "tipo not in('Cordillera', 'Sierra')")
    arcpy.env.workspace = salida
    #arcpy.management.CopyFeatures(cordillerasMundo, archivo[:-4])
    arcpy.conversion.FeaturesToJSON(cordillerasMundo, archivo[:-4] + '.geojson', geoJSON=True)
    arcpy.env.workspace = rutaSHPSMundo