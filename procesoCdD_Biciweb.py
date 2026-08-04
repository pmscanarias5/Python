import geopandas as gp
from shapely import wkb

from datetime import date


#Conexión a la BD y lectura de la tabla
uri = "postgresql://pedro.martin:Cnig.2024@10.67.33.15:5432/biciweb"
gdf = gp.read_postgis("SELECT st_envelope(geom), geom, nom_e FROM biciweb.etapa", uri, geom_col="geom")

print (gdf)
#Creación del campo de geometría de tipo envelope legible
gdf["st_envelope"] = gdf["st_envelope"].apply(wkb.loads)

#Se elimina la geometría lineal para asignar la poligonal
gdf_env = (
    gdf
    .set_geometry("st_envelope")
    .drop(columns=["geom"])   # ← elimina la otra geometría
)

#Se asigna el SRC proveniente de la tabla
gdf_env = gdf_env.set_crs(epsg=3857)


#Se introducen campos requeridos por el CdD, se pueden parametrizar en el python.

gdf_env["Ruta-nombre"] = r"C:\rutaDeEjemplo"

gdf_env["Título"] = gdf_env["nom_e"]#Se cambia valor de campo por el requerido en el CdD para título
gdf_env.drop(columns=["nom_e"])#Se cambia valor de campo por el requerido en el CdD para título
gdf_env["Formato del fichero"] = "GPX / KML"
gdf_env["Fecha del dato"] = date.today()
gdf_env["Escala resolución o densidad"] = "Preguntar que debemos indicar"
husoObtenidoGeomeria = '29' #Aqui se puede incluir funcion de obtener huso con gpd o postgis
gdf_env["Huso"] = f"Huso {husoObtenidoGeomeria}"
gdf_env["Autor de los datos"] = "Centro Nacional de Información Geográfica" #Se puede parametrizar o usar campo nombre del la tabla dic_promotor vinculando con el id_e de la tabla geom
gdf_env["Idproductor"] = "Preguntar a CdD como proceder"
gdf_env["Serie"] = "Preguntar a CdD como proceder"
gdf_env["Subserie"] = "Preguntar a CdD como proceder"


#Se exporta a SHP el envelope
out_shp = r"C:\temp\biciweb_cdd\etapa_envelopes.shp"
gdf_env.to_file(out_shp, driver="ESRI Shapefile")
