import os
from openpyxl import load_workbook
from lxml import etree


#Para gestión de xml

ns = {
    'gmd': 'http://www.isotc216.org/2005/gmd',
    'gco': 'http://www.isotc216.org/2005/gco'
}
parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse('PlantillaMetadatos.xml', parser)
root = tree.getroot()

# Carga archivo Excel
wb = load_workbook(filename='ElementosMetadatos.xlsx')
sheet_ranges = wb['Hoja1']
 
# Lee contenido de la plantilla
with open('PlantillaMetadatos.xml','r',encoding="utf-8") as file:
    filedata = file.read()

# Inicia en la fila 1
i = 1
variable = sheet_ranges['A' + str(i)].value
valor = sheet_ranges['B' + str(i)].value

# Verifica encabezados
if variable == 'Variable' and valor == 'Valor':
    i += 1
    variable = sheet_ranges['A' + str(i)].value
    valor = str(sheet_ranges['B' + str(i)].value)
    
    # Reemplaza variables en la plantilla
    while variable is not None and valor is not None:
        
        valor_str = str(valor)
        print(f"{variable} => {valor_str}")
        filedata = filedata.replace(variable, valor_str)
        
        # Si la variable es 'fileIdentifier', guarda su valor
        if variable == '_fileIdentifier_':
            file_identifier_value = valor_str.strip()


        #Código para añadir automáticamente capas al xml desde el excel poniendo ; únicamente

        if variable == '_IdentificadorCapa1_' and ';' in valor_str:
            listaCapas = valor.split(';')
            print('Lista de capas: ',listaCapas)

            for capa in listaCapas:
                if listaCapas.index(capa) !=0:

                    identifiers = root.xpath('//gmd:identifier', namespaces=ns)
                    # Obtener el último de la lista
                    ultimo_id = identifiers[-1]
                    #  Crear una copia exacta (deep copy)
                    nuevo_id = etree.fromstring(etree.tostring(ultimo_id))

                    # buscando el CharacterString dentro de gmd:code
                    char_strings = nuevo_id.xpath('.//gmd:code/gco:CharacterString', namespaces=ns)
                    if char_strings:
                        char_strings[0].text = capa

                        # 5. Insertar la copia justo después del último original
                        padre = ultimo_id.getparent()
                        indice_ultimo = padre.index(ultimo_id)
                        padre.insert(indice_ultimo + 1, nuevo_id)

        i += 1
        variable = sheet_ranges['A' + str(i)].value
        valor = str(sheet_ranges['B' + str(i)].value)
    
    # Valida que encontramos el valor de fileIdentifier
    if not file_identifier_value:
        print("No se encontró el valor para '_fileIdentifier_' en el Excel.")
    else:

        # NUEVO BLOQUE: Guarda con otro nombre en otra carpeta - Carpeta output_xml
        output_folder = 'output_xml'
        os.makedirs(output_folder, exist_ok=True)
    
        # Usa el valor de fileIdentifier como nombre base del archivo
        base_name = file_identifier_value
        extension = '.xml'
        new_filename = base_name + extension
        new_filepath = os.path.join(output_folder, new_filename)
    
        # Para evitar sobrescribir agrega sufijo si ya existe
        counter = 1
        while os.path.exists(new_filepath):
            new_filename = f"{base_name}_{counter}{extension}"
            new_filepath = os.path.join(output_folder, new_filename)
            counter += 1
  
        # Guardar el archivo modificado
        with open(new_filepath, 'w', encoding="utf-8") as file:
            file.write(filedata)
        
            print(f"\nArchivo guardado como: {new_filepath}")

        tree.write('resultado_metadatos.xml', pretty_print=True, xml_declaration=True, encoding="UTF-8")
            
else:
 print("Las columnas de excel no se llaman 'Variable' y 'Valor'")
 
