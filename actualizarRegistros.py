import arcpy
from datetime import datetime, timedelta

nombreMunicipio =''
nombreProvincia = ''
nombreComunidad = ''

arcpy.SignInToPortal("https://certicontenidosgis2.ign.es/portal", 'portaladmin', 'portaladmin2022')
# Especificar la tabla o capa dentro de PostGIS que deseas usar como datos de origen
datos_origen = r"C:\temp\106732118.sde\portalign.geofisica.idee_catalogo"
# PARA COGER LA FECHA DE HACE UNA SEMANA

# # Restar una semana
una_semana_atras = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d')
#
print("Hace una semana:", una_semana_atras)
# Ruta al servicio de entidades en ArcGIS Enterprise
gdbTerremotos = r"//192.168.193.55/datos_c/sismologia.gdb/terremotosHistoricos"
servicio_entidades_municipios= 'https://certiserviciosgis2.ign.es/servicios/rest/services/Hosted/municipios/FeatureServer/0'

#Campos para buscar en ambas tablas
fields = ['evid', 'fecha', 'profundidad', 'magnitud', 'tipomagnitud', 'localizacion', 'intensidad', 'revisionlocalizacion', 'revisionintensidad', "SHAPE@XY"]
with arcpy.da.SearchCursor(gdbTerremotos, fields, where_clause=f"fecha >= date '{una_semana_atras}'") as cursorGDB:
    # Crear una lista de geometrías para almacenar las entidades
    geometries = []



    for rowGDB in cursorGDB:
        evidGDB = rowGDB[0]
        print(evidGDB)
        with arcpy.da.SearchCursor(datos_origen, '*', where_clause=f"fecha >= '{una_semana_atras}'") as cursor:
        # Crear una lista de geometrías para almacenar las entidades

            geometries = []
            for row in cursor:
                evidPostGIS = row[0]
                puntoGeometria = arcpy.PointGeometry(arcpy.Point(row[9][0], row[9][1]),spatial_reference=arcpy.SpatialReference(4258))  # Mirar el tema del shape porque no esta funcionando bien
                puntoGeometriaProyectado = puntoGeometria.projectAs(arcpy.SpatialReference(3857))
                if evidGDB == evidPostGIS:
                    if rowGDB[0] != row[0] or rowGDB[1] != row[1] or rowGDB[2] != row[2] or rowGDB[3] != row[3] or rowGDB[4] != row[4] or rowGDB[5] != row[5] or rowGDB[6] != row[6] and str(rowGDB[9][0])[0:10] != str(puntoGeometriaProyectado[0].X)[0:10] and str(rowGDB[9][1])[0:10] != str(puntoGeometriaProyectado[0].Y)[0:10]:
                        print('IMPORTANT: algo diferente')
                        with arcpy.da.SearchCursor(servicio_entidades_municipios, ['SHAPE@', 'nameunit', 'ccaa', 'provincia']) as cursorMunicipios:
                            for municipio in cursorMunicipios:
                                geometriaMuni = municipio[0]
                                nombreMuni = municipio[1]
                                nombreCCAA = municipio[2]
                                nombreProv = municipio[3]

                                if geometriaMuni.contains(puntoGeometria):
                                    nombreMunicipio = nombreMuni
                                    nombreProvincia = nombreProv
                                    nombreComunidad = nombreCCAA
                                    break
                        evid = row[0]
                        fecha = row[1]
                        print(fecha)
                        profundidad = row[2]
                        magnitud = row[3]
                        tipomagnitud = row[4]
                        localizacion = row[5]
                        intensidad = row[6]
                        geometries.append([puntoGeometriaProyectado,evid,fecha,profundidad,magnitud,tipomagnitud,localizacion,intensidad, nombreMunicipio, nombreComunidad, nombreProvincia])
                    else:
                        print('todo igual')
                else:
                    print('no coincide evid')
#with arcpy.da.InsertCursor(gdbTerremotos, ["SHAPE@XY", "evid", "fecha", "profundidad", "magnitud", "tipomagnitud","localizacion", "intensidad", "nameunit", "ccaa", "provincia"]) as cursor:
    #for el in geometries:
        #print(el[0][0])
        # Puedes proporcionar valores para campos adicionales si es necesario
       # cursor.insertRow([el[0],el[1], el[2], el[3], el[4], el[5], el[6], el[7], el[8], el[9], el[10]])  # Usar 'i' como ID de ejemplo


print("Datos añadidos correctamente.")
