import requests
import json
import time

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
listaEstaciones = []
for estacion in response:
    estacionCodigo = estacion["indicativo"]
    peticionModeloTemperatura = f'https://opendata.aemet.es/opendata/api/valores/climatologicos/valoresextremos/parametro/T/estacion/{estacionCodigo}/?api_key=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwbXNjYW5hcmlhczVAZ21haWwuY29tIiwianRpIjoiMDM0ODliZTktOGI4ZC00ZGExLTg2YzItMTdjNTYzNmMxNmZhIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE2OTk2MTgxMTMsInVzZXJJZCI6IjAzNDg5YmU5LThiOGQtNGRhMS04NmMyLTE3YzU2MzZjMTZmYSIsInJvbGUiOiIifQ.RQFdY6X1K7Uts43kL8nmVdiZnkJDzRGShR9i3soaWXQ'
    peticionModeloPrecipitacion = f'https://opendata.aemet.es/opendata/api/valores/climatologicos/valoresextremos/parametro/P/estacion/{estacionCodigo}/?api_key=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwbXNjYW5hcmlhczVAZ21haWwuY29tIiwianRpIjoiMDM0ODliZTktOGI4ZC00ZGExLTg2YzItMTdjNTYzNmMxNmZhIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE2OTk2MTgxMTMsInVzZXJJZCI6IjAzNDg5YmU5LThiOGQtNGRhMS04NmMyLTE3YzU2MzZjMTZmYSIsInJvbGUiOiIifQ.RQFdY6X1K7Uts43kL8nmVdiZnkJDzRGShR9i3soaWXQ'
    responseTemperatura = requests.request("GET", peticionModeloTemperatura, headers=headers, params=querystring).text
    if(responseTemperatura[21:26] != 'exito'):
        print('se excede el tiempo')
        while (responseTemperatura[21:26] != 'exito'):
            responseTemperatura = requests.request("GET", peticionModeloTemperatura, headers=headers, params=querystring).text
        responseTemperatura = json.loads(responseTemperatura)
        print('respuestaCuandoDuerme: ', responseTemperatura)

    else:
        responseTemperatura = json.loads(responseTemperatura)


    responseTemperatura = requests.request("GET", responseTemperatura["datos"], headers=headers, params=querystring).text
    errorTemperatura = False
    try:
        responseTemperatura = json.loads(responseTemperatura)
    except json.JSONDecodeError:
        print("⚠️ JSON vacío o mal formado en respuestaTemperatura")
        print("Contenido:", responseTemperatura)
        errorTemperatura = True


    responsePrecipitacion = requests.request("GET", peticionModeloPrecipitacion, headers=headers, params=querystring).text
    if(responsePrecipitacion[21:26] != 'exito'):
        print('se excede el tiempo')
        while (responsePrecipitacion[21:26] != 'exito'):
            responsePrecipitacion = requests.request("GET", peticionModeloPrecipitacion, headers=headers, params=querystring).text
        responsePrecipitacion = json.loads(responsePrecipitacion)
        print('respuestaCuandoDuerme: ',responsePrecipitacion)
    else:
        responsePrecipitacion = json.loads(responsePrecipitacion)


    responsePrecipitacion = requests.request("GET", responsePrecipitacion["datos"], headers=headers, params=querystring).text
    errorPrecipitacion = False
    try:
        responsePrecipitacion = json.loads(responsePrecipitacion)
    except json.JSONDecodeError:
        print("⚠️ JSON vacío o mal formado en respuestaTemperatura")
        print("Contenido:", responsePrecipitacion)
        errorPrecipitacion = True

    print(responsePrecipitacion)
    if (errorTemperatura):
        tempMax = '9999'
        tempMin = '9999'
    else:
        tempMax = responseTemperatura["temMax"][12]
        tempMin = responseTemperatura["temMin"][12]

    if (errorPrecipitacion):
        precMax = '9999'
    else:
        precMax = responsePrecipitacion["precMaxDia"][12]



    listaEstaciones.append([estacionCodigo,precMax,tempMax,tempMin])

print(listaEstaciones)

ruta = r"C:\temp\resultado.txt"

with open(ruta, "w", encoding="utf-8") as f:
    for elemento in listaEstaciones:
        f.write(str(elemento) + "\n")
