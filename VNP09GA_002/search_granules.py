from datetime import date
from typing import Union, List

import earthaccess

import VIIRS_tiled_granules

from rasters import Point, Polygon, RasterGeometry

from .constants import VNP09GA_002_CONCEPT_ID

def search_granules(
        date_UTC: Union[date, str] = None,
        start_date_UTC: Union[date, str] = None,
        end_date_UTC: Union[date, str] = None,
        geometry: Union[Point, Polygon, RasterGeometry] = None,
        tile: str = None,
        concept_ID: str = VNP09GA_002_CONCEPT_ID) -> List[earthaccess.search.DataGranule]:
    """
    Search for VNP09GA granules.

    Parameters:
    - date_UTC (Union[date, str], optional): Specific date for the search.
    - start_date_UTC (Union[date, str], optional): Start date for the search range.
    - end_date_UTC (Union[date, str], optional): End date for the search range.
    - target_geometry (Union[Point, Polygon, RasterGeometry], optional): Geometry to target for the search.
    - tile (str, optional): Specific tile to search within.
    - concept_ID (str, optional): Concept ID for the granules. Defaults to VNP09GA_002_CONCEPT_ID.

    Returns:
    - List[earthaccess.search.DataGranule]: List of found remote granules.
    """
    return VIIRS_tiled_granules.search_granules(
        concept_ID=concept_ID,
        date_UTC=date_UTC,
        start_date_UTC=start_date_UTC,
        end_date_UTC=end_date_UTC,
        geometry=geometry,
        tile=tile
    )
