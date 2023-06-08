# pytest-qgis

[![PyPI version](https://badge.fury.io/py/pytest-qgis.svg)](https://badge.fury.io/py/pytest-qgis)
[![Downloads](https://img.shields.io/pypi/dm/pytest-qgis.svg)](https://pypistats.org/packages/pytest-qgis)
![CI](https://github.com/GispoCoding/pytest-qgis/workflows/CI/badge.svg)
[![Code on Github](https://img.shields.io/badge/Code-GitHub-brightgreen)](https://github.com/GispoCoding/pytest-qgis)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![codecov.io](https://codecov.io/github/GispoCoding/pytest-qgis/coverage.svg?branch=main)](https://codecov.io/github/GispoCoding/pytest-qgis?branch=main)

A [pytest](https://docs.pytest.org) plugin for testing QGIS python plugins.

## Features

This plugin makes it easier to write QGIS plugin tests with the help of some fixtures and hooks:

### Fixtures

* `qgis_app` returns and eventually exits fully
  configured [`QgsApplication`](https://qgis.org/pyqgis/master/core/QgsApplication.html). This fixture is called
  automatically on the start of pytest session.
* `qgis_bot` returns a [`QgisBot`](#qgisbot), which holds common utility methods for interacting with QGIS. Also
  fixture `module_qgis_bot` in module scope is provided.
* `qgis_canvas` returns [`QgsMapCanvas`](https://qgis.org/pyqgis/master/gui/QgsMapCanvas.html).
* `qgis_parent` returns the QWidget used as parent of the `qgis_canvas`
* `qgis_iface` returns stubbed [`QgsInterface`](https://qgis.org/pyqgis/master/gui/QgisInterface.html)
* `qgis_new_project` makes sure that all the map layers and configurations are removed. This should be used with tests
  that add stuff to [`QgsProject`](https://qgis.org/pyqgis/master/core/QgsProject.html).
* `qgis_processing` initializes the processing framework. This can be used when testing code that
  calls `processing.run(...)`.
* `qgis_version` returns QGIS version number as integer.
* `qgis_world_map_geopackage` returns Path to the world_map.gpkg that ships with QGIS
* `qgis_countries_layer` returns Natural Earth countries layer from world.map.gpkg as QgsVectorLayer

### Markers

* `qgis_show_map` lets developer inspect the QGIS map visually at the teardown of the test. Full signature of the marker
  is:
  ```python
  @pytest.mark.qgis_show_map(timeout: int = 30, add_basemap: bool = False, zoom_to_common_extent: bool = True, extent: QgsRectangle = None)
  ```
    * `timeout` is the time in seconds until the map is closed.
    * `add_basemap` when set to True, adds Natural Earth countries layer as the basemap for the map.
    * `zoom_to_common_extent` when set to True, centers the map around all layers in the project.
    * `extent` is alternative to `zoom_to_common_extent` and lets user specify the extent
      as [`QgsRectangle`](https://qgis.org/pyqgis/master/core/QgsRectangle.html)

Check the marker api [documentation](https://docs.pytest.org/en/latest/mark.html)
and [examples](https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules) for the ways
markers can be used.

### Utility tools

* `clean_qgis_layer` decorator found in `pytest_qgis.utils` is a decorator which can be used with `QgsMapLayer` fixtures
  to ensure that they are cleaned properly if they are used but not added to the `QgsProject`. This is only needed with
  layers with other than memory provider.
   ```python
   # conftest.py or start of a test file
   import pytest
   from pytest_qgis.utils import clean_qgis_layer
   from qgis.core import QgsVectorLayer

   @pytest.fixture()
   @clean_qgis_layer
   def some_layer() -> QgsVectorLayer:
     return QgsVectorLayer("layer_file.geojson", "some layer")

   ```

### Hooks

* `pytest_configure` hook is used to initialize and
  configure [`QgsApplication`](https://qgis.org/pyqgis/master/core/QgsApplication.html). With QGIS >= 3.18 it is also
  used to patch `qgis.utils.iface` with `qgis_iface` automatically.

  > Be careful not to import modules importing `qgis.utils.iface` in the root of conftest, because the `pytest_configure` hook has not yet patched `iface` in that point. See [this issue](https://github.com/GispoCoding/pytest-qgis/issues/35) for details.

### Command line options

* `--qgis_disable_gui` can be used to disable graphical user interface in tests. This speeds up the tests that use Qt
  widgets of the plugin.
* `--qgis_disable_init` can be used to prevent QGIS (QgsApplication) from initializing. Mainly used in internal testing.

### ini-options

* `qgis_qui_enabled` whether the QUI will be visible or not. Defaults to `True`. Command line
  option `--qgis_disable_gui` will override this.
* `qgis_canvas_width` width of the QGIS canvas in pixels. Defaults to 600.
* `qgis_canvas_height` height of the QGIS canvas in pixels. Defaults to 600.

## QgisBot

Class to hold common utility methods for interacting with QGIS. Here are some of the methods:

* `create_feature_with_attribute_dialog` method to create a feature with default values using QgsAttributeDialog. This
  ensures that all the default values are honored and for example boolean fields are either true or false, not null.
* `get_qgs_attribute_dialog_widgets_by_name` function can be used to get dictionary of the `QgsAttributeDialog` widgets.
  Check the test [test_qgis_ui.py::test_attribute_dialog_change](./tests/visual/test_qgis_ui.py) for a usage example.

## Requirements

This pytest plugin requires QGIS >= 3.16 to work though it might work with older versions.

## Installation

Install with `pip`:

```bash
pip install pytest-qgis
```

## Development environment

1. Create a virtual environment and activate it.
2. `pip install pip-tools`
3. `pip-sync requirements.txt requirements-dev.txt`
4. `pre-commit install`

### Updating dependencies

1. `pip-compile --upgrade`
2. `pip-compile --upgrade requirements-dev.in`

## Contributing

Contributions are very welcome.

## License

Distributed under the terms of the `GNU GPL v2.0` license, "pytest-qgis" is free and open source software.
