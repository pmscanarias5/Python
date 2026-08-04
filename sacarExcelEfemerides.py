import requests
import json
import time
import pandas as pd
import ast

url = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones/"

querystring = {"api_key":"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwbXNjYW5hcmlhczVAZ21haWwuY29tIiwianRpIjoiMDM0ODliZTktOGI4ZC00ZGExLTg2YzItMTdjNTYzNmMxNmZhIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE2OTk2MTgxMTMsInVzZXJJZCI6IjAzNDg5YmU5LThiOGQtNGRhMS04NmMyLTE3YzU2MzZjMTZmYSIsInJvbGUiOiIifQ.RQFdY6X1K7Uts43kL8nmVdiZnkJDzRGShR9i3soaWXQ"}

headers = {
    'cache-control': "no-cache"
    }

response = requests.request("GET", url, headers=headers, params=querystring).text
response = json.loads(response)
urlEstaciones = response["datos"]
response = requests.request("GET", urlEstaciones, headers=headers, params=querystring).text
response = json.loads(response)


# Leer el archivo txt
ruta = r"C:\temp\resultado.txt"
datos = []
with open(ruta, "r") as f:
    for linea in f:
        # Convertir string a lista usando ast.literal_eval
        datos.append(ast.literal_eval(linea.strip()))

# Crear DataFrame
df = pd.DataFrame(datos, columns=["codigo", "precmax", "tmax", "tmin"])

# Convertir valores a numéricos
df["tmax"] = pd.to_numeric(df["tmax"])
df["tmin"] = pd.to_numeric(df["tmin"])
df["precmax"] = pd.to_numeric(df["precmax"])

# --- Filtrar 9999 para extremos ---
tmax_max = df.loc[df["tmax"] != 9999, "tmax"].max()
tmin_min = df.loc[df["tmin"] != 9999, "tmin"].min()
precmax_max = df.loc[df["precmax"] != 9999, "precmax"].max()

# Añadir columna para marcar extremos
df["extremo"] = ""
df.loc[df["tmax"] == tmax_max, "extremo"] += "Mayor TMAX; "
df.loc[df["tmin"] == tmin_min, "extremo"] += "Menor TMIN; "
df.loc[df["precmax"] == precmax_max, "extremo"] += "Mayor PREC; "

nombres_estaciones = {}
for estacion in response:
    estacionCodigo = estacion["indicativo"]
    estacionNombre = estacion["nombre"]
    nombres_estaciones[estacionCodigo] = estacionNombre

df["nombre"] = df["codigo"].map(nombres_estaciones)
# Guardar
ruta = r"C:\temp\resultado.xlsx"
df.to_excel(ruta, index=False)

print(df)
