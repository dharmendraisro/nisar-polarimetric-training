# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import numpy as np

def write_geotiff(data,path,transform,epsg,nodata=np.nan):
    import rasterio
    from rasterio.transform import Affine
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if not isinstance(transform,Affine): transform=Affine(*transform)
    with rasterio.open(p,'w',driver='GTiff',height=data.shape[0],width=data.shape[1],count=1,dtype=str(data.dtype),crs=f'EPSG:{epsg}',transform=transform,nodata=nodata,compress='deflate',tiled=True) as dst: dst.write(data,1)
    return p
