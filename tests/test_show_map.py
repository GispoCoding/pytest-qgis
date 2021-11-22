#  Copyright (C) 2021 pytest-qgis Contributors.
#
#
#  This file is part of pytest-qgis.
#
#  pytest-qgis is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  pytest-qgis is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with pytest-qgis.  If not, see <https://www.gnu.org/licenses/>.
#
import pytest
from qgis.core import QgsProject, QgsRectangle

"""
These tests are meant to be tested visually by the developer.
"""

DEFAULT_TIMEOUT = 2


@pytest.fixture(autouse=True)
def setup(new_project):
    pass


@pytest.mark.qgis_show_map(timeout=DEFAULT_TIMEOUT)
def test_show_map(layer_polygon):
    QgsProject.instance().addMapLayers([layer_polygon])


@pytest.mark.qgis_show_map(timeout=DEFAULT_TIMEOUT, extent=QgsRectangle(25, 65, 26, 66))
def test_show_map_custom_extent(layer_polygon):
    QgsProject.instance().addMapLayers([layer_polygon])


@pytest.mark.qgis_show_map(timeout=3)
def test_show_map_crs_change_to_3067(layer_polygon, layer_polygon_3067, raster_3067):
    layer_polygon_3067.setOpacity(0.3)
    raster_3067.setOpacity(0.9)
    QgsProject.instance().addMapLayers([layer_polygon, layer_polygon_3067, raster_3067])


@pytest.mark.qgis_show_map(timeout=DEFAULT_TIMEOUT)
def test_show_map_crs_change_to_4326(layer_polygon, raster_3067, layer_points):
    raster_3067.setOpacity(0.9)
    QgsProject.instance().addMapLayers([layer_points, raster_3067, layer_polygon])


@pytest.mark.qgis_show_map(timeout=DEFAULT_TIMEOUT)
def test_show_map_crs_change_to_4326_2(layer_polygon, layer_points, layer_polygon_3067):
    QgsProject.instance().addMapLayers(
        [layer_points, layer_polygon_3067, layer_polygon]
    )
