import arcpy
arcpy.CheckOutExtension("Spatial")
# Rutas de entrada
arcpy.env.workspace = 'D:\OneDrive - MITMA\Documentos\ArcGIS\Projects\MyProject12\MyProject12.gdb'
arcpy.env.overwriteOutput = True
wcs_url = "https://servicios.idee.es/wcs-inspire/mdt?"  # URL del servicio WCS
layer_wcs = "Elevacion25830_25"  # Nombre de la capa en el WCS
polilinea_fc = "gices_faltaZ"  # Feature Class de entrada
puntos_fc = "polilinea_puntos"  # Salida intermedia
polilinea_z_fc = "polilineaConzValor"  # Salida final

# Crear una copia de la capa original para preservar atributos
arcpy.management.CopyFeatures(polilinea_fc, polilinea_z_fc)

# # 1️⃣ Convertir cada polilínea en puntos individuales
# arcpy.management.FeatureVerticesToPoints(polilinea_fc, puntos_fc, "ALL")
#
# # 2️⃣ Extraer valores de elevación desde el WCS
# puntos_con_z_fc = "C:/ruta/a/tu.gdb/puntos_con_z"
# arcpy.sa.ExtractValuesToPoints(puntos_fc, wcs_raster, puntos_con_z_fc)

# 3️⃣ Crear una nueva capa con geometría Z
# arcpy.management.AddField('puntos_con_z', "Z", "DOUBLE")  # Agregar campo Z
# arcpy.CalculateField_management('puntos_con_z', "Z", "!RASTERVALU!", "PYTHON3")

# 4️⃣ Reconstruir polilíneas con la coordenada Z y mantener atributos
# arcpy.management.EnableZ(polilinea_z_fc)
with arcpy.da.UpdateCursor(polilinea_z_fc, ["SHAPE@", "OID@"]) as poly_cursor:
    for poly_row in poly_cursor:
        oid = poly_row[1]
        new_array = arcpy.Array()

        # Obtener puntos asociados a esta polilínea
        with arcpy.da.SearchCursor('puntosConCordenadaZ', ["SHAPE@"], f"OBJECTID = {oid}") as point_cursor:
            for point_row in point_cursor:
                pt = point_row[0]  # Geometría del punto
                if pt and pt.firstPoint:
                    new_array.add(arcpy.Point(pt.firstPoint.X, pt.firstPoint.Y, pt.firstPoint.Z))

        # Crear nueva polilínea con Z y actualizar la entidad
        if new_array.count > 1:  # Evita crear geometrías vacías o con un solo punto
            poly_row[0] = arcpy.Polyline(new_array, has_z=True)
            poly_cursor.updateRow(poly_row)

print("✅ Polilíneas con Z generadas correctamente manteniendo atributos.")
