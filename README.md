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

This plugin makes it easier to write QGIS plugin tests with the help of some fixtures:

* `qgis_app` initializes and returns fully configured [`QgsApplication`](https://qgis.org/pyqgis/master/core/QgsApplication.html). This fixture is called
    automatically on the start of pytest session.
* `qgis_canvas` initializes and returns [`QgsMapCanvas`](https://qgis.org/pyqgis/master/gui/QgsMapCanvas.html)
* `qgis_iface` returns mocked [`QgsInterface`](https://qgis.org/pyqgis/master/gui/QgisInterface.html)
* `new_project` makes sure that all the map layers and configurations are removed. This should be used with tests that
    add stuff to [`QgsProject`](https://qgis.org/pyqgis/master/core/QgsProject.html).
* `qgis_processing` initializes the processing framework. This can be used when testing code that calls `processing.run(...)`.


## Requirements

This pytest plugin requires QGIS >= 3.10 to work.


## Installation

Install with `pip`:

```bash
pip install pytest-qgis
```


## Contributing

Contributions are very welcome.

## License

Distributed under the terms of the `GNU GPL v2.0` license, "pytest-qgis" is free and open source software.
