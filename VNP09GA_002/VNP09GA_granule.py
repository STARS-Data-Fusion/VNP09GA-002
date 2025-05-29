from typing import Union, List
import logging
from datetime import datetime
from glob import glob
from os import makedirs
from os.path import exists, join, abspath, expanduser, basename, splitext
import json
import h5py
import numpy as np
import pandas as pd
from dateutil import parser
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Point, Polygon
from skimage.transform import resize

import colored_logging
import rasters
import rasters as rt
from modland import parsehv, generate_modland_grid

from rasters import Raster, RasterGrid, RasterGeometry

from VIIRS_tiled_granules import VIIRSTiledGranule

# Define colormaps for NDVI and Albedo
NDVI_COLORMAP = LinearSegmentedColormap.from_list(
    name="NDVI",
    colors=[
        "#0000ff",
        "#000000",
        "#745d1a",
        "#e1dea2",
        "#45ff01",
        "#325e32"
    ]
)

ALBEDO_COLORMAP = "gray"

DEFAULT_WORKING_DIRECTORY = "."

logger = logging.getLogger(__name__)

class VNP09GAGranule(VIIRSTiledGranule):
    CLOUD_DATASET_NAME = "HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SurfReflect_QF1_1"

    def __init__(self, filename: Union[str, VIIRSTiledGranule]):
        """
        Initialize the VNP09GAGranule object.

        :param filename: The filename of the granule.
        """
        if isinstance(filename, VIIRSTiledGranule):
            super().__init__(filename.filename)
        elif isinstance(filename, str):
            super().__init__(filename)
        else:
            raise ValueError("no valid granule filename given")

    def get_cloud_mask(self, target_shape: tuple = None) -> Raster:
        h, v = self.hv

        if self._cloud_mask is None:
            with h5py.File(self.filename_absolute, "r") as f:
                QF1 = np.array(f[self.CLOUD_DATASET_NAME])
                cloud_levels = (QF1 >> 2) & 3
                cloud_mask = cloud_levels > 0
                self._cloud_mask = cloud_mask
        else:
            cloud_mask = self._cloud_mask

        if target_shape is not None:
            cloud_mask = resize(cloud_mask, target_shape, order=0).astype(bool)
            shape = target_shape
        else:
            shape = cloud_mask.shape

        geometry = generate_modland_grid(h, v, shape[0])
        cloud_mask = Raster(cloud_mask, geometry=geometry)

        return cloud_mask

    cloud_mask = property(get_cloud_mask)

    def dataset(
            self,
            filename: str,
            dataset_name: str,
            scale_factor: float,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None,
            resampling: str = None) -> Raster:

        with h5py.File(filename, "r") as f:
            DN = np.array(f[dataset_name])
            h, v = self.hv
            grid = generate_modland_grid(h, v, DN.shape[0])
            logger.info(f"opening VIIRS file: {colored_logging.file(self.filename)}")
            logger.info(f"loading {colored_logging.val(dataset_name)} at {colored_logging.val(f'{grid.cell_size:0.2f} m')} resolution")
            DN = Raster(DN, geometry=grid)

        data = DN * scale_factor

        if apply_cloud_mask:
            if cloud_mask is None:
                cloud_mask = self.get_cloud_mask(target_shape=DN.shape)

            data = rt.where(cloud_mask, np.nan, data)

        if geometry is not None:
            data = data.to_geometry(geometry, resampling=resampling)

        return data

    @property
    def geometry_M(self) -> RasterGrid:
        return generate_modland_grid(*self.hv, 1200)

    @property
    def geometry_I(self) -> RasterGrid:
        return generate_modland_grid(*self.hv, 2400)

    def geometry(self, band: str) -> RasterGrid:
        try:
            band_letter = band[0]
        except Exception as e:
            raise ValueError(f"invalid band: {band}")

        if band_letter == "I":
            return self.geometry_I
        elif band_letter == "M":
            return self.geometry_M
        else:
            raise ValueError(f"invalid band: {band}")

    def get_sensor_zenith_M(self, geometry: RasterGeometry = None) -> Raster:
        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SensorZenith_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank sensor zenith image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    sensor_zenith_M = property(get_sensor_zenith_M)

    def get_sensor_zenith_I(self, geometry: RasterGeometry = None) -> Raster:
        h, v = self.hv
        grid_I = generate_modland_grid(h, v, 2400)

        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SensorZenith_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False,
            geometry=grid_I,
            resampling="cubic"
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank sensor zenith image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    sensor_zenith_I = property(get_sensor_zenith_I)

    def sensor_zenith(self, band: str, geometry: RasterGeometry = None) -> Raster:
        try:
            band_letter = band[0]
        except Exception as e:
            raise ValueError(f"invalid band: {band}")

        if band_letter == "I":
            return self.get_sensor_zenith_I(geometry=geometry)
        elif band_letter == "M":
            return self.get_sensor_zenith_M(geometry=geometry)
        else:
            raise ValueError(f"invalid band: {band}")

    def get_sensor_azimuth_M(self, geometry: RasterGeometry = None) -> Raster:
        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SensorAzimuth_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank sensor azimuth image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    sensor_azimuth_M = property(get_sensor_azimuth_M)

    def get_sensor_azimuth_I(self, geometry: RasterGeometry = None) -> Raster:
        h, v = self.hv
        grid_I = generate_modland_grid(h, v, 2400)

        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SensorAzimuth_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False,
            geometry=grid_I,
            resampling="cubic"
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank sensor azimuth image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    sensor_azimuth_I = property(get_sensor_azimuth_I)

    def sensor_azimuth(self, band: str, geometry: RasterGeometry = None) -> Raster:
        try:
            band_letter = band[0]
        except Exception as e:
            raise ValueError(f"invalid band: {band}")

        if band_letter == "I":
            return self.get_sensor_azimuth_I(geometry=geometry)
        elif band_letter == "M":
            return self.get_sensor_azimuth_M(geometry=geometry)
        else:
            raise ValueError(f"invalid band: {band}")

    def get_solar_zenith_M(self, geometry: RasterGeometry = None) -> Raster:
        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SolarZenith_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank solar zenith image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    solar_zenith_M = property(get_solar_zenith_M)

    def get_solar_zenith_I(self, geometry: RasterGeometry = None) -> Raster:
        h, v = self.hv
        grid_I = generate_modland_grid(h, v, 2400)

        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SolarZenith_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False,
            geometry=grid_I,
            resampling="cubic"
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank solar zenith image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    solar_zenith_I = property(get_solar_zenith_I)

    def solar_zenith(self, band: str, geometry: RasterGeometry = None) -> Raster:
        try:
            band_letter = band[0]
        except Exception as e:
            raise ValueError(f"invalid band: {band}")

        if band_letter == "I":
            return self.get_solar_zenith_I(geometry=geometry)
        elif band_letter == "M":
            return self.get_solar_zenith_M(geometry=geometry)
        else:
            raise ValueError(f"invalid band: {band}")

    def get_solar_azimuth_M(self, geometry: RasterGeometry = None) -> Raster:
        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SolarAzimuth_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank solar azimuth image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    solar_azimuth_M = property(get_solar_azimuth_M)

    def get_solar_azimuth_I(self, geometry: RasterGeometry = None) -> Raster:

        h, v = self.hv
        grid_I = generate_modland_grid(h, v, 2400)

        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SolarAzimuth_1",
            0.01,
            cloud_mask=None,
            apply_cloud_mask=False,
            geometry=grid_I,
            resampling="cubic"
        )

        if np.all(np.isnan(image)):
            raise ValueError("blank solar azimuth image")

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    solar_azimuth_I = property(get_solar_azimuth_I)

    def solar_azimuth(self, band: str, geometry: RasterGeometry = None) -> Raster:
        try:
            band_letter = band[0]
        except Exception as e:
            raise ValueError(f"invalid band: {band}")

        if band_letter == "I":
            return self.get_solar_azimuth_I(geometry=geometry)
        elif band_letter == "M":
            return self.get_solar_azimuth_M(geometry=geometry)
        else:
            raise ValueError(f"invalid band: {band}")

    def get_M_band(
            self,
            band: int,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:
        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_1km_2D/Data Fields/SurfReflect_M{int(band)}_1",
            0.0001,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask
        )

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    def get_I_band(
            self,
            band: int,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:
        image = self.dataset(
            self.filename_absolute,
            f"HDFEOS/GRIDS/VIIRS_Grid_500m_2D/Data Fields/SurfReflect_I{int(band)}_1",
            0.0001,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask
        )

        if geometry is not None:
            image = image.to_geometry(geometry)

        return image

    def band(
            self,
            band: str,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:
        try:
            band_letter = band[0]
            band_number = int(band[1:])
        except Exception as e:
            raise ValueError(f"invalid band: {band}")

        if band_letter == "I":
            return self.get_I_band(
                band=band_number,
                cloud_mask=cloud_mask,
                apply_cloud_mask=apply_cloud_mask,
                geometry=geometry
            )
        elif band_letter == "M":
            return self.get_M_band(
                band=band_number,
                cloud_mask=cloud_mask,
                apply_cloud_mask=apply_cloud_mask,
                geometry=geometry
            )
        else:
            raise ValueError(f"invalid band: {band}")

    def get_red(
            self,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:
        return self.get_I_band(
            band=1,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

    red = property(get_red)

    def get_NIR(
            self,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:
        return self.get_I_band(
            band=2,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

    NIR = property(get_NIR)

    def get_NDVI(
            self,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:

        red = self.get_red(
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        NIR = self.get_NIR(
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        NDVI = np.clip((NIR - red) / (NIR + red), -1, 1)

        if geometry is not None:
            NDVI = NDVI.to_geometry(geometry)

        NDVI.cmap = NDVI_COLORMAP

        return NDVI

    NDVI = property(get_NDVI)

    def get_albedo(
            self,
            cloud_mask: Raster = None,
            apply_cloud_mask: bool = True,
            geometry: RasterGeometry = None) -> Raster:
        b1 = self.get_M_band(
            1,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b2 = self.get_M_band(
            2,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b3 = self.get_M_band(
            3,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b4 = self.get_M_band(
            4,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b5 = self.get_M_band(
            5,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b7 = self.get_M_band(
            7,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b8 = self.get_M_band(
            8,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b10 = self.get_M_band(
            10,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        b11 = self.get_M_band(
            11,
            cloud_mask=cloud_mask,
            apply_cloud_mask=apply_cloud_mask,
            geometry=geometry
        )

        # https://lpdaac.usgs.gov/documents/194/VNP43_ATBD_V1.pdf
        albedo = 0.2418 * b1 \
                    - 0.201 * b2 \
                    + 0.2093 * b3 \
                    + 0.1146 * b4 \
                    + 0.1348 * b5 \
                    + 0.2251 * b7 \
                    + 0.1123 * b8 \
                    + 0.0860 * b10 \
                    + 0.0803 * b11 \
                    - 0.0131

        albedo = np.clip(albedo, 0, 1)

        if geometry is not None:
            logger.info(f"projecting VIIRS albedo from {colored_logging.val(albedo.geometry.cell_size)} to {colored_logging.val(geometry.cell_size)}")
            albedo = albedo.to_geometry(geometry)

        albedo.cmap = ALBEDO_COLORMAP

        return albedo
    
    albedo = property(get_albedo)

    def variable(self, variable: str) -> Raster:
        if hasattr(self, variable):
            return getattr(self, variable)
        else:
            raise AttributeError(f"Variable '{variable}' not found in VNP21A1DGranule.")
