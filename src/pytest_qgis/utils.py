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
from collections import Counter
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional

import sip
from osgeo import gdal
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsLayerTree,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
    QgsVectorLayer,
)

DEFAULT_RASTER_FORMAT = "tif"

DEFAULT_CRS = QgsCoordinateReferenceSystem("EPSG:4326")


def get_common_extent_from_all_layers() -> Optional[QgsRectangle]:
    """Get common extent from all QGIS layers in the project."""
    map_crs = QgsProject.instance().crs()
    layers = list(QgsProject.instance().mapLayers(validOnly=True).values())

    if layers:
        extent = transform_rectangle(layers[0].extent(), layers[0].crs(), map_crs)
        for layer in layers[1:]:
            extent.combineExtentWith(
                transform_rectangle(layer.extent(), layer.crs(), map_crs)
            )
        return extent
    return None


def set_map_crs_based_on_layers() -> None:
    """Set map crs based on layers of the project."""
    crs_counter = Counter(
        layer.crs().authid()
        for layer in QgsProject.instance().mapLayers().values()
        if layer.isSpatial()
    )
    if crs_counter:
        crs_id, _ = crs_counter.most_common(1)[0]
        crs = QgsCoordinateReferenceSystem(crs_id)
    else:
        crs = DEFAULT_CRS
    QgsProject.instance().setCrs(crs)


def transform_rectangle(
    rectangle: QgsRectangle,
    in_crs: QgsCoordinateReferenceSystem,
    out_crs: QgsCoordinateReferenceSystem,
) -> QgsRectangle:
    """
    Transform rectangle from one crs to other.
    """
    if in_crs == out_crs:
        return rectangle

    transform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem(in_crs),
        QgsCoordinateReferenceSystem(out_crs),
        QgsProject.instance(),
    )
    box = transform.transformBoundingBox(rectangle)
    return box


def get_layers_with_different_crs() -> List[QgsMapLayer]:
    map_crs = QgsProject.instance().crs()
    return [
        layer
        for layer in QgsProject.instance().mapLayers().values()
        if layer.crs() != map_crs
    ]


def replace_layers_with_reprojected_clones(
    layers: List[QgsMapLayer], output_path: Path
) -> None:
    """
    For some reason all layers having differing crs from the project are invisible.
    Hotfix is to replace those by reprojected layers with map crs.
    """
    import processing

    vector_layers = [
        layer
        for layer in layers
        if isinstance(layer, QgsVectorLayer) and layer.isSpatial()
    ]
    raster_layers = [
        layer
        for layer in layers
        if isinstance(layer, QgsRasterLayer) and layer.isSpatial()
    ]

    map_crs = QgsProject.instance().crs()
    for input_layer in vector_layers:
        output_layer: QgsVectorLayer = processing.run(
            "native:reprojectlayer",
            {"INPUT": input_layer, "TARGET_CRS": map_crs, "OUTPUT": "TEMPORARY_OUTPUT"},
        )["OUTPUT"]
        copy_layer_style_and_position(input_layer, output_layer, output_path)

    for input_layer in raster_layers:
        try:
            output_raster = str(
                Path(output_path, f"{input_layer.name()}.{DEFAULT_RASTER_FORMAT}")
            )
            warp = gdal.Warp(
                output_raster, input_layer.source(), dstSRS=map_crs.authid()
            )
        finally:
            warp = None  # noqa F841

        copy_layer_style_and_position(
            input_layer, QgsRasterLayer(output_raster), output_path
        )

    # Remove originals from project
    QgsProject.instance().removeMapLayers([layer.id() for layer in layers])


def copy_layer_style_and_position(
    layer1: QgsMapLayer, layer2: QgsMapLayer, tmp_path: Path
) -> None:
    """
    Copy layer style and position to another layer.
    """
    style_file = str(Path(tmp_path, f"{layer1.id()}.qml"))
    msg, succeeded = layer1.saveNamedStyle(style_file)
    if succeeded:
        layer2.loadNamedStyle(style_file)
    layer2.setMetadata(layer1.metadata())
    layer2.setName(layer1.name())
    if layer2.isValid():
        QgsProject.instance().addMapLayer(layer2, False)

    root: QgsLayerTree = QgsProject.instance().layerTreeRoot()
    layer_tree_layer: QgsLayerTreeLayer = root.findLayer(layer1)
    group: QgsLayerTreeGroup = layer_tree_layer.parent()
    index = {child.name(): i for i, child in enumerate(group.children())}[
        layer_tree_layer.name()
    ]

    group.insertLayer(index + 1, layer2)


def clean_qgis_layer(fn: Callable) -> Callable:
    """
    Decorator to ensure that the QGIS layer (fixture) is cleaned properly.

    Sometimes fixture non-memory layers that are used but not added
    to the project might cause segmentation fault errors.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> QgsMapLayer:
        layer: QgsMapLayer = fn(*args, **kwargs)
        yield layer

        if (
            isinstance(layer, QgsMapLayer)
            and not sip.isdeleted(layer)
            and layer.id() not in QgsProject.instance().mapLayers(True).keys()
        ):
            QgsProject.instance().addMapLayer(layer)
            QgsProject.instance().removeMapLayer(layer)

    return wrapper
