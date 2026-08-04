import requests
import json
import pandas as pd
import ast

# --- Obtener estaciones desde AEMET ---
url = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones/"
querystring = {"api_key":"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwbXNjYW5hcmlhczVAZ21haWwuY29tIiwianRpIjoiMDM0ODliZTktOGI4ZC00ZGExLTg2YzItMTdjNTYzNmMxNmZhIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE2OTk2MTgxMTMsInVzZXJJZCI6IjAzNDg5YmU5LThiOGQtNGRhMS04NmMyLTE3YzU2MzZjMTZmYSIsInJvbGUiOiIifQ.RQFdY6X1K7Uts43kL8nmVdiZnkJDzRGShR9i3soaWXQ"}
headers = {'cache-control': "no-cache"}

response = requests.get(url, headers=headers, params=querystring).json()
urlEstaciones = response["datos"]
response = requests.get(urlEstaciones, headers=headers, params=querystring).json()

# --- Leer archivo txt con resultados ---
ruta = r"C:\temp\resultado.txt"
datos = []
with open(ruta, "r") as f:
    for linea in f:
        datos.append(ast.literal_eval(linea.strip()))

# --- Crear DataFrame ---
df = pd.DataFrame(datos, columns=["codigo", "precmax","diaPrecMax","mesPrecMax","añoPrecMax", "tmax","diaTempMax","mesTempMax","añoTempMax", "tmin","diaTempMin","mesTempMin","añoTempMin"])

# Convertir valores a numéricos
df["tmax"] = pd.to_numeric(df["tmax"])
df["tmin"] = pd.to_numeric(df["tmin"])
df["precmax"] = pd.to_numeric(df["precmax"])

# --- Filtrar 9999 para calcular top ---
df_filtrado = df[(df["tmax"] != 9999) & (df["tmin"] != 9999) & (df["precmax"] != 9999)]

# --- Obtener top 30 y seleccionar columnas específicas por cada pestaña ---
# Top TMAX
top_tmax = df_filtrado.nlargest(30, "tmax")[["codigo", "tmax", "diaTempMax","mesTempMax", "añoTempMax"]]

# Top TMIN
top_tmin = df_filtrado.nsmallest(30, "tmin")[["codigo", "tmin", "diaTempMin","mesTempMin", "añoTempMin"]]

# Top PRECIPITACIÓN
top_prec = df_filtrado.nlargest(30, "precmax")[["codigo", "precmax", "diaPrecMax","mesPrecMax", "añoPrecMax"]]

# --- Marcar como extremo ---
top_tmax["extremo"] = "Mayor TMAX"
top_tmin["extremo"] = "Menor TMIN"
top_prec["extremo"] = "Mayor PREC"

# --- Mapear nombres de estaciones ---
nombres_estaciones = {}
for estacion in response:
    nombres_estaciones[estacion["indicativo"]] = estacion["nombre"]

top_tmax["nombre"] = top_tmax["codigo"].map(nombres_estaciones)
top_tmin["nombre"] = top_tmin["codigo"].map(nombres_estaciones)
top_prec["nombre"] = top_prec["codigo"].map(nombres_estaciones)

# --- Guardar
ruta = r"C:\temp\top30_variables_extremos.xlsx"
with pd.ExcelWriter(ruta) as writer:
    top_tmax.to_excel(writer, sheet_name="Top30_TMAX", index=False)
    top_tmin.to_excel(writer, sheet_name="Top30_TMIN", index=False)
    top_prec.to_excel(writer, sheet_name="Top30_PREC", index=False)

print("Excel con top 30 y extremos creado en:", ruta)