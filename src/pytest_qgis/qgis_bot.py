#  Copyright (C) 2021-2022 pytest-qgis Contributors.
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
from typing import Any, Dict, Optional

from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsVectorDataProvider,
    QgsVectorLayer,
    QgsVectorLayerUtils,
)
from qgis.gui import QgsAttributeDialog, QgsAttributeEditorContext


class QgisBot:
    """
    Class to hold common utility methods for interacting with QIGS.
    """

    def __init__(self) -> None:
        # Import has to be here (or in each method needing iface),
        # because iface is not automatically injected
        # since this module is imported in conftest
        from qgis.utils import iface

        self._iface = iface

    def create_feature_with_attribute_dialog(
        self,
        layer: QgsVectorLayer,
        geometry: QgsGeometry,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> QgsFeature:
        """
        Create test feature with default values using QgsAttributeDialog.
        This ensures that all the default values are honored and
        for example boolean fields are either true or false, not null.
        """
        initial_ids = set(layer.allFeatureIds())

        capabilities = layer.dataProvider().capabilities()

        if not capabilities & QgsVectorDataProvider.AddFeatures:
            raise ValueError(f"Could not create feature for the layer {layer.name()}")

        new_feature = QgsVectorLayerUtils.createFeature(
            layer, context=layer.createExpressionContext()
        )
        new_feature.setGeometry(geometry)

        if attributes is not None:
            if capabilities & QgsVectorDataProvider.ChangeAttributeValues:
                for field_name, value in attributes.items():
                    new_feature[field_name] = value
            else:
                raise ValueError(
                    f"Could not change attributes for layer {layer.name()}"
                )

        assert new_feature.isValid()

        context = QgsAttributeEditorContext()
        context.setMapCanvas(self._iface.mapCanvas())

        dialog = QgsAttributeDialog(
            layer, new_feature, False, self._iface.mainWindow(), True, context
        )
        dialog.setMode(QgsAttributeEditorContext.AddFeatureMode)

        # Two accepts to bypass some warnings
        dialog.accept()
        dialog.accept()
        layer.commitChanges()

        feature_ids = set(layer.allFeatureIds())
        feature_id = list(feature_ids.difference(initial_ids))

        assert feature_id, "Creating new feature failed"
        return layer.getFeature(feature_id[0])
