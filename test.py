from __future__ import print_function

from OCC.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Circ
from OCC.GeomAPI import GeomAPI_PointsToBSpline
from OCC.TColgp import TColgp_Array1OfPnt
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeEdge,         
BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.BRepOffsetAPI import BRepOffsetAPI_MakePipe

from OCC.Display.SimpleGui import init_display
display, start_display, add_menu, add_function_to_menu = init_display()

def pipe():
# the bspline path, must be a wire
# This will later be in a for loop but this is merely to validate the method         
#using three different points.

array = TColgp_Array1OfPnt(1,2)
makeWire = BRepBuilderAPI_MakeWire()

point1 = gp_Pnt(0,0,0)
point2 = gp_Pnt(0,0,1)
array.SetValue(1, point1)
array.SetValue(2, point2)
spline = GeomAPI_PointsToBSpline(array).Curve()
edge = BRepBuilderAPI_MakeEdge(spline).Edge()

makeWire.Add(edge)

point1 = gp_Pnt(0, 0, 1)
point2 = gp_Pnt(0, 1, 2)
array.SetValue(1, point1)
array.SetValue(2, point2)
spline = GeomAPI_PointsToBSpline(array).Curve()
edge = BRepBuilderAPI_MakeEdge(spline).Edge()

makeWire.Add(edge)

point1 = gp_Pnt(0, 1, 2)
point2 = gp_Pnt(0, 2, 2)
array.SetValue(1, point1)
array.SetValue(2, point2)
spline = GeomAPI_PointsToBSpline(array).Curve()
edge = BRepBuilderAPI_MakeEdge(spline).Edge()

makeWire.Add(edge)

makeWire.Build()
wire = makeWire.Wire()

# the bspline profile. Profile mist be a wire/face
point = gp_Pnt(0,0,0)
dir = gp_Dir(0,0,1)
circle = gp_Circ(gp_Ax2(point,dir), 0.2)
profile_edge = BRepBuilderAPI_MakeEdge(circle).Edge()
profile_wire = BRepBuilderAPI_MakeWire(profile_edge).Wire()
profile_face = BRepBuilderAPI_MakeFace(profile_wire).Face()

# pipe
pipe = BRepOffsetAPI_MakePipe(wire, profile_face).Shape()

display.DisplayShape(profile_edge, update=False)
display.DisplayShape(wire, update=True)
display.DisplayShape(pipe, update=True)

if __name__ == '__main__':
pipe()
start_display()