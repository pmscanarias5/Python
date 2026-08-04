import arcpy
from datetime import datetime, timedelta
import arcgis
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection, Feature

# 1. Conexiones e Inicialización
gis = GIS("https://contenidosgis2.ign.es/portal", "portaladmin", "portaladmin2022")
item_id = "51a2d226852444928d1fff60c9fff805"
item = gis.content.get(item_id)
flc = FeatureLayerCollection.fromitem(item)
table = flc.tables[0]  # Tabla standalone hosted

arcpy.SignInToPortal("https://contenidosgis2.ign.es/portal", 'portaladmin', 'portaladmin2022')

datos_origen = r"C:/temp/106732118.sde/portalign.geofisica.munimacro"
gdbTerremotos = r"//192.168.192.125/datos_c/sismologia.gdb/tablaIntensidad"

# Rango de fechas (5 semanas atrás)
una_semana_atras = (datetime.now() - timedelta(weeks=3)).strftime('%Y-%m-%d')
print("Procesando datos desde:", una_semana_atras)

fields = ['evid', 'codine', 'localizacion', 'intensidad', 'Iddate']
listaEvidsTerremotos = []


def formatear_intensidad(val):
    """Convierte '1,5' a float 1.5 para la REST API de ArcGIS."""
    if val is None:
        return None
    if isinstance(val, str):
        val = val.replace(',', '.')
    return float(val)

# ---------------------------------------------------------
# FASE 0: Identificar todos los registros VIGENTES en Origen (PostGIS)
# ---------------------------------------------------------
origen_keys = set()
with arcpy.da.SearchCursor(datos_origen, ['evid', 'localidad', 'codine', 'int', 'lddate'],
                           where_clause=f"lddate >= TIMESTAMP '{una_semana_atras}'") as cursor:
    for row in cursor:
        # Clave única compuesta (evid + localizacion)
        origen_keys.add(f"{row[0]}_{row[1]}")

# ---------------------------------------------------------
# FASE 1: Sincronizar PostGIS -> GDB Local
# ---------------------------------------------------------

# 1.1 ELIMINAR de la GDB local si el registro fue borrado en origen
registros_eliminados_gdb = 0
with arcpy.da.UpdateCursor(gdbTerremotos, ['evid', 'localizacion'], where_clause=f"Iddate >= date '{una_semana_atras}'") as cursorGDB:
    for rowGDB in cursorGDB:
        keyGDB = f"{rowGDB[0]}_{rowGDB[1]}"
        if keyGDB not in origen_keys:
            cursorGDB.deleteRow()
            registros_eliminados_gdb += 1

print(f"Registros eliminados de la GDB local: {registros_eliminados_gdb}")

# 1.2 ACTUALIZAR registros existentes en GDB local si hay diferencias
geometries_a_procesar = []

with arcpy.da.SearchCursor(gdbTerremotos, fields, where_clause=f"Iddate >= date '{una_semana_atras}'") as cursorGDB:
    for rowGDB in cursorGDB:
        evidGDB, codineGDB, localizacionGDB, intensidadGDB, iddateGDB = rowGDB

        with arcpy.da.SearchCursor(datos_origen, '*',
                                   where_clause=f"lddate >= date '{una_semana_atras}'") as cursorOrigen:
            for row in cursorOrigen:
                evidOrigen = row[0]
                localizacionOrigen = row[1]

                if evidGDB == evidOrigen and localizacionGDB == localizacionOrigen:
                    listaEvidsTerremotos.append(evidOrigen + localizacionOrigen)

                    # Si detectamos diferencias con el origen, preparamos actualización de GDB
                    if (rowGDB[0] != row[0] or rowGDB[1] != row[2] or rowGDB[2] != row[1] or
                            rowGDB[3] != row[3] or rowGDB[4].date() != row[6].date()):
                        geometries_a_procesar.append([row[0], row[1], row[2], row[6], row[3]])

# Actualizar en GDB local los modificados
if geometries_a_procesar:
    with arcpy.da.UpdateCursor(gdbTerremotos, ["evid", "localizacion", "codine", "Iddate", "intensidad"],
                               where_clause=f"Iddate >= date '{una_semana_atras}'") as updateCursor:
        for rowUpdate in updateCursor:
            evidUpdate = rowUpdate[0]
            for geo in geometries_a_procesar:
                if evidUpdate == geo[0]:
                    updateCursor.updateRow(geo)

# ---------------------------------------------------------
# FASE 2: Inserción de Nuevos Registros en GDB Local
# ---------------------------------------------------------
nuevos_para_gdb = []

with arcpy.da.SearchCursor(datos_origen, '*', where_clause=f"lddate >= TIMESTAMP '{una_semana_atras}'") as cursor:
    for row in cursor:
        evidKey = row[0] + row[1]
        if evidKey not in listaEvidsTerremotos:
            print(f"Nuevo registro detectado: {evidKey}")
            nuevos_para_gdb.append([row[0], row[1], row[2], row[6], row[3]])

if nuevos_para_gdb:
    with arcpy.da.InsertCursor(gdbTerremotos, ["evid", "localizacion", "codine", "Iddate", "intensidad"]) as cursor:
        for el in nuevos_para_gdb:
            cursor.insertRow([el[0], el[1], el[2], el[3], el[4]])
            print("Dato añadido a GDB local.")

# ---------------------------------------------------------
# FASE 3: Sincronización Inteligente GDB -> Servicio (ADDS vs UPDATES)
# ---------------------------------------------------------
print("Comprobando sincronización con el servicio hosted...")

features_to_add = []
features_to_update = []
objectids_to_delete = []
# 3.1 Consultar todos los registros vigentes en el servicio hosted para el periodo
query_servicio = table.query(where=f"iddate >= date '{una_semana_atras}'", out_fields="objectid,evid,localizacion,codine", return_geometry=False)

servicio_dict = {}
for feat in query_servicio.features:
    obj_id = feat.attributes["objectid"]
    evid_s = feat.attributes.get("evid")
    loc_s = feat.attributes.get("localizacion")
    key_servicio = f"{evid_s}_{loc_s}"
    servicio_dict[key_servicio] = obj_id

# 3.2 Determinar cuáles hay que ELIMINAR en el servicio (existen en el servicio pero no en origen_keys)
for key_serv, obj_id in servicio_dict.items():
    if key_serv not in origen_keys:
        objectids_to_delete.append(str(obj_id))

# 3.3 Procesar AÑADIDOS / ACTUALIZACIONES desde la GDB local ya al día
with arcpy.da.SearchCursor(gdbTerremotos, fields, where_clause=f"Iddate >= date '{una_semana_atras}'") as cursorGDB:
    for rowGDB in cursorGDB:
        evid, codine, localizacion, intensidad, iddate = rowGDB
        intensidad_clean = formatear_intensidad(intensidad)
        key_gdb = f"{evid}_{localizacion}"

        attr_dict = {
            "evid": evid,
            "intensidad": intensidad_clean,
            "codine": codine,
            "localizacion": localizacion,
            "iddate": iddate
        }

        if key_gdb in servicio_dict:
            # Existe en el servicio -> Se ACTUALIZA
            attr_dict["objectid"] = servicio_dict[key_gdb]
            features_to_update.append(Feature(attributes=attr_dict))
        else:
            # Falta en el servicio -> Se AÑADE
            features_to_add.append(Feature(attributes=attr_dict))

# 3.4 Aplicar cambios finales en lote al servicio hosted
deletes_str = ",".join(objectids_to_delete) if objectids_to_delete else None

if features_to_add or features_to_update or deletes_str:
    res = table.edit_features(adds=features_to_add, updates=features_to_update, deletes=deletes_str)
    print(f"Servicio sincronizado -> Añadidos: {len(features_to_add)} | Actualizados: {len(features_to_update)} | Eliminados: {len(objectids_to_delete)}")
else:
    print("El servicio hosted ya estaba totalmente sincronizado.")

print("Fin del script")