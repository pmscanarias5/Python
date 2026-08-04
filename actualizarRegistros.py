import arcpy
from datetime import datetime, timedelta
import time
import gc

nombreMunicipio =''
nombreProvincia = ''
nombreComunidad = ''

arcpy.SignInToPortal("https://certicontenidosgis2.ign.es/portal", 'portaladmin', 'portaladmin2022')
# Especificar la tabla o capa dentro de PostGIS que deseas usar como datos de origen
datos_origen = r"C:/temp/106732118.sde/portalign.geofisica.idee_catalogo"
# PARA COGER LA FECHA DE HACE UNA SEMANA

# # Restar una semana
una_semana_atras = (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d')
#
print("Hace una semana:", una_semana_atras)
# Ruta a la fuente de datos del servicio de entidades de terremotos y servicio de entidades de municipios:
gdb_workspace = r"//192.168.193.55/datos_c/sismologia.gdb"
gdbTerremotos = r"//192.168.193.55/datos_c/sismologia.gdb/terremotosHistoricos"#Se cambia en la GDB de clase de entidad
servicio_entidades_municipios= 'https://certiserviciosgis2.ign.es/servicios/rest/services/Hosted/municipios/FeatureServer/0'

#Campos para buscar en ambas tablas
fields = ['evid', 'fecha', 'profundidad', 'magnitud', 'tipomagnitud', 'localizacion', 'intensidad', 'revisionlocalizacion', 'revisionintensidad', "SHAPE@XY"]
listaEvidsTerremotos = []

#Se define la funcion que agrega o actualiza datos y será llamada posteriormente en función de si el dato ya existia o es nuevo
def actualizacion_AdicionTerremotos(servicio_entidades_municipios,row,geometries, nombreMunicipio, nombreProvincia, nombreComunidad):
    print('IMPORTANT: algo diferente o nuevo terremoto')
    with arcpy.da.SearchCursor(servicio_entidades_municipios, ['SHAPE@', 'nameunit', 'ccaa', 'provincia']) as cursorMunicipios:
        puntoGeometria = arcpy.PointGeometry(arcpy.Point(row[9][0], row[9][1]),spatial_reference=arcpy.SpatialReference(4258))
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
    print(evid)
    profundidad = row[2]
    magnitud = row[3]
    tipomagnitud = row[4]
    localizacion = row[5]
    intensidad = row[6]
     # Mirar el tema del shape porque no esta funcionando bien
    puntoGeometriaProyectado = puntoGeometria.projectAs(arcpy.SpatialReference(3857))
    geometries.append([puntoGeometriaProyectado, evid, fecha, profundidad, magnitud, tipomagnitud, localizacion, intensidad,nombreMunicipio, nombreComunidad, nombreProvincia])

def insertar_con_reintentos(gdb_path, campos, geometries, intentos=5, espera_inicial=5):
    """
    Inserta las filas de 'geometries' en gdb_path. Si arcpy no puede adquirir
    el bloqueo (al abrir, insertar o cerrar el cursor), reintenta con backoff
    creciente, sin repetir las filas que ya se insertaron con éxito.
    """
    pendientes = list(geometries)
    idx_evid = campos.index("evid")

    for intento in range(1, intentos + 1):
        if not pendientes:
            return

        insertados_este_intento = []
        try:
            with arcpy.da.InsertCursor(gdb_path, campos) as cursor:
                for el in pendientes:
                    cursor.insertRow(el)
                    insertados_este_intento.append(el)
                    print("Dato añadido correctamente:", el[idx_evid])
            return  # todo insertado sin errores

        except RuntimeError as e:
            pendientes = [el for el in pendientes if el not in insertados_este_intento]
            print(f"[Debug] Fallo tras insertar {len(insertados_este_intento)} filas en este intento. "
                  f"Quedan {len(pendientes)} pendientes.")

            if "bloqueo" in str(e).lower() or "lock" in str(e).lower():
                if intento == intentos:
                    raise RuntimeError(
                        f"No se pudo adquirir el bloqueo tras {intentos} intentos. "
                        f"Quedaron {len(pendientes)} registros sin insertar: "
                        f"{[el[idx_evid] for el in pendientes]}"
                    )
                espera = espera_inicial * intento
                print(f"[Aviso] Bloqueo al insertar (intento {intento}/{intentos}). Reintentando en {espera}s...")
                time.sleep(espera)
            else:
                raise

# ============================================================
# FASE 0: Identificar todos los registros VIGENTES en Origen (PostGIS)
#         y ELIMINAR de la GDB local los que ya no existan en origen
# ============================================================
origen_keys = set()
with arcpy.da.SearchCursor(datos_origen, ['evid'], where_clause="fecha >= date '{}'".format(una_semana_atras)) as cursor:
    for row in cursor:
        origen_keys.add(row[0])

registros_eliminados_gdb = 0
with arcpy.da.UpdateCursor(gdbTerremotos, ['evid'], where_clause="fecha >= date '{}'".format(una_semana_atras)) as cursorGDB:
    for rowGDB in cursorGDB:
        if rowGDB[0] not in origen_keys:
            cursorGDB.deleteRow()
            registros_eliminados_gdb += 1

print("Registros eliminados de la GDB local:", registros_eliminados_gdb)

# ============================================================
# FASE 1: LECTURA Y COMPARACIÓN (sin cursores de escritura abiertos)
# ============================================================

# 1a. Leemos la GDB
#     Este SearchCursor se cierra completamente aquí (con el "with") antes de pasar a la fase 2.
filasGDB = {}
with arcpy.da.SearchCursor(gdbTerremotos, fields, where_clause="fecha >= date '{}'".format(una_semana_atras)) as cursorGDB:
    for rowGDB in cursorGDB:
        evidGDB = rowGDB[0]
        filasGDB[evidGDB] = rowGDB

# 1b. Recorremos el origen (PostGIS) y decidimos, para cada terremoto, si:
#     - No existe en la GDB -> hay que insertarlo (se gestiona en la fase 3)
#     - Existe pero con diferencias -> hay que actualizarlo (se acumula en 'actualizaciones')
#     - Existe y es igual -> no se hace nada
actualizaciones = []  # aquí guardamos las filas de origen que requieren UPDATE

with arcpy.da.SearchCursor(datos_origen, '*', where_clause="fecha >= date '{}'".format(una_semana_atras)) as cursor:
    for row in cursor:
        evidOrigen = row[0]

        if evidOrigen in filasGDB:
            listaEvidsTerremotos.append(evidOrigen)
            rowGDB = filasGDB[evidOrigen]

            # Proyectamos la geometría de origen para poder comparar coordenadas en el mismo SR que la GDB (3857)
            puntoGeometria = arcpy.PointGeometry(arcpy.Point(row[9][0], row[9][1]), spatial_reference=arcpy.SpatialReference(4258))
            puntoGeometriaProyectado = puntoGeometria.projectAs(arcpy.SpatialReference(3857))

            # ---- ESTO es el "if <hay_diferencias>": la misma condición que ya tenías ----
            hay_diferencias = (
                rowGDB[0] != row[0] or
                rowGDB[1] != row[1] or
                rowGDB[2] != row[2] or
                rowGDB[3] != row[3] or
                rowGDB[4] != row[4] or
                rowGDB[5] != row[5] or
                rowGDB[6] != row[6] or
                str(rowGDB[9][0])[0:8] != str(puntoGeometriaProyectado[0].X)[0:8] or
                str(rowGDB[9][1])[0:8] != str(puntoGeometriaProyectado[0].Y)[0:8]
            )

            if hay_diferencias:
                print(rowGDB, ' | ', row)
                actualizaciones.append(row)  # guardamos la fila de ORIGEN completa, la procesaremos en fase 2
            else:
                print('todo igual')
        else:
            pass  # no está en la GDB -> se insertará en la fase 3


# ============================================================
# FASE 2: ACTUALIZACIÓN (un único UpdateCursor, ya sin SearchCursor abierto sobre gdbTerremotos)
# ============================================================
if actualizaciones:
    geometriesUpdate = []
    for row in actualizaciones:
        actualizacion_AdicionTerremotos(servicio_entidades_municipios, row, geometriesUpdate,
                                         nombreMunicipio, nombreProvincia, nombreComunidad)

    with arcpy.da.UpdateCursor(gdbTerremotos,["SHAPE@", "evid", "fecha", "profundidad", "magnitud", "tipomagnitud","localizacion", "intensidad", "nameunit", "ccaa", "provincia"],where_clause="fecha >= date '{}'".format(una_semana_atras)) as updateCursor:
        for rowUpdate in updateCursor:
            evidUpdate = rowUpdate[1]
            for geometriaUpdate in geometriesUpdate:
                evidGeometriaUpdate = geometriaUpdate[1]
                if evidUpdate == evidGeometriaUpdate:
                    print('rowUpdateNuevo -->', rowUpdate[0][0], ' | ', geometriaUpdate[0][0])
                    updateCursor.updateRow(geometriaUpdate)

#Ahora pasamos a la fase de insercion de datos en el caso necesario una vez ya realizado el bucle
geometries = [] #Reiniciamos el array para eliminar los valores si ha habido updates
with arcpy.da.SearchCursor(datos_origen, '*', where_clause="fecha >= date '{}'".format(una_semana_atras))as cursor:
    for row in cursor:
        evidRowPrevioInsertar = row[0]
        if evidRowPrevioInsertar not in listaEvidsTerremotos:
            print('Terremoto nuevo a actualizar')
            actualizacion_AdicionTerremotos(servicio_entidades_municipios,row,geometries,nombreMunicipio, nombreProvincia, nombreComunidad)

if geometries:
    campos_insert = ["SHAPE@XY", "evid", "fecha", "profundidad", "magnitud", "tipomagnitud",
                      "localizacion", "intensidad", "nameunit", "ccaa", "provincia"]
    insertar_con_reintentos(gdbTerremotos, campos_insert, geometries)


# ============================================================
# FASE FINAL: LIBERACIÓN DE BLOQUEOS Y COMPACTACIÓN
# ============================================================
print("Liberando memoria y bloqueos de la Geodatabase...")
arcpy.management.ClearWorkspaceCache(gdb_workspace)
gc.collect()

print("Compactando la Geodatabase...")
try:
    arcpy.management.Compact(gdb_workspace)
    print("Geodatabase compactada con éxito.")
except Exception as e:
    print(f"Error al compactar la Geodatabase: {e}")

print("Fin del script")