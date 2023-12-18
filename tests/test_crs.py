import unittest
from pathlib import Path

from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer

app = QgsApplication([], GUIenabled=False)


class TestCrs(unittest.TestCase):
    def setUp(self):
        # This works with both unittest and pytest
        # app = QgsApplication([], GUIenabled=False)

        # This makes both unittest and pytest fail
        # self._app = QgsApplication([], GUIenabled=False)
        pass

    def test_crs_raster(self):
        raster_path = Path(Path(__file__).parent, "data", "small_raster.tif")
        layer = QgsRasterLayer(raster_path.as_posix())
        assert layer.crs().toWkt()
        print(layer.crs())  # noqa: T201
        assert layer.crs().isValid()

    def test_crs_vector(self):
        gpkg = Path(Path(__file__).parent, "data", "db.gpkg")
        layer = QgsVectorLayer(f"{gpkg}|layername=polygon_3067", "layer", "ogr")
        assert layer.crs().toWkt()
        print(layer.crs())  # noqa: T201
        assert layer.crs().isValid()
