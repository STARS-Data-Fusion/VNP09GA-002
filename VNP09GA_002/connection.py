from typing import Union, List
from datetime import date, datetime

import earthaccess

import rasters as rt
from rasters import SpatialGeometry, RasterGeometry, Raster
from modland import generate_modland_grid
from VIIRS_tiled_granules import VIIRSTiledProductConnection

from .constants import *
from .search_granules import search_granules
from .retrieve_granule import retrieve_granule
from .VNP09GA_granule import VNP09GAGranule

class VNP09GA(VIIRSTiledProductConnection):
    GranuleClass = VNP09GAGranule

    def __init__(
            self,
            download_directory: str = DOWNLOAD_DIRECTORY):
        super().__init__(
            concept_ID=VNP09GA_002_CONCEPT_ID,
            download_directory=download_directory
        )

    def granule(
            self,
            date_UTC: Union[date, str] = None,
            tile: str = None,
            download_directory: str = DOWNLOAD_DIRECTORY) -> GranuleClass:
        return retrieve_granule(
            date_UTC=date_UTC,
            tile=tile,
            download_directory=download_directory
        )
    
    def variable(
            self,
            variable: str,
            date_UTC: Union[date, str],
            geometry: RasterGeometry = None,
            tile: str = None,
            tile_size: int = 1200,
            filename: str = None,
            resampling: str = None) -> Raster:
        if geometry is None and tile_size is None:
            raise ValueError("neither geometry nor tile size given")

        if geometry is None:
            geometry = generate_modland_grid(tile=tile, tile_size=tile_size)

        remote_granules = self.search(
            date_UTC=date_UTC,
            geometry=geometry,
            tile=tile,
            tile_size=tile_size
        )

        granules = [
            retrieve_granule(remote_granule)
            for remote_granule 
            in remote_granules
        ]

        images = [
            granule.variable(variable)
            for granule 
            in granules
        ]

        mosaic = rt.mosaic(
            images=images,
            geometry=geometry,
            resampling=resampling
        )

        return mosaic
    
    def NDVI(
            self,
            date_UTC: Union[date, str],
            geometry: RasterGeometry,
            filename: str = None,
            resampling: str = None) -> Raster:
        return self.variable(
            variable="NDVI",
            date_UTC=date_UTC,
            geometry=geometry,
            filename=filename,
            resampling=resampling
        )
    
    def albedo(
            self,
            date_UTC: Union[date, str],
            geometry: RasterGeometry,
            filename: str = None,
            resampling: str = None) -> Raster:
        return self.variable(
            variable="albedo",
            date_UTC=date_UTC,
            geometry=geometry,
            filename=filename,
            resampling=resampling
        )
    