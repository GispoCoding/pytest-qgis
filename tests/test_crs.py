import unittest
from pathlib import Path

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsRasterLayer,
    QgsVectorLayer,
)

app = QgsApplication([], GUIenabled=False)


class TestCrs(unittest.TestCase):
    def test_crs_copying(self):
        crs1 = QgsCoordinateReferenceSystem("EPSG:4326")
        assert crs1.isValid()
        crs2 = QgsCoordinateReferenceSystem.fromWkt(crs1.toWkt())
        assert crs1.toWkt() == crs2.toWkt()
        assert crs2.isValid()  # <-- raises error

    def test_crs_raster(self):
        raster_path = Path(Path(__file__).parent, "data", "small_raster.tif")
        layer = QgsRasterLayer(raster_path.as_posix())
        assert layer.crs().toWkt()
        assert layer.crs().isValid()

    def test_crs_vector(self):
        gpkg = Path(Path(__file__).parent, "data", "db.gpkg")
        layer = QgsVectorLayer(f"{gpkg}|layername=polygon_3067", "layer", "ogr")
        assert layer.crs().toWkt()
        assert layer.crs().isValid()
