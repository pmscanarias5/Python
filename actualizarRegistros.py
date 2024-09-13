import arcpy
# Especificar la tabla o capa dentro de PostGIS que deseas usar como datos de origen
datos_origen = r"C:\temp\106732118.sde\portalign.geofisica.idee_catalogo"

# Ruta al servicio de entidades en ArcGIS Enterprise
servicio_entidades = "https://certiserviciosgis2.ign.es/servicios/rest/services/RedSismica/Test_Terremotos_Hosteado/FeatureServer/0"
servicio_entidades_municipios= 'https://certiserviciosgis2.ign.es/servicios/rest/services/Hosted/municipios/FeatureServer/0'

feature_set = arcpy.FeatureSet()
#feature_set.load(servicio_entidades)

consulta = "1=1"  # Sin filtro, pero podrías agregar condiciones adicionales aquí
orden = "fecha DESC"  # Ordenar por fecha de manera descendente (para obtener la fecha más reciente)
feature_set.load(servicio_entidades + f"/query?where={consulta}&orderByFields={orden}&returnCountOnly=false&outFields=fecha&f=json")

#Recogemos la ultima fecha de terremoto recogida en el servicio de entidades
ultimaFecha = ''
# Recorrer las entidades obtenidas y tomar solo la primera (más reciente)
with arcpy.da.SearchCursor(feature_set, ["*"]) as cursor:
    for row in cursor:
        ultimaFecha = row[0]
        break
print(ultimaFecha)

#Realizamos consulta a la BBDD para quedarnos con todos los registros posteriores a la fecha
consulta = f"fecha > {ultimaFecha}"
feature_set2 = arcpy.FeatureSet()

nombreMunicipio =''
nombreProvincia = ''
nombreComunidad = ''
with arcpy.da.SearchCursor(datos_origen, '*', where_clause=f"fecha >= '{ultimaFecha}'") as cursor:
    # Crear una lista de geometrías para almacenar las entidades
    geometries = []
    for row in cursor:
        print(row[9][0])
        puntoGeometria = arcpy.PointGeometry(arcpy.Point(row[9][0],row[9][1]))

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
        geometries.append([puntoGeometria,evid,fecha,profundidad,magnitud,tipomagnitud,localizacion,intensidad, nombreMunicipio, nombreComunidad, nombreProvincia])

with arcpy.da.InsertCursor(servicio_entidades, ["SHAPE@", "evid", "fecha", "profundida", "magnitud", "tipomagnit","localizaci", "intensidad", "nameunit", "ccaa", "provincia"]) as cursor:
    for el in geometries:
        # Puedes proporcionar valores para campos adicionales si es necesario
        cursor.insertRow([el[0],el[1], el[2], el[3], el[4], el[5], el[6], el[7], el[8], el[9], el[10]])  # Usar 'i' como ID de ejemplo


print("Datos añadidos correctamente.")
