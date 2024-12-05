# VIIRS/NPP Surface Reflectance Daily L2G Global 1 km and 500 m SIN Grid Search and Download Utility

This tool uses the `earthaccess` library to search and download VNP09GA collection 2 surface reflectance remote sensing data products from the Visible Infrared Imaging Radiometer Suite (VIIRS).

[Gregory H. Halverson](https://github.com/gregory-halverson-jpl) (they/them)<br>
[gregory.h.halverson@jpl.nasa.gov](mailto:gregory.h.halverson@jpl.nasa.gov)<br>
NASA Jet Propulsion Laboratory 329G

## Installation

Install the `VNP09GA-002` package with a dash in the name from PyPi using pip:

```
pip install VNP09GA-002
```

## Usage

Import the `VNP09GA_002` package with an underscore in the name:

```
import VNP09GA_002
```

See the [example notebook](Searching%20VNP09GA.002%20with%20earthaccess.ipynb) for usage.

## References

NASA Land Processes Distributed Active Archive Center (LP DAAC). 2021. VIIRS/NPP Surface Reflectance Daily L2G Global 1 km and 500 m SIN Grid V002. NASA EOSDIS Land Processes DAAC. doi:[10.5067/VIIRS/VNP09GA.002](https://doi.org/10.5067/VIIRS/VNP09GA.002).
