from pathlib import Path

from qgis.core import QgsApplication, QgsRasterLayer


def test_crs():
    app = QgsApplication([], GUIenabled=False)  # noqa: F841
    raster_path = Path(Path(__file__).parent, "data", "small_raster.tif")
    layer = QgsRasterLayer(raster_path.as_posix())
    assert layer.crs().toWkt()
    print(layer.crs())  # noqa: T201
    assert layer.crs().isValid()
