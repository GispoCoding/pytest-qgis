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
import os

from qgis.core import Qgis, QgsCoordinateReferenceSystem

try:
    QGIS_VERSION = Qgis.versionInt()
except AttributeError:
    QGIS_VERSION = Qgis.QGIS_VERSION_INT

IN_CI = os.environ.get("QGIS_IN_CI")

EPSG_4326 = "EPSG:4326"
EPSG_3067 = "EPSG:3067"

DEFAULT_CRS = QgsCoordinateReferenceSystem(EPSG_4326)
CRS_3067 = QgsCoordinateReferenceSystem(EPSG_3067)
