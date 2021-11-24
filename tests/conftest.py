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
import shutil
from pathlib import Path

import pytest
from qgis.core import QgsRasterLayer, QgsVectorLayer

from pytest_qgis.utils import clean_qgis_layer

pytest_plugins = "pytester"


@pytest.fixture()
def gpkg(tmp_path: Path) -> Path:
    db = Path(Path(__file__).parent, "data", "db.gpkg")
    new_db_path = tmp_path / "db.gpkg"
    shutil.copy(db, new_db_path)
    return new_db_path


@pytest.fixture()
@clean_qgis_layer
def layer_polygon(gpkg: Path):
    return get_gpkg_layer("polygon", gpkg)


@pytest.fixture()
@clean_qgis_layer
def layer_polygon_3067(gpkg: Path):
    return get_gpkg_layer("polygon_3067", gpkg)


@pytest.fixture()
@clean_qgis_layer
def raster_3067():
    return get_raster_layer(
        "small raster 3067", Path(Path(__file__).parent, "data", "small_raster.tif")
    )


@pytest.fixture()
@clean_qgis_layer
def layer_points(gpkg: Path):
    return get_gpkg_layer("points", gpkg)


def get_gpkg_layer(name: str, gpkg: Path) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"{str(gpkg)}|layername={name}", name, "ogr")
    layer.setProviderEncoding("utf-8")
    assert layer.isValid()
    return layer


def get_raster_layer(name: str, path: Path) -> QgsRasterLayer:
    layer = QgsRasterLayer(str(path), name)
    assert layer.isValid()
    return layer
