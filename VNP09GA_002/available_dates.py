from typing import Union, List
from datetime import date, datetime
from rasters import SpatialGeometry

from .search_granules import search_granules

def available_dates(
        start_date_UTC: Union[date, str],
        end_date_UTC: Union[date, str],
        geometry: SpatialGeometry) -> List[str]:
    remote_granules = search_granules(
        start_date_UTC=start_date_UTC,
        end_date_UTC=end_date_UTC,
        geometry=geometry,
    )

    available_dates = sorted(set([
        datetime.strptime(remote_granule["meta"]["native-id"].split(".")[1][1:], "%Y%j").strftime("%Y-%m-%d")
        for remote_granule
        in remote_granules
    ]))

    return available_dates
