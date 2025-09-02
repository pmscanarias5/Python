import arcpy

# Ruta de la capa de puntos
arcpy.env.workspace = 'D:\OneDrive - MITMA\Documentos\ArcGIS\Projects\MyProject12\MyProject12.gdb'
arcpy.env.overwriteOutput = True
puntos_fc= 'puntosConCordenadaZ'
# Habilitar Z en la capa si no lo tiene
# arcpy.management.EnableZ(puntos_fc)

# Actualizar los puntos con el valor Z del campo
with arcpy.da.UpdateCursor(puntos_fc, ["SHAPE@", "Z"]) as cursor:
    for row in cursor:
        punto = row[0]  # Geometría original
        valor_z = row[1] if row[1] is not None else 0  # Z desde el campo, por defecto 0

        # Crear un nuevo punto con la coordenada Z
        new_point = arcpy.Point(punto.centroid.X, punto.centroid.Y, valor_z)
        row[0] = arcpy.PointGeometry(new_point, has_z=True)

        cursor.updateRow(row)

print("✅ Se ha asignado la coordenada Z a la capa de puntos correctamente.")