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
from typing import Any, Dict, Optional, Union

from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsVectorDataProvider,
    QgsVectorLayer,
    QgsVectorLayerUtils,
)
from qgis.gui import QgisInterface, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.PyQt.QtWidgets import QLabel, QWidget


class QgisBot:
    """
    Class to hold common utility methods for interacting with QIGS.
    """

    def __init__(  # noqa: QGS105 # Iface has to be passed in order to
        # ensure compatibility with all QGIS versions >= 3.10
        self,
        iface: QgisInterface,
    ) -> None:
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

        feature_ids = set(layer.allFeatureIds())
        feature_id = list(feature_ids.difference(initial_ids))

        assert feature_id, "Creating new feature failed"
        return layer.getFeature(feature_id[0])

    @staticmethod
    def get_qgs_attribute_dialog_widgets_by_name(
        widget: Union[QgsAttributeDialog, QWidget]
    ) -> Dict[str, QWidget]:
        """
        Gets recursively all attribute dialog widgets by name.
        :param widget: QgsAttributeDialog for the first time, afterwards QWidget.
        :return: Dictionary with field names as keys and corresponding
        QWidgets as values.
        """
        widgets_by_name = {}
        for child in widget.children():
            if isinstance(child, QLabel):
                if child.text() != "" and child.toolTip() != "":
                    related_widget = child.buddy()
                    if related_widget is not None:
                        widgets_by_name[child.text()] = child.buddy()
            if hasattr(child, "children"):
                widgets_by_name = {
                    **widgets_by_name,
                    **QgisBot.get_qgs_attribute_dialog_widgets_by_name(child),
                }

        return widgets_by_name
