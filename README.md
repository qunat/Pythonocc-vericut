# pythonocc-vericut
TPythonocc vericut is a NC machining simulation software based on pythonocc 3D kernel




![alt tag](http://cad-upyun.test.upcdn.net/Pythonocc-vericut/pythonocc-vericut-3.png)
![alt tag](http://cad-upyun.test.upcdn.net/Pythonocc-vericut/pythonocc-vericut-2.png)
![alt tag](http://cad-upyun.test.upcdn.net/Pythonocc-vericut/pythonocc-vericut-1.png)
![alt tag](http://cad-upyun.test.upcdn.net/Pythonocc-vericut/pythonocc-vericut-4.png)

pythonocc-core
--------------

About
-----

pythonocc is a python package whose purpose is to provide 3D modeling
features. It is intended to CAD/PDM/PLM and BIM related development.

Latest release : [pythonocc-core 7.4.0 (february 2020)](https://github.com/tpaviot/pythonocc-core/releases/tag/7.4.0)

Features
--------
pythonocc provides the following features:

*   a full access from Python to almost all af the thousand OpenCascade C++ classes. Classes and methods/functions share the same names, and, as possible as it can be, the same signature

*   3D visualization from the most famous Python Gui (pyQt, PySide1 and 2, wxPython)

*   3D visualization in a web browser using WebGl and/or x3dom renderers

*   3D visualization and work within a jupyter notebook

*   Various utility Python classes/methods for DataExchange, Topology operations, intertia computations etc.



# first create an environment
```
conda create --name=pyoccenv python=3.7
source activate pyoccenv
conda install -c conda-forge pythonocc-core=7.4
```

#Run it 
```
git clone https://github.com/qunat/Pythonocc-vericur.git
conda activate your environment
cd pythonocc-vericut
python BaseGui.py
```



