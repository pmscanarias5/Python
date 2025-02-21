import arcpy


def delete_old_feature_classes(gdb_path):
    """
    Elimina todas las clases de entidad en la geodatabase que terminan con '_old'.

    :param gdb_path: Ruta de la geodatabase.
    """
    arcpy.env.workspace = gdb_path

    # Obtener todas las clases de entidad en la GDB
    feature_classes = arcpy.ListFeatureClasses()

    if not feature_classes:
        arcpy.AddMessage("No se encontraron clases de entidad en la GDB.")
        return

    # Filtrar las clases de entidad que terminan en '_old'
    old_feature_classes = [fc for fc in feature_classes if fc.endswith('_old')]

    if not old_feature_classes:
        arcpy.AddMessage("No hay clases de entidad que terminen en '_old'.")
        return

    # Eliminar las clases de entidad seleccionadas
    for fc in old_feature_classes:
        try:
            arcpy.Delete_management(fc)
            arcpy.AddMessage(f"Eliminado: {fc}")
        except Exception as e:
            arcpy.AddError(f"Error al eliminar {fc}: {str(e)}")


if __name__ == "__main__":
    # Obtener la geodatabase desde los parámetros de la herramienta
    gdb_path = arcpy.GetParameterAsText(0)
    delete_old_feature_classes(gdb_path)