# coding=utf-8

"""QGIS plugin implementation.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

.. note:: This source code was copied from the 'postgis viewer' application
     with original authors:
     Copyright (c) 2010 by Ivan Mincik, ivan.mincik@gista.sk
     Copyright (c) 2011 German Carrillo, geotux_tuxman@linuxmail.org
     Copyright (c) 2014 Tim Sutton, tim@linfiniti.com
     Copyright (c) 2021 pytest-qgis Contributors

"""

__author__ = "tim@linfiniti.com"
__revision__ = "$Format:%H$"
__date__ = "10/01/2011"
__copyright__ = (
    "Copyright (c) 2010 by Ivan Mincik, ivan.mincik@gista.sk and "
    "Copyright (c) 2011 German Carrillo, geotux_tuxman@linuxmail.org"
    "Copyright (c) 2014 Tim Sutton, tim@linfiniti.com"
    "Copyright (c) 2021 pytest-qgis Contributors"
)

import logging
from typing import Dict, List, Optional, Union

import sip
from qgis.core import (
    QgsLayerTree,
    QgsMapLayer,
    QgsProject,
    QgsRelationManager,
    QgsVectorLayer,
)
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QAction,
    QDockWidget,
    QMainWindow,
    QMenuBar,
    QToolBar,
    QWidget,
)

from pytest_qgis.mock_qgis_classes import MockMessageBar

LOGGER = logging.getLogger("QGIS")


# noinspection PyMethodMayBeStatic,PyPep8Naming
class QgisInterface(QObject):
    """Class to expose QGIS objects and functions to plugins.

    This class is here for enabling us to run unit tests only,
    so most methods are simply stubs.
    """

    currentLayerChanged = pyqtSignal(QgsMapCanvas)  # noqa N802
    newProjectCreated = pyqtSignal()  # noqa N802

    def __init__(
        self, canvas: QgsMapCanvas, messageBar: MockMessageBar, mainWindow: QMainWindow
    ) -> None:
        """Constructor
        :param canvas:
        """
        QObject.__init__(self)
        self.canvas = canvas
        self._messageBar = messageBar
        self._mainWindow = mainWindow
        self._active_layer_id: Optional[str] = None

        # Set up slots so we can mimic the behaviour of QGIS when layers
        # are added.
        LOGGER.debug("Initialising canvas...")
        # noinspection PyArgumentList
        QgsProject.instance().layersAdded.connect(self.addLayers)
        # noinspection PyArgumentList
        QgsProject.instance().removeAll.connect(self.removeAllLayers)

        # For processing module
        self.destCrs = None
        self._layers: List[QgsMapLayer] = []

        # Add the MenuBar
        menu_bar = QMenuBar()
        self._mainWindow.setMenuBar(menu_bar)

        # Add the toolbar list
        self._toolbars: Dict[str, QToolBar] = {}

    @pyqtSlot("QList<QgsMapLayer*>")
    def addLayers(self, layers: List[QgsMapLayer]) -> None:
        """Handle layers being added to the registry so they show up in canvas.

        :param layers: list<QgsMapLayer> list of map layers that were added

        .. note:: The QgsInterface api does not include this method,
            it is added here as a helper to facilitate testing.
        """
        # LOGGER.debug('addLayers called on qgis_interface')
        # LOGGER.debug('Number of layers being added: %s' % len(layers))
        # LOGGER.debug('Layer Count Before: %s' % len(self.canvas.layers()))
        current_layers = self.canvas.layers()
        final_layers = []
        for layer in current_layers:
            final_layers.append(layer)
        for layer in layers:
            final_layers.append(layer)
        self._layers = final_layers

        self.canvas.setLayers(final_layers)
        # LOGGER.debug('Layer Count After: %s' % len(self.canvas.layers()))

    @pyqtSlot()
    def removeAllLayers(self) -> None:
        """Remove layers from the canvas before they get deleted."""
        if not sip.isdeleted(self.canvas):
            self.canvas.setLayers([])
        self._layers = []

    def newProject(self) -> None:
        """Create new project."""
        # noinspection PyArgumentList
        instance = QgsProject.instance()
        instance.removeAllMapLayers()
        root: QgsLayerTree = instance.layerTreeRoot()
        root.removeAllChildren()
        relation_manager: QgsRelationManager = instance.relationManager()
        for relation in relation_manager.relations():
            relation_manager.removeRelation(relation)
        self._layers = []
        self.newProjectCreated.emit()

    # ---------------- API Mock for QgsInterface follows -------------------

    def zoomFull(self) -> None:
        """Zoom to the map full extent."""
        pass

    def zoomToPrevious(self) -> None:
        """Zoom to previous view extent."""
        pass

    def zoomToNext(self) -> None:
        """Zoom to next view extent."""
        pass

    def zoomToActiveLayer(self) -> None:
        """Zoom to extent of active layer."""
        pass

    def addVectorLayer(
        self, path: str, base_name: str, provider_key: str
    ) -> QgsVectorLayer:
        """Add a vector layer.

        :param path: Path to layer.
        :type path: str

        :param base_name: Base name for layer.
        :type base_name: str

        :param provider_key: Provider key e.g. 'ogr'
        :type provider_key: str
        """
        layer = QgsVectorLayer(path, base_name, provider_key)
        self.addLayers([layer])
        return layer

    def addRasterLayer(self, path: str, base_name: str) -> None:
        """Add a raster layer given a raster layer file name

        :param path: Path to layer.
        :type path: str

        :param base_name: Base name for layer.
        :type base_name: str
        """
        pass

    def activeLayer(self) -> Optional[QgsMapLayer]:
        """Get pointer to the active layer (layer selected in the legend)."""
        return (
            QgsProject.instance().mapLayer(self._active_layer_id)
            if self._active_layer_id
            else None
        )

    def addPluginToMenu(self, name: str, action: QAction) -> None:
        """Add plugin item to menu.

        :param name: Name of the menu item
        :type name: str

        :param action: Action to add to menu.
        :type action: QAction
        """
        pass

    def addToolBarIcon(self, action: QAction) -> None:
        """Add an icon to the plugins toolbar.

        :param action: Action to add to the toolbar.
        :type action: QAction
        """
        pass

    def removeToolBarIcon(self, action: QAction) -> None:
        """Remove an action (icon) from the plugin toolbar.

        :param action: Action to add to the toolbar.
        :type action: QAction
        """
        pass

    def addToolBar(self, toolbar: Union[str, QToolBar]) -> QToolBar:
        """Add toolbar with specified name.

        :param toolbar: Name for the toolbar or QToolBar object.
        """
        if isinstance(toolbar, str):
            name = toolbar
            _toolbar = QToolBar(name, parent=self._mainWindow)
        else:
            name = toolbar.windowTitle()
            _toolbar = toolbar
        self._toolbars[name] = _toolbar
        return _toolbar

    def mapCanvas(self) -> QgsMapCanvas:
        """Return a pointer to the map canvas."""
        return self.canvas

    def mainWindow(self) -> QWidget:
        """Return a pointer to the main window.

        In case of QGIS it returns an instance of QgisApp.
        """
        return self._mainWindow

    def addDockWidget(
        self, area: int, dock_widget: QDockWidget
    ) -> None:  # noqa: ANN001
        """Add a dock widget to the main window.

        :param area: Where in the ui the dock should be placed.
        :type area: Qt.DockWidgetArea

        :param dock_widget: A dock widget to add to the UI.
        :type dock_widget: QDockWidget
        """
        pass

    def legendInterface(self) -> QgsMapCanvas:
        """Get the legend."""
        return self.canvas

    def messageBar(self) -> MockMessageBar:
        """Get the messagebar"""
        return self._messageBar

    def getMockLayers(self) -> List[QgsMapLayer]:
        return self._layers

    def setActiveLayer(self, layer: QgsMapLayer) -> None:
        """
        Set the active layer (layer gets selected in the legend)
        """
        self._active_layer_id = layer.id()
