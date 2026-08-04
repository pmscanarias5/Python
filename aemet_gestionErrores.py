import requests
import time


API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwbXNjYW5hcmlhczVAZ21haWwuY29tIiwianRpIjoiMDM0ODliZTktOGI4ZC00ZGExLTg2YzItMTdjNTYzNmMxNmZhIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE2OTk2MTgxMTMsInVzZXJJZCI6IjAzNDg5YmU5LThiOGQtNGRhMS04NmMyLTE3YzU2MzZjMTZmYSIsInJvbGUiOiIifQ.RQFdY6X1K7Uts43kL8nmVdiZnkJDzRGShR9i3soaWXQ"

headers = {
    'cache-control': "no-cache"
}

# -------------------------------------------------
# FUNCIÓN REQUEST CON REINTENTOS
# -------------------------------------------------
def get_with_retry(url, params,headers=None, retries=8, timeout=30, ):

    for intento in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout, params = params)
            r.raise_for_status()
            return r.json()

        except Exception:
            print(f"Intento {intento+1}/{retries} fallido -> {url}")

            if intento < retries - 1:
                espera = 2
                time.sleep(espera)
            else:
                print("❌ Se agotaron los intentos.")
                return None


# -------------------------------------------------
# 1) INVENTARIO ESTACIONES
# -------------------------------------------------
url_inventario = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones/"
querystring = {"api_key": API_KEY}

modeloInventario = get_with_retry(url_inventario, headers=headers, params = querystring)

if not modeloInventario:
    print("No se pudo obtener inventario.")
    exit()

urlEstaciones = modeloInventario.get("datos")

listaEstacionesData = get_with_retry(urlEstaciones, headers=headers,params = querystring)

if not listaEstacionesData:
    print("No se pudo obtener listado estaciones.")
    exit()

# -------------------------------------------------
# 2) BUCLE ESTACIONES
# -------------------------------------------------
listaEstaciones = []

for estacion in listaEstacionesData:

    estacionCodigo = estacion["indicativo"]

    peticionModeloTemperatura = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/"
        f"valoresextremos/parametro/T/estacion/{estacionCodigo}/?api_key={API_KEY}"
    )

    peticionModeloPrecipitacion = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/"
        f"valoresextremos/parametro/P/estacion/{estacionCodigo}/?api_key={API_KEY}"
    )

    # ---------------- TEMPERATURA ----------------
    modeloTemp = get_with_retry(peticionModeloTemperatura, headers=headers,params = querystring)

    if modeloTemp:
        responseTemperatura = get_with_retry(modeloTemp.get("datos"), headers=headers, params = querystring)
    else:
        responseTemperatura = None

    # ---------------- PRECIPITACIÓN ----------------
    modeloPrec = get_with_retry(peticionModeloPrecipitacion, headers=headers, params = querystring)

    if modeloPrec:
        responsePrecipitacion = get_with_retry(modeloPrec.get("datos"), headers=headers, params = querystring)
    else:
        responsePrecipitacion = None

    # ---------------- VALORES FINALES ----------------
    if responseTemperatura:
        try:
            tempMax = responseTemperatura["temMax"][12]
            diaTempMax = responseTemperatura["diaMax"][12]
            mesTempMax = responseTemperatura["mesMax"]
            añoTempMax = responseTemperatura["anioMax"][12]
            tempMin = responseTemperatura["temMin"][12]
            diaTempMin = responseTemperatura["diaMin"][12]
            mesTempMin = responseTemperatura["mesMin"]
            añoTempMin = responseTemperatura["anioMin"][12]
        except:
            tempMax = '9999'
            tempMin = '9999'
            diaTempMax = '9999'
            mesTempMax = '9999'
            añoTempMax = '9999'
            diaTempMin = '9999'
            mesTempMin = '9999'
            añoTempMin = '9999'
    else:
        tempMax = '9999'
        tempMin = '9999'
        diaTempMax = '9999'
        mesTempMax = '9999'
        añoTempMax = '9999'
        diaTempMin = '9999'
        mesTempMin = '9999'
        añoTempMin = '9999'

    if responsePrecipitacion:
        try:
            precMax = responsePrecipitacion["precMaxDia"][12]
            diaPrecMax = responsePrecipitacion["diaMaxDia"][12]
            mesPrecMax = responsePrecipitacion["mesMaxDia"]
            añoPrecMax = responsePrecipitacion["anioMaxDia"][12]
        except:
            precMax = '9999'
            diaPrecMax =  '9999'
            mesPrecMax = '9999'
            añoPrecMax= '9999'
    else:
        precMax = '9999'
        diaPrecMax = '9999'
        mesPrecMax = '9999'
        añoPrecMax = '9999'

    listaEstaciones.append([estacionCodigo, precMax,diaPrecMax, mesPrecMax, añoPrecMax, tempMax,diaTempMax, mesTempMax, añoTempMax, tempMin,diaTempMin, mesTempMin, añoTempMin])

# -------------------------------------------------
# 3) GUARDAR RESULTADO
# -------------------------------------------------
print(listaEstaciones)

ruta = r"C:\temp\resultado.txt"

with open(ruta, "w", encoding="utf-8") as f:
    for elemento in listaEstaciones:
        f.write(str(elemento) + "\n")