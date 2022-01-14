# Summary
The purpose of this software is to make quality of expirence (QoE) measurements 
for push-to-talk (PTT) communications systems. This python package contains a 
GUI for making these measurements. This GUI is the recommended way to run the 
following QoE measurements:

* [mouth 2 ear latency](https://nvlpubs.nist.gov/nistpubs/ir/2018/NIST.IR.8206.pdf)
* [Access Time](https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8275.pdf)
* Probability of Successful Delivery
* [Intelligibility](https://www.its.bldrdoc.gov/publications/download/Voran-ICASSP17.pdf)
* [Transmit Volume Optomization](https://doi.org/10.6028/NIST.TN.2171)



# MCV-QoE-GUI Python Package

The `mcvqoe` GUI package depends on the following other PSCR published packages:

* <https://github.com/usnistgov/mcvqoe-base>
* <https://github.com/usnistgov/abcmrt16>
* <https://github.com/usnistgov/mouth2ear>
* <https://github.com/usnistgov/accessTime>
* <https://github.com/usnistgov/psud>
* <https://github.com/usnistgov/intelligibility>
* <https://github.com/usnistgov/MCV-QOE-TVO>

They must be installed before the `mcvqoe` package is installed. In addition the 
following dependencies can be found in the Python Package index (PyPi) and will 
be downloaded automatically, if needed, when `mcvqoe` is installed:

* numpy
* pandas
* dash
* flask
* plotly
* requests
* pillow

To install the package, clone this repository and run the following from the 
root of the git repository:

```
pip install .
```

## Running with terminal output

On windows, the GUI entry point, `mcvqoe` causes all console output from the GUI 
to be lost (on windows). If the input is desired on windows the GUI can also be 
run with the following:

```
python -m mcvqoe.hub
```

## Evaluation GUI

The evaluation GUI can be run using the evaluation GUI entry point:

```
mcvqoe-evaluation
```

# License

This software was developed by employees of the National Institute of Standards 
and Technology (NIST), an agency of the Federal Government. Pursuant to title 17 
United States Code Section 105, works of NIST employees are not subject to 
copyright protection in the United States and are considered to be in the public 
domain. Permission to freely use, copy, modify, and distribute this software and 
its documentation without fee is hereby granted, provided that this notice and 
disclaimer of warranty appears in all copies.

THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER 
EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY 
THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, 
AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY 
WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE 
FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR 
CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED 
WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR 
OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR 
OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE 
RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
