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
    "Copyright (c) 2021-2023 pytest-qgis Contributors"
)

import logging
import typing
from typing import Any, ClassVar, Optional, Union

from qgis import core as qgis_core
from qgis.core import (
    QgsLayerTree,
    QgsMapLayer,
    QgsProject,
    QgsRelationManager,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface as QgisAbstractInterface
from qgis.gui import (
    QgsAbstractMapToolHandler,
    QgsAdvancedDigitizingDockWidget,
    QgsApplicationExitBlockerInterface,
    QgsAttributeDialog,
    QgsBrowserGuiModel,
    QgsCustomDropHandler,
    QgsCustomProjectOpenHandler,
    QgsDevToolWidgetFactory,
    QgsLayerTreeMapCanvasBridge,
    QgsLayerTreeView,
    QgsLayoutCustomDropHandler,
    QgsLayoutDesignerInterface,
    QgsMapCanvas,
    QgsMapLayerConfigWidgetFactory,
    QgsMessageBar,
    QgsOptionsWidgetFactory,
    QgsPluginManagerInterface,
    QgsStatusBar,
)
from qgis.PyQt import QtCore, QtGui, QtWidgets, sip
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot

from pytest_qgis.mock_qgis_classes import MockMessageBar

LOGGER = logging.getLogger("QGIS")


class QgisInterface(QgisAbstractInterface):
    """
    Class to expose QGIS objects and functions to plugins.

    This class is here for enabling us to run unit tests only,
    so some of the methods are simply stubs.
    """

    currentLayerChanged = QtCore.pyqtSignal(QgsMapCanvas)  # noqa: N815
    newProjectCreated = pyqtSignal()  # noqa: N815

    layerSavedAs: ClassVar[QtCore.pyqtSignal]
    projectRead: ClassVar[QtCore.pyqtSignal]
    initializationCompleted: ClassVar[QtCore.pyqtSignal]
    layoutDesignerClosed: ClassVar[QtCore.pyqtSignal]
    layoutDesignerWillBeClosed: ClassVar[QtCore.pyqtSignal]
    layoutDesignerOpened: ClassVar[QtCore.pyqtSignal]
    currentThemeChanged: ClassVar[QtCore.pyqtSignal]

    def __init__(
        self,
        canvas: QgsMapCanvas,
        messageBar: MockMessageBar,
        mainWindow: QtWidgets.QMainWindow,
    ) -> None:
        super().__init__()
        self.canvas = canvas
        self._messageBar = messageBar
        self._mainWindow = mainWindow
        self._active_layer_id: Optional[str] = None

        # Set up slots so we can mimic the behaviour of QGIS when layers
        # are added.
        LOGGER.debug("Initialising canvas...")
        QgsProject.instance().layersAdded.connect(self.addLayers)
        QgsProject.instance().removeAll.connect(self.removeAllLayers)

        # For processing module
        self.destCrs = None
        self._layers: list[QgsMapLayer] = []

        # Add the MenuBar
        menu_bar = QtWidgets.QMenuBar()
        self._mainWindow.setMenuBar(menu_bar)

        # Add the toolbar list
        self._toolbars: dict[str, QtWidgets.QToolBar] = {}

    @pyqtSlot("QList<QgsMapLayer*>")
    def addLayers(self, layers: list[QgsMapLayer]) -> None:
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

    def newProject(self, promptToSaveFlag: bool = False) -> bool:
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
        return True

    def setGpsPanelConnection(
        self, connection: Optional[qgis_core.QgsGpsConnection]
    ) -> None:
        ...

    def browserModel(self) -> Optional["QgsBrowserGuiModel"]:
        ...

    def askForDatumTransform(
        self,
        sourceCrs: qgis_core.QgsCoordinateReferenceSystem,
        destinationCrs: qgis_core.QgsCoordinateReferenceSystem,
    ) -> bool:
        ...

    def invalidateLocatorResults(self) -> None:
        ...

    def deregisterLocatorFilter(
        self, filter: Optional[qgis_core.QgsLocatorFilter]
    ) -> None:
        ...

    def registerLocatorFilter(
        self, filter: Optional[qgis_core.QgsLocatorFilter]
    ) -> None:
        ...

    def locatorSearch(self, searchText: Optional[str]) -> None:
        ...

    def preloadForm(self, uifile: Optional[str]) -> None:
        ...

    def getFeatureForm(
        self, layer: Optional[qgis_core.QgsVectorLayer], f: qgis_core.QgsFeature
    ) -> Optional["QgsAttributeDialog"]:
        ...

    def openFeatureForm(
        self,
        l: Optional[qgis_core.QgsVectorLayer],
        f: qgis_core.QgsFeature,
        updateFeatureOnly: bool = ...,
        showModal: bool = ...,
    ) -> bool:
        ...

    def openURL(self, url: Optional[str], useQgisDocDirectory: bool = ...) -> None:
        ...

    def unregisterCustomLayoutDropHandler(
        self, handler: Optional["QgsLayoutCustomDropHandler"]
    ) -> None:
        ...

    def registerCustomLayoutDropHandler(
        self, handler: Optional["QgsLayoutCustomDropHandler"]
    ) -> None:
        ...

    def unregisterCustomProjectOpenHandler(
        self, handler: Optional["QgsCustomProjectOpenHandler"]
    ) -> None:
        ...

    def registerCustomProjectOpenHandler(
        self, handler: Optional["QgsCustomProjectOpenHandler"]
    ) -> None:
        ...

    def unregisterCustomDropHandler(
        self, handler: Optional["QgsCustomDropHandler"]
    ) -> None:
        ...

    def registerCustomDropHandler(
        self, handler: Optional["QgsCustomDropHandler"]
    ) -> None:
        ...

    def unregisterMapToolHandler(
        self, handler: Optional["QgsAbstractMapToolHandler"]
    ) -> None:
        ...

    def registerMapToolHandler(
        self, handler: Optional["QgsAbstractMapToolHandler"]
    ) -> None:
        ...

    def unregisterApplicationExitBlocker(
        self, blocker: Optional["QgsApplicationExitBlockerInterface"]
    ) -> None:
        ...

    def registerApplicationExitBlocker(
        self, blocker: Optional["QgsApplicationExitBlockerInterface"]
    ) -> None:
        ...

    def unregisterDevToolWidgetFactory(
        self, factory: Optional["QgsDevToolWidgetFactory"]
    ) -> None:
        ...

    def registerDevToolWidgetFactory(
        self, factory: Optional["QgsDevToolWidgetFactory"]
    ) -> None:
        ...

    def unregisterProjectPropertiesWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        ...

    def registerProjectPropertiesWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        ...

    def unregisterOptionsWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        ...

    def registerOptionsWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        ...

    def unregisterMapLayerConfigWidgetFactory(
        self, factory: Optional["QgsMapLayerConfigWidgetFactory"]
    ) -> None:
        ...

    def registerMapLayerConfigWidgetFactory(
        self, factory: Optional["QgsMapLayerConfigWidgetFactory"]
    ) -> None:
        ...

    def unregisterMainWindowAction(self, action: Optional[QtWidgets.QAction]) -> bool:
        ...

    def registerMainWindowAction(
        self, action: Optional[QtWidgets.QAction], defaultShortcut: Optional[str]
    ) -> bool:
        ...

    def removeWindow(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def addWindow(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def showAttributeTable(
        self,
        l: Optional[qgis_core.QgsVectorLayer],
        filterExpression: Optional[str] = ...,
    ) -> Optional[QtWidgets.QDialog]:
        ...

    def showLayerProperties(
        self, layer: Optional[qgis_core.QgsMapLayer], page: Optional[str] = ...
    ) -> None:
        ...

    def removeDockWidget(self, dockwidget: Optional[QtWidgets.QDockWidget]) -> None:
        ...

    def addTabifiedDockWidget(
        self,
        area: QtCore.Qt.DockWidgetArea,
        dockwidget: Optional[QtWidgets.QDockWidget],
        tabifyWith: typing.Iterable[Optional[str]] = ...,
        raiseTab: bool = ...,
    ) -> None:
        ...

    def addDockWidget(
        self,
        area: QtCore.Qt.DockWidgetArea,
        dockwidget: Optional[QtWidgets.QDockWidget],
    ) -> None:
        ...

    def removePluginMeshMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def addPluginToMeshMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def removePluginWebMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def addPluginToWebMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def removePluginVectorMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def addPluginToVectorMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def removePluginRasterMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def addPluginToRasterMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def removePluginDatabaseMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def addPluginToDatabaseMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def removeAddLayerAction(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def insertAddLayerAction(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def removePluginMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def addPluginToMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        ...

    def saveStyleSheetOptions(self, opts: dict[Optional[str], Any]) -> None:
        ...

    def buildStyleSheet(self, opts: dict[Optional[str], Any]) -> None:
        ...

    def showProjectPropertiesDialog(self, currentPage: Optional[str] = ...) -> None:
        ...

    def showOptionsDialog(
        self,
        parent: Optional[QtWidgets.QWidget] = ...,
        currentPage: Optional[str] = ...,
    ) -> None:
        ...

    def openLayoutDesigner(
        self, layout: Optional[qgis_core.QgsMasterLayoutInterface]
    ) -> Optional["QgsLayoutDesignerInterface"]:
        ...

    def showLayoutManager(self) -> None:
        ...

    def addUserInputWidget(self, widget: Optional[QtWidgets.QWidget]) -> None:
        ...

    def openMessageLog(self) -> None:
        ...

    @typing.overload
    def addToolBar(self, name: Optional[str]) -> Optional[QtWidgets.QToolBar]:
        ...

    @typing.overload
    def addToolBar(
        self,
        toolbar: Optional[QtWidgets.QToolBar],
        area: Optional[QtCore.Qt.ToolBarArea] = None,
    ) -> None:
        ...

    def addToolBar(
        self,
        toolbar: Union[str, QtWidgets.QToolBar],
        area: Optional[QtCore.Qt.ToolBarArea] = None,
    ) -> Optional[QtWidgets.QToolBar]:
        if isinstance(toolbar, str):
            name = toolbar
            _toolbar = QtWidgets.QToolBar(name, parent=self._mainWindow)
        else:
            name = toolbar.windowTitle()
            _toolbar = toolbar
        self._toolbars[name] = _toolbar
        return _toolbar if isinstance(toolbar, str) else None

    def removeWebToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        ...

    def addWebToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        ...

    def addWebToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        ...

    def removeDatabaseToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        ...

    def addDatabaseToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        ...

    def addDatabaseToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        ...

    def removeVectorToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        ...

    def addVectorToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        ...

    def addVectorToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        ...

    def removeRasterToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        ...

    def addRasterToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        ...

    def addRasterToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        ...

    def removeToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        ...

    def addToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        ...

    def addToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        ...

    def pasteFromClipboard(self, a0: Optional[qgis_core.QgsMapLayer]) -> None:
        ...

    def copySelectionToClipboard(self, a0: Optional[qgis_core.QgsMapLayer]) -> None:
        ...

    def setActiveLayer(self, layer: Optional[qgis_core.QgsMapLayer]) -> bool:
        """
        Set the active layer (layer gets selected in the legend)
        """
        if layer is not None and QgsProject.instance().mapLayer(layer.id()):
            self._active_layer_id = layer.id()
            return True
        return False

    def reloadConnections(self) -> None:
        ...

    def addProject(self, project: Optional[str]) -> bool:
        ...

    def addTiledSceneLayer(
        self, url: Optional[str], baseName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsTiledSceneLayer]:
        ...

    def addPointCloudLayer(
        self, url: Optional[str], baseName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsPointCloudLayer]:
        ...

    def addVectorTileLayer(
        self, url: Optional[str], baseName: Optional[str]
    ) -> Optional[qgis_core.QgsVectorTileLayer]:
        ...

    def addMeshLayer(
        self, url: Optional[str], baseName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsMeshLayer]:
        ...

    @typing.overload
    def addRasterLayer(
        self, rasterLayerPath: Optional[str], baseName: Optional[str] = ...
    ) -> Optional[qgis_core.QgsRasterLayer]:
        ...

    @typing.overload
    def addRasterLayer(
        self, url: Optional[str], layerName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsRasterLayer]:
        ...

    def addVectorLayer(
        self,
        vectorLayerPath: Optional[str],
        baseName: Optional[str],
        providerKey: Optional[str],
    ) -> Optional[qgis_core.QgsVectorLayer]:
        layer = QgsVectorLayer(vectorLayerPath, baseName, providerKey)
        self.addLayers([layer])
        return layer

    def zoomToActiveLayer(self) -> None:
        ...

    def zoomToNext(self) -> None:
        ...

    def zoomToPrevious(self) -> None:
        ...

    def zoomFull(self) -> None:
        ...

    def userProfileManager(self) -> Optional[qgis_core.QgsUserProfileManager]:
        ...

    def layerTreeInsertionPoint(
        self,
    ) -> qgis_core.QgsLayerTreeRegistryBridge.InsertionPoint:
        ...

    def takeAppScreenShots(
        self, saveDirectory: Optional[str], categories: int = ...
    ) -> None:
        ...

    def statusBarIface(self) -> Optional["QgsStatusBar"]:
        ...

    def messageTimeout(self) -> int:
        ...

    def vectorLayerTools(self) -> Optional[qgis_core.QgsVectorLayerTools]:
        ...

    def actionRegularPolygonCenterCorner(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRegularPolygonCenterPoint(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRegularPolygon2Points(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRectangle3PointsProjected(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRectangle3PointsDistance(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRectangleExtent(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRectangleCenterPoint(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionEllipseFoci(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionEllipseExtent(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionEllipseCenterPoint(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionEllipseCenter2Points(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCircleCenterPoint(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCircle2TangentsPoint(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCircle3Tangents(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCircle3Points(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCircle2Points(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAbout(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCheckQgisVersion(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionQgisHomePage(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionHelpContents(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCustomProjection(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionOptions(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionToggleFullScreen(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionShowPythonDialog(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionPluginListSeparator(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionManagePlugins(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionShowSelectedLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionHideDeselectedLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionToggleSelectedLayersIndependently(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionToggleSelectedLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionHideSelectedLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionShowAllLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionHideAllLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRemoveAllFromOverview(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddAllToOverview(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddToOverview(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionLayerProperties(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionDuplicateLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionLayerSaveAs(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCancelAllEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCancelEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRollbackAllEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionRollbackEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSaveAllEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSaveEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAllEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSaveActiveLayerEdits(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionToggleEditing(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionOpenStatisticalSummary(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionOpenFieldCalculator(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionOpenTable(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionPasteLayerStyle(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCopyLayerStyle(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddAmsLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddAfsLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddPointCloudLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddVectorTileLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddXyzLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddWmsLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddPgLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddRasterLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddOgrLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionNewVectorLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionDraw(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionShowBookmarks(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionNewBookmark(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionMapTips(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomActualSize(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomNext(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomLast(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomToSelected(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomToLayers(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomToLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomFullExtent(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionMeasureArea(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionMeasure(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionFeatureAction(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionIdentify(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSelectRadius(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSelectFreehand(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSelectPolygon(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSelectRectangle(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSelect(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomOut(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionZoomIn(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionPanToSelected(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionPan(self) -> Optional[QtWidgets.QAction]:
        ...

    def mapToolActionGroup(self) -> Optional[QtWidgets.QActionGroup]:
        ...

    def actionVertexToolActiveLayer(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionVertexTool(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionDeletePart(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionDeleteRing(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSimplifyFeature(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddPart(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddRing(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSplitParts(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSplitFeatures(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionMoveFeature(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionDeleteSelected(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionAddFeature(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionPasteFeatures(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCopyFeatures(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCutFeatures(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionExit(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionShowLayoutManager(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionCreatePrintLayout(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionProjectProperties(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSaveMapAsImage(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSaveProjectAs(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionSaveProject(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionOpenProject(self) -> Optional[QtWidgets.QAction]:
        ...

    def actionNewProject(self) -> Optional[QtWidgets.QAction]:
        ...

    def webToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def databaseToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def vectorToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def rasterToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def helpToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def pluginToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def selectionToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def attributesToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def shapeDigitizeToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def advancedDigitizeToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def digitizeToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def mapNavToolToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def openDataSourceManagerPage(self, pageName: Optional[str]) -> None:
        ...

    def dataSourceManagerToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def layerToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def fileToolBar(self) -> Optional[QtWidgets.QToolBar]:
        ...

    def helpMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def windowMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def firstRightStandardMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def webMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def vectorMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def databaseMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def rasterMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def pluginHelpMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def pluginMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def settingsMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def addLayerMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def newLayerMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def layerMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def viewMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def editMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def removeProjectExportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def addProjectExportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def removeProjectImportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def addProjectImportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        ...

    def projectImportExportMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def projectMenu(self) -> Optional[QtWidgets.QMenu]:
        ...

    def cadDockWidget(self) -> Optional["QgsAdvancedDigitizingDockWidget"]:
        ...

    def defaultStyleSheetFont(self) -> QtGui.QFont:
        ...

    def defaultStyleSheetOptions(self) -> dict[str, Any]:
        ...

    def openLayoutDesigners(self) -> list["QgsLayoutDesignerInterface"]:
        ...

    def messageBar(self) -> Optional["QgsMessageBar"]:
        return self._messageBar

    def mainWindow(self) -> Optional[QtWidgets.QWidget]:
        return self._mainWindow

    def layerTreeCanvasBridge(self) -> Optional["QgsLayerTreeMapCanvasBridge"]:
        ...

    def activeDecorations(self) -> list[qgis_core.QgsMapDecoration]:
        ...

    def mapCanvas(self) -> Optional["QgsMapCanvas"]:
        return self.canvas

    def activeLayer(self) -> Optional[qgis_core.QgsMapLayer]:
        return (
            QgsProject.instance().mapLayer(self._active_layer_id)
            if self._active_layer_id
            else None
        )

    def editableLayers(self, modified: bool = ...) -> list[qgis_core.QgsMapLayer]:
        ...

    def iconSize(self, dockedToolbar: bool = ...) -> QtCore.QSize:
        ...

    def closeMapCanvas(self, name: Optional[str]) -> None:
        ...

    def createNewMapCanvas(self, name: Optional[str]) -> Optional["QgsMapCanvas"]:
        ...

    def mapCanvases(self) -> list["QgsMapCanvas"]:
        ...

    def removeCustomActionForLayerType(
        self, action: Optional[QtWidgets.QAction]
    ) -> bool:
        ...

    def addCustomActionForLayer(
        self,
        action: Optional[QtWidgets.QAction],
        layer: Optional[qgis_core.QgsMapLayer],
    ) -> None:
        ...

    def addCustomActionForLayerType(
        self,
        action: Optional[QtWidgets.QAction],
        menu: Optional[str],
        type: qgis_core.Qgis.LayerType,
        allLayers: bool,
    ) -> None:
        ...

    def layerTreeView(self) -> Optional["QgsLayerTreeView"]:
        ...

    def pluginManagerInterface(self) -> Optional["QgsPluginManagerInterface"]:
        ...
