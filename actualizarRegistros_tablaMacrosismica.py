import arcpy
from datetime import datetime, timedelta
import arcgis
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection, FeatureSet, Feature
from arcgis.features import Feature


gis = GIS("https://certicontenidosgis2.ign.es/portal", "portaladmin", "portaladmin2022")
item_id = "9ec1a85b1c1d40d6a6b2e6336e4e6549"  # ID del servicio hosted
item = gis.content.get(item_id)
flc = FeatureLayerCollection.fromitem(item)
# flc.properties
table = flc.tables[0]  # tabla standalone

arcpy.SignInToPortal("https://certicontenidosgis2.ign.es/portal", 'portaladmin', 'portaladmin2022')
# Especificar la tabla o capa dentro de PostGIS que deseas usar como datos de origen
datos_origen = r"C:/temp/106732118.sde/portalign.geofisica.munimacro"
# PARA COGER LA FECHA DE HACE UNA SEMANA

# # Restar una semana
una_semana_atras = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d')
#
print("Hace una semana:", una_semana_atras)
# Ruta a la fuente de datos del servicio de entidades de terremotos y servicio de entidades de municipios:
gdbTerremotos = r"//192.168.193.55/datos_c/sismologia.gdb/tablaIntensidad"
#Campos para buscar en ambas tablas
fields = ['evid', 'codine', 'localizacion', 'intensidad', 'Iddate']
listaEvidsTerremotos = []

#Se define la funcion que agrega o actualiza datos y será llamada posteriormente en función de si el dato ya existia o es nuevo
def actualizacion_AdicionTerremotos(row,geometries):
    print('IMPORTANT: algo diferente o nuevo terremoto')
    evid = row[0]
    localizacion = row[1]
    codine = row[2]
    iddate = row[6]
    print(evid+localizacion)

    intensidad = row[3]
    geometries.append([evid, localizacion, codine, iddate, intensidad])


#Se recorren los terremotos de la ultima semana en nuestra GDB
with arcpy.da.SearchCursor(gdbTerremotos, fields, where_clause="Iddate >= date '{}'".format(una_semana_atras)) as cursorGDB:
    # Crear una lista de geometrias para almacenar las entidades
    geometries = []
    for rowGDB in cursorGDB:
        evidGDB = rowGDB[0]
        localizacionGDB = rowGDB[2]

        #Se pasa a recorrer al mismo tiempo que los terremotos de la GDB los del postgis para ver si hay diferencias y en el caso de haberlas actualizar la GDB
        with arcpy.da.SearchCursor(datos_origen, '*', where_clause="lddate >= date '{}'".format(una_semana_atras)) as cursor:
        # Crear una lista de geometrías para almacenar las entidades
            geometries = []
            for row in cursor:
                evidOrigen = row[0]
                localizacionOrigen = row[1]
                print('Antes de meter a la lista: EvidGDB: ', evidGDB, ' | EvidOrigen: ', evidOrigen,
                      ' || Localizacion GDB: ', localizacionGDB, ' | Localizacion origen: ', localizacionOrigen)
                if evidGDB == evidOrigen and localizacionGDB == localizacionOrigen:
                    print('Entra a meter a la lista: EvidGDB: ', evidGDB, ' | EvidOrigen: ', evidOrigen, ' || Localizacion GDB: ',localizacionGDB, ' | Localizacion origen: ', localizacionOrigen)
                    listaEvidsTerremotos.append(evidOrigen + localizacionOrigen) #Esta lista va a servir para verificar que los terremotos están en ambas tablas, sino pasamos a un insert
                    #intensidadFloat = float(rowGDB[3].replace(",", "."))

                    if rowGDB[0] != row[0] or rowGDB[1] != row[2] or rowGDB[2] != row[1] or rowGDB[3] != row[3] or rowGDB[4].date() != row[6].date():
                        print(rowGDB, ' | ', row)
                        #Si hay un terremoto con el mismo codigo identificativo pero con alguna diferencia se actualiza la entidad:
                        actualizacion_AdicionTerremotos(row,geometries)
                        #Aqui actualizamos GDB
                        with arcpy.da.UpdateCursor(gdbTerremotos, ["evid", "localizacion", "codine", "Iddate", "intensidad"],where_clause="Iddate >= date '{}'".format(una_semana_atras)) as updateCursor:
                            for rowUpdate in updateCursor:
                                evidUpdate = rowUpdate[0]
                                for geometriaUpdate in geometries:
                                    evidGeometriaUpdate = geometriaUpdate[0]
                                    if evidUpdate == evidGeometriaUpdate:
                                        rowUpdate = geometriaUpdate
                                        updateCursor.updateRow(rowUpdate)
                                        #Aqui actualizamos GDBelse:
                                        pass
                        # Aqui actualizamos Servicio
                        features_to_update = []
                        for f in geometries:
                            where_clause = f"evid = '{f[0]}' AND codine = '{f[2]}'"
                            query_result = table.query(where=where_clause, out_fields="objectid", return_geometry=False)
                            objectid = query_result.features[0].attributes["objectid"]  # obtenemos solo el OBJECTID

                            registro_actualizado = Feature(
                                attributes={
                                    "objectid": objectid,  # obligatorio para actualizar
                                    "evid": f[0],
                                    "intensidad": f[4],  # nuevo valor
                                    "codine": f[2],
                                    "localizacion": f[1],
                                    "iddate": f[3]  # actualizar fecha/hora
                                    # si quieres mantener evid y codine en la actualización, añádelos también
                                }
                            )
                            features_to_update.append(registro_actualizado)

                        # Actualizar todos los registros encontrados en una sola llamada
                        result = table.edit_features(updates=features_to_update)
                    else:
                        print('todo igual')
                else:
                    pass
                    #print('Distinto evid')
#Ahora pasamos a la fase de insercion de datos en el caso necesario una vez ya realizado el bucle
geometries = [] #Reiniciamos el array para eliminar los valores si ha habido updates

with arcpy.da.SearchCursor(datos_origen, '*', where_clause=" lddate >= TIMESTAMP '{}'".format(una_semana_atras))as cursor:
    for row in cursor:
        evidRowPrevioInsertar = row[0] + row[1]
        print('Lista de evids ya registrados: ')
        print(listaEvidsTerremotos)
        print(' | Este evid: '+ evidRowPrevioInsertar)
        if evidRowPrevioInsertar not in listaEvidsTerremotos:
            print('Intensidad nueva a actualizar')
            actualizacion_AdicionTerremotos(row,geometries)

#Se modifica base de datos
with arcpy.da.InsertCursor(gdbTerremotos, ["evid", "localizacion", "codine", "Iddate", "intensidad"]) as cursor:
    for el in geometries:
        # Puedes proporcionar valores para campos adicionales si es necesario

        cursor.insertRow([el[0],el[1], el[2], el[3], el[4]])  # Usar 'i' como ID de ejemplo
        print("Dato añadido correctamente.")

#Se modifica servicio
features_to_update = []
for f in geometries:
    #where_clause = f"evid = '{f[0]}' AND codine = {f[2]}"
    #query_result = table.query(where=where_clause, out_fields="OBJECTID", return_geometry=False)
    #objectid = query_result.features[0].attributes["OBJECTID"]  # obtenemos solo el OBJECTID

    registro_actualizado = Feature(
        attributes={
            #"OBJECTID": objectid,  # obligatorio para actualizar
            "evid": f[0],
            "intensidad": f[4],  # nuevo valor
            "codine": f[2],
            "localizacion": f[1],
            "iddate": f[3]  # actualizar fecha/hora
            # si quieres mantener evid y codine en la actualización, añádelos también
        }
    )
    features_to_update.append(registro_actualizado)

# Actualizar todos los registros encontrados en una sola llamada
if len(geometries)> 0:
    result = table.edit_features(adds=features_to_update)

print("Fin del script")