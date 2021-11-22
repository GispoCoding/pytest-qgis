# pytest-qgis

[![PyPI version](https://badge.fury.io/py/pytest-qgis.svg)](https://badge.fury.io/py/pytest-qgis)
[![Downloads](https://img.shields.io/pypi/dm/pytest-qgis.svg)](https://pypistats.org/packages/pytest-qgis)
![CI](https://github.com/GispoCoding/pytest-qgis/workflows/CI/badge.svg)
[![Code on Github](https://img.shields.io/badge/Code-GitHub-brightgreen)](https://github.com/GispoCoding/pytest-qgis)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A [pytest](https://docs.pytest.org) plugin for testing QGIS python plugins.

## Features

This plugin makes it easier to write QGIS plugin tests with the help of some fixtures and hooks:

### Fixtures

* `qgis_app` returns and eventually exits fully
  configured [`QgsApplication`](https://qgis.org/pyqgis/master/core/QgsApplication.html). This fixture is called
  automatically on the start of pytest session.
* `qgis_canvas` returns [`QgsMapCanvas`](https://qgis.org/pyqgis/master/gui/QgsMapCanvas.html).
* `qgis_iface` returns stubbed [`QgsInterface`](https://qgis.org/pyqgis/master/gui/QgisInterface.html)
* `new_project` makes sure that all the map layers and configurations are removed. This should be used with tests that
  add stuff to [`QgsProject`](https://qgis.org/pyqgis/master/core/QgsProject.html).
* `qgis_processing` initializes the processing framework. This can be used when testing code that
  calls `processing.run(...)`.

### Hooks

* `pytest_configure` hook is used to initialize and
  configure [`QgsApplication`](https://qgis.org/pyqgis/master/core/QgsApplication.html). With QGIS >= 3.18 it is also
  used to patch `qgis.utils.iface` with `qgis_iface` automatically.

### Command line options

* `--qgis_disable_gui` can be used to disable graphical user interface in tests. This speeds up the tests that use Qt
  widgets of the plugin.

### ini-options

* `qgis_qui_enabled` whether the QUI will be visible or not. Defaults to `True`. Command line
  option `--qgis_disable_gui` will override this.
* `qgis_canvas_width` width of the QGIS canvas in pixels. Defaults to 600.
* `qgis_canvas_height` height of the QGIS canvas in pixels. Defaults to 600.
* `qgis_initialize_automatically` whether to autouse `qgis_app` fixture or not. Mainly used in internal testing.

## Requirements

This pytest plugin requires QGIS >= 3.10 to work.

## Installation

Install with `pip`:

```bash
pip install pytest-qgis
```

## Development environment

1. Create a virtual environment and activate it.
2. `pip install pip-tools`
3. `pip-sync requirements.txt requirements-dev.txt`

### Updating dependencies

1. `pip-compile --upgrade`
2. `pip-compile --upgrade requirements-dev.in`

## Contributing

Contributions are very welcome.

## License

Distributed under the terms of the `GNU GPL v2.0` license, "pytest-qgis" is free and open source software.
