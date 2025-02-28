import arcpy
import os


def actualizar_gdb(tipo_proyecto, gdb_proyecto, gdb_nuevos_datos):
    arcpy.env.workspace = gdb_proyecto
    feature_classes = arcpy.ListFeatureClasses()

    # Renombrar las clases de entidad agregando el sufijo "_old"
    renombrados = {}
    for fc in feature_classes:
        if tipo_proyecto=='Poblaciones' and fc == 'capProv':
            continue

        new_name = f"{fc}_old"
        arcpy.management.Rename(fc, new_name)
        renombrados[fc] = new_name

    # Copiar nuevas clases de entidad desde GDB2
    arcpy.env.workspace = gdb_nuevos_datos
    nuevas_feature_classes = arcpy.ListFeatureClasses()
    for fc in nuevas_feature_classes:
        if tipo_proyecto=='Poblaciones' and fc == 'capProv':
            continue

        try:
            arcpy.AddMessage(f"Copiando {fc} a {gdb_proyecto}")
            arcpy.conversion.FeatureClassToGeodatabase(fc, gdb_proyecto)
        except Exception as e:
            arcpy.AddMessage(f"Error copiando {fc}: {e}")

    # Restaurar workspace a GDB1
    arcpy.env.workspace = gdb_proyecto

    # Copiar índices de los _old a las nuevas clases de entidad si son índices de atributos y existen en la clase nueva
    for old_fc, new_fc in renombrados.items():
        new_fc_path = os.path.join(gdb_proyecto, old_fc)  # Nueva clase de entidad
        old_fc_path = os.path.join(gdb_proyecto, new_fc)  # La renombrada con _old

        if arcpy.Exists(new_fc_path):
            indices = arcpy.ListIndexes(old_fc_path)
            for index in indices:
                if index.name != 'FDO_OBJECTID' and index.name != 'FDO_SHAPE':
                    camposIndice = []
                    for campo in index.fields:
                        camposIndice.append(campo.name)
                    arcpy.AddMessage(f"Añadiendo índice para {index.name} y los campos {camposIndice}")
                    arcpy.management.AddIndex(new_fc_path, camposIndice, index.name, 'NON_UNIQUE', 'ASCENDING')

    # Actualizar las fuentes de datos en los mapas del proyecto
    aprx = arcpy.mp.ArcGISProject('CURRENT')
    for m in aprx.listMaps():
        if tipo_proyecto == "Poblaciones" and m.name == "Capitales Provincia":
            continue  # No actualizar en "Capitales Provincia" si el tipo es "Poblaciones"

        for layer in m.listLayers():
            # if layer.supports('DATASOURCE'):  # Asegurar que es una capa con fuente de datos
            for old_fc, new_fc in renombrados.items():
                    # if new_fc in layer.dataSource:  # Si la capa apunta a una de las renombradas
                new_fc_path = os.path.join(gdb_proyecto, old_fc)
                if layer.dataSource[0:-4] == new_fc_path:
                    updateConnection = layer.connectionProperties
                    updateConnection['dataset'] = updateConnection['dataset'][0:-4]
                    layer.updateConnectionProperties(layer.connectionProperties, updateConnection, validate=False)
                    arcpy.AddMessage(f"Se actualiza{layer} con la proveniente de {new_fc_path}")

    arcpy.AddMessage("Proceso completado correctamente")


if __name__ == "__main__":
    tipo_proyecto = arcpy.GetParameterAsText(0)  # Nuevo parámetro desplegable con opciones RT o Poblaciones
    gdb_proyecto = arcpy.GetParameterAsText(1)
    gdb_nuevos_datos = arcpy.GetParameterAsText(2)
    actualizar_gdb(tipo_proyecto, gdb_proyecto, gdb_nuevos_datos)