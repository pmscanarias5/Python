import arcpy
import os

gdb_proyecto = r'\\192.168.192.162\fgdb\RT.gdb'

arcpy.env.workspace = gdb_proyecto
feature_classes = arcpy.ListFeatureClasses()

# Renombrar las clases de entidad agregando el sufijo "_old"
renombrados = {}
for fc in feature_classes:
    new_name = f"{fc}_old"
    #arcpy.management.Rename(fc, new_name)
    renombrados[fc] = new_name


# print(renombrados[clave])
for old_fc, new_fc in renombrados.items():
    new_fc_path = os.path.join(gdb_proyecto, old_fc)  # Nueva clase de entidad
    old_fc_path = os.path.join(gdb_proyecto, new_fc)  # La renombrada con _old

    if new_fc_path[-4:] != '_old':
        if arcpy.Exists(new_fc_path):
            print(old_fc_path)
            indices = arcpy.ListIndexes(old_fc_path)
            for index in indices:
                if index.name != 'FDO_OBJECTID' and index.name != 'FDO_SHAPE':
                    camposIndice = []
                    for campo in index.fields:
                        camposIndice.append(campo.name)
                    #arcpy.AddMessage(f"Añadiendo índice para {index.name} y los campos {camposIndice}")
                    print(f'El index name es{index.name}')

                    arcpy.management.AddIndex(new_fc_path, camposIndice,index.name, "NON_UNIQUE", "ASCENDING")
                    print(f"Añadiendo índice para {index.name} y los campos {camposIndice} en {new_fc_path}")


    # Copiar índices de los _old a las nuevas clases de entidad si son índices de atributos y existen en la clase nueva

