# SPDX-License-Identifier: Apache-2.0
"""Mapping utilities for NISAR GCOV Training."""
from pathlib import Path
import base64,io
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon,box,mapping as shapely_mapping

def _epsg_code(epsg):
    if epsg is None: raise ValueError("Product EPSG is required for mapping.")
    return int(str(epsg).replace("EPSG:",""))

def scene_footprint_wgs84(x,y,epsg):
    x=np.asarray(x); y=np.asarray(y)
    xmin,xmax=float(x.min()),float(x.max()); ymin,ymax=float(y.min()),float(y.max())
    corners=[(xmin,ymin),(xmin,ymax),(xmax,ymax),(xmax,ymin),(xmin,ymin)]
    tr=Transformer.from_crs(f"EPSG:{_epsg_code(epsg)}","EPSG:4326",always_xy=True)
    return Polygon([tr.transform(a,b) for a,b in corners])

def bounds_from_polygon(poly):
    minx,miny,maxx,maxy=poly.bounds
    return {"lon_min":float(minx),"lat_min":float(miny),"lon_max":float(maxx),"lat_max":float(maxy)}

def scene_extent_wgs84(x,y,epsg):
    p=scene_footprint_wgs84(x,y,epsg); return bounds_from_polygon(p),p

def aoi_polygon(lon_min,lon_max,lat_min,lat_max):
    if lon_min>=lon_max or lat_min>=lat_max: raise ValueError("Invalid AOI bounds.")
    return box(float(lon_min),float(lat_min),float(lon_max),float(lat_max))

def load_vector_layer(path):
    import geopandas as gpd
    p=Path(path)
    if not p.exists(): raise FileNotFoundError(f"GIS layer not found: {p}")
    gdf=gpd.read_file(p)
    if gdf.empty: raise ValueError(f"GIS layer is empty: {p}")
    if gdf.crs is None: raise ValueError(f"GIS layer has no CRS: {p}")
    return gdf.to_crs(4326)

def plot_scene_overview(x,y,epsg,title="NISAR Product Footprint",aoi=None,gis_layers=None,figsize=(10,7)):
    import matplotlib.pyplot as plt
    p=scene_footprint_wgs84(x,y,epsg); fig,ax=plt.subplots(figsize=figsize)
    if gis_layers:
        for name,gdf in gis_layers.items(): gdf.boundary.plot(ax=ax,linewidth=.8,label=name)
    xs,ys=p.exterior.xy; ax.fill(xs,ys,alpha=.08); ax.plot(xs,ys,linewidth=2.2,label="NISAR product footprint")
    if aoi is not None:
        ap=aoi if hasattr(aoi,'geom_type') else aoi_polygon(aoi['lon_min'],aoi['lon_max'],aoi['lat_min'],aoi['lat_max'])
        xs,ys=ap.exterior.xy; ax.plot(xs,ys,'--',linewidth=2,label="Requested AOI")
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)"); ax.set_title(title); ax.grid(alpha=.25); ax.legend(loc='best'); fig.tight_layout(); return fig,ax

def _center_zoom(b):
    span=max(b['lon_max']-b['lon_min'],b['lat_max']-b['lat_min'])
    zoom=4 if span>20 else 5 if span>10 else 6 if span>5 else 7 if span>2 else 8 if span>1 else 9 if span>.5 else 10 if span>.2 else 11
    return ((b['lat_min']+b['lat_max'])/2,(b['lon_min']+b['lon_max'])/2),zoom

def folium_scene_map(x,y,epsg,title="NISAR Product",aoi=None,gis_layers=None,add_draw=False,raster_overlay=None):
    import folium
    from folium import GeoJson,LayerControl
    p=scene_footprint_wgs84(x,y,epsg); b=bounds_from_polygon(p); center,zoom=_center_zoom(b)
    m=folium.Map(location=center,zoom_start=zoom,tiles='OpenStreetMap',control_scale=True)
    folium.GeoJson(shapely_mapping(p),name='NISAR Product Footprint',style_function=lambda _: {'color':'#1f4e79','weight':3,'fillOpacity':.08},tooltip=title).add_to(m)
    if aoi is not None:
        ap=aoi if hasattr(aoi,'geom_type') else aoi_polygon(aoi['lon_min'],aoi['lon_max'],aoi['lat_min'],aoi['lat_max'])
        folium.GeoJson(shapely_mapping(ap),name='Requested AOI',style_function=lambda _: {'color':'#d62728','weight':2,'dashArray':'6,4','fillOpacity':.04}).add_to(m)
    if gis_layers:
        for name,gdf in gis_layers.items(): GeoJson(gdf.__geo_interface__,name=name,style_function=lambda _: {'color':'#555','weight':1.2,'fillOpacity':.02}).add_to(m)
    if raster_overlay is not None:
        image,bounds,name=raster_overlay; folium.raster_layers.ImageOverlay(image=image,bounds=bounds,opacity=.78,interactive=True,zindex=3,name=name).add_to(m)
    if add_draw:
        from folium.plugins import Draw
        Draw(export=True,filename='NISAR_AOI.geojson',position='topleft',draw_options={'polyline':False,'polygon':False,'circle':False,'marker':False,'circlemarker':False}).add_to(m)
    LayerControl(collapsed=False).add_to(m); return m

def interactive_aoi_map(x,y,epsg,aoi=None,gis_layers=None):
    from ipyleaflet import Map,Polygon,DrawControl,GeoJSON,basemaps
    from IPython.display import display
    p=scene_footprint_wgs84(x,y,epsg); b=bounds_from_polygon(p); center,zoom=_center_zoom(b)
    m=Map(basemap=basemaps.OpenStreetMap.Mapnik,center=center,zoom=zoom,scroll_wheel_zoom=True)
    m.add_layer(Polygon(locations=[[lat,lon] for lon,lat in p.exterior.coords],color='#1f4e79',fill_color='#1f4e79',fill_opacity=.08,weight=3))
    if aoi is not None:
        ap=aoi if hasattr(aoi,'geom_type') else aoi_polygon(aoi['lon_min'],aoi['lon_max'],aoi['lat_min'],aoi['lat_max'])
        m.add_layer(Polygon(locations=[[lat,lon] for lon,lat in ap.exterior.coords],color='#d62728',fill_color='#d62728',fill_opacity=.04,weight=2))
    if gis_layers:
        for _,gdf in gis_layers.items(): m.add_layer(GeoJSON(data=gdf.__geo_interface__))
    dc=DrawControl(); dc.rectangle={'shapeOptions':{'color':'#d62728','weight':2,'fillOpacity':.05}}; dc.polygon={}; dc.polyline={}; dc.circle={}; dc.marker={}; dc.circlemarker={}; m.add_control(dc); m._nisar_aoi=None
    def on_draw(target,action,geo_json):
        if action=='created' and geo_json.get('geometry',{}).get('type')=='Polygon':
            ring=geo_json['geometry']['coordinates'][0]; lons=[q[0] for q in ring]; lats=[q[1] for q in ring]; m._nisar_aoi={'lon_min':min(lons),'lon_max':max(lons),'lat_min':min(lats),'lat_max':max(lats)}; print('Selected AOI:',m._nisar_aoi)
    dc.on_draw(on_draw); display(m); return m

def array_to_png_data_uri(arr,vmin=None,vmax=None,cmap='gray'):
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from PIL import Image
    a=np.asarray(arr,dtype=float); vmin=float(np.nanpercentile(a,2)) if vmin is None else vmin; vmax=float(np.nanpercentile(a,98)) if vmax is None else vmax
    rgba=plt.get_cmap(cmap)(Normalize(vmin=vmin,vmax=vmax,clip=True)(a),bytes=True); buf=io.BytesIO(); Image.fromarray(rgba,'RGBA').save(buf,format='PNG'); return 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode('ascii')

def raster_map(x,y,epsg,arr,lonlat_bounds,title='GCOV',aoi=None,cmap='gray',vmin=None,vmax=None):
    uri=array_to_png_data_uri(arr,vmin,vmax,cmap); rb=[[lonlat_bounds['lat_min'],lonlat_bounds['lon_min']],[lonlat_bounds['lat_max'],lonlat_bounds['lon_max']]]; return folium_scene_map(x,y,epsg,title=title,aoi=aoi,raster_overlay=(uri,rb,title))
