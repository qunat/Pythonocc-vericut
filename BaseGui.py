# -*- coding: utf-8 -*-
import copy
import copyreg
import logging
import os
import sys
import threading
import time,re
#from PyQt5 import QtSvg
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepTools import breptools_Write
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Pnt,gp_Dir,gp_Circ,gp_Ax2,gp_Lin,gp_Ax1
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Display.OCCViewer import OffscreenRenderer
from OCC.Display.backend import load_backend, get_qt_modules
from OCC.Extend.TopologyUtils import TopologyExplorer
from PyQt5.QtWidgets import QHBoxLayout, QDockWidget, \
	QListWidget, QFileDialog
from module import G_Code_interpreter
from PyQt5 import QtCore, QtWidgets,Qt
from graphics import GraphicsView, GraphicsPixmapItem
from OCC.Core.TopAbs import (TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX,
							 TopAbs_SHELL, TopAbs_SOLID)
from module.Get_Linear_interpolation import Get_Linear_interpolation_point,Get_Arc_interpolation_point
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe
from PyQt5.QtWidgets import QApplication, QStyleFactory
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge,BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.GC import GC_MakeSegment, GC_MakeCircle, GC_MakeArcOfCircle, GC_MakeEllipse
import math
from OCC.Core.BOPAlgo import BOPAlgo_RemoveFeatures
from OCC.Core.BRepTools import breptools_Read
from OCC.Core.BRep import BRep_Builder
from OCC.Core import BRepTools
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
#------------------------------------------------------------开始初始化环境
log = logging.getLogger(__name__)
def check_callable(_callable):
	if not callable(_callable):
		raise AssertionError("The function supplied is not callable")
backend_str=None
size=[850, 873]
display_triedron=True
background_gradient_color1=[206, 215, 222]
background_gradient_color2=[128, 128, 128]
if os.getenv("PYTHONOCC_OFFSCREEN_RENDERER") == "1":
	# create the offscreen renderer
	offscreen_renderer = OffscreenRenderer()


	def do_nothing(*kargs, **kwargs):
		""" takes as many parameters as you want,
		ans does nothing
		"""
		pass


	def call_function(s, func):
		""" A function that calls another function.
		Helpfull to bypass add_function_to_menu. s should be a string
		"""
		check_callable(func)
		log.info("Execute %s :: %s menu fonction" % (s, func.__name__))
		func()
		log.info("done")

	# returns empty classes and functions
used_backend = load_backend(backend_str)
log.info("GUI backend set to: %s", used_backend)
#------------------------------------------------------------初始化结束
from OCC.Display.qtDisplay import qtViewer3d
from module import MainGui
from PyQt5.QtGui import QPixmap
QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()
from OCC.Extend.DataExchange import read_step_file,write_step_file,read_stl_file,read_iges_file,read_step_file_with_names_colors
from OCC.Core.TopoDS import TopoDS_Shape,TopoDS_Builder,TopoDS_Compound,topods_CompSolid




class Mywindown(QtWidgets.QMainWindow,MainGui.Ui_MainWindow):
	pass
	def __init__(self, parent=None):
		super(Mywindown,self).__init__(parent)
		self.Cutting_result = None
		self.setupUi(self)
		#3D显示设置
		self.canva = qtViewer3d(self.tab_4)#链接3D模块
		self.setWindowTitle("pythonocc_vericui_仿真软件")
		#self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
		self.setFixedSize(self.width(), self.height());
		self.canva.setGeometry(QtCore.QRect(0, 0, 541, 400))
		self.centerOnScreen()
		#------------------------------------------------------------------视图设置
		self.quit.triggered.connect(self.Quit)
		self.actionView_Right.triggered.connect(self.View_Right)
		self.actionView_Left.triggered.connect(self.View_Left)
		self.actionView_Top.triggered.connect(self.View_Top)
		self.actionView_Bottom.triggered.connect(self.View_Bottom)
		self.actionView_Front.triggered.connect(self.View_Front)
		self.actionView_Iso.triggered.connect(self.View_Iso)

		#--------------------------------------------------------------状态栏
		self.statusBar().showMessage('状态：软件运行正常')
		self.pushButton_2.clicked.connect(self.Import_NC_Code)
		#self.pushButton.clicked.connect(self.Automatic_run)
		self.pushButton_3.clicked.connect(self.G_code_run)#运行仿真
		self.pushButton.clicked.connect(self.Mill_cut_Simulation)#切削仿真
		self.pushButton_4.clicked.connect(self.pause_continun_fun)#暂停
		self.pushButton_5.clicked.connect(self.Create_Blank)#创建毛坯
		self.pushButton_6.clicked.connect(self.Delete_Blank)#删除毛坯
		self.pushButton_7.clicked.connect(self.finish_button_fun)  # 结束仿真
		self.pushButton_8.clicked.connect(self.clear_path_button_fun)#清理现有界面
		#---------------------------------------------------------------菜单栏
		self.import_machone_model.triggered.connect(self.Import_machine_model)
		self.import_machining_part.triggered.connect(self.Import_machining_part)

		#--------------------------------------------------------------控件更新信号
		#self.comboBox_3.currentTextChanged.connect(self.updata_show)
		#self.comboBox_4.currentTextChanged.connect(self.updata_show_)
		#self.tabWidget_2.currentChanged['int'].connect(self.Refresh)  # 切换时刷新

		#-----------------------------------------------------------------------初始化变量
		self.shape = TopoDS_Shape
		self.filename=str()
		self.pause=1
		self.interpreter_G_code=G_Code_interpreter.G_code_interpreter()
		self.pause = 1  # 暂停信号
		self.finish = 1  # 结束信号
		self.clear_path = 1  # 重新开始信号
		self.fitall = 1  # 全显一次信号

	def changeEvent(self, e):
		if e.type() == QtCore.QEvent.WindowStateChange:
			if self.isMinimized():
				# print("窗口最小化")
				#self.canva._display.Repaint()
				pass
			elif self.isMaximized():
				pass
				# print("窗口最大化")
				#self.canva._display.Repaint()
			elif self.isFullScreen():
				# print("全屏显示")
				pass
			elif self.isActiveWindow():
				# print("活动窗口")
				self.canva._display.Repaint()
				pass

	def View_Bottom(self):
		pass
		self.canva._display.View_Bottom()
	def View_Front(self):
		pass
		self.canva._display.View_Front()
	def View_Iso(self):
		pass
		self.canva._display.View_Iso()

	def View_Left(self):
		pass
		self.canva._display.View_Left()
	def View_Right(self):
		pass
		self.canva._display.View_Right()

	def View_Top(self):
		pass
		self.canva._display.View_Top()

	def centerOnScreen(self):
		'''Centers the window on the screen.'''
		resolution = QtWidgets.QApplication.desktop().screenGeometry()
		x = (resolution.width() - self.frameSize().width()) / 2
		y = (resolution.height() - self.frameSize().height()) / 2
		self.move(x, y)

	def Refresh(self):
		self.canva._display.Repaint()

	def Import_NC_Code(self):  # 导入NC程序
		try:
			self.chose_document = QFileDialog.getOpenFileName(self, '打开文件', './',
															  " NC files(*.nc , *.ngc);;(*.cnc);;(*.prim);;")  # 选择转换的文价夹
			filepath = self.chose_document[0]  # 获取打开文件夹路径
			self.interpreter_G_code.Read_nc_code(filepath=filepath)
			file = open(filepath, "r")
			nc_code_list = file.readlines()
			# textBrowser内容清零
			self.textBrowser.clear()
			self.textBrowser_list = []
			self.statusBar().showMessage('状态：G代码加载中.......')
			for i in nc_code_list:
				i = i.strip()
				self.textBrowser.append(i)
				self.textBrowser_list.append(i)
				QtWidgets.QApplication.processEvents()
			# 返回开头
			self.statusBar().showMessage('状态：G代码加载完成')
			self.textBrowser.ensureCursorVisible()  # 游标可用
			self.cursor = self.textBrowser.textCursor()  # 设置游标
			# self.tetxBrowser.moveCursor(self.cursor.setPos(0,0))  # 光标移到最后，这样就会自动显示出来
			self.cursor.setPosition(0)
			self.textBrowser.setTextCursor(self.cursor)
			QtWidgets.QApplication.processEvents()  # 一定加上这个功能，不然有卡顿
		except Exception as e:
			print(e)
			pass

	def Import_machining_part(self):  # 导入加工数据
		try:
			self.chose_document = QFileDialog.getOpenFileName(self, '打开文件', './',
															  " STP files(*.stp , *.step);;(*.iges);;(*.stl)")  # 选择转换的文价夹
			filepath = self.chose_document[0]  # 获取打开文件夹路径
			# 判断文件类型 选择对应的导入函数
			end_with = str(filepath).lower()
			if end_with.endswith(".step") or end_with.endswith("stp"):
				self.import_shape = read_step_file(filepath)

			elif end_with.endswith("iges"):
				self.import_shape = read_iges_file(filepath)
			elif end_with.endswith("stl"):
				self.import_shape = read_stl_file(filepath)

			try:
				# self.canva._display.Context.Remove(self.show[0], True)
				self.acompound=self.import_shape
				self.show = self.canva._display.DisplayShape(self.import_shape, color="WHITE", update=True)
				self.canva._display.FitAll()
			except:
				pass
				#self.show = self.canva._display.DisplayShape(self.import_shape, color="WHITE", update=True)
				#self.canva._display.FitAll()
				pass
			self.statusbar.showMessage("状态：打开成功")  ###
			self.statusBar().showMessage('状态：软件运行正常')
		except:
			pass
	def Import_machine_model(self):  # 导入机床模型
		pass
		# 清除之前数据
		try:
			try:
				self.Machine_spindle_shape=read_step_file("./machine/仿真机床/Machine_spindle.stp")
				self.Machine_work_table=read_step_file("./machine/仿真机床/Machine_work_table.stp")
				# self.canva._display.Context.Remove(self.show[0], True)
				#self.acompound=self.import_shape
				self.canva._display.EraseAll()
				self.canva._display.hide_triedron()
				self.canva._display.display_triedron()
				self.show_Machine_spindle_shape = self.canva._display.DisplayShape(self.Machine_spindle_shape, color="WHITE", update=True)
				self.show_Machine_work_table = self.canva._display.DisplayShape(self.Machine_work_table, color="WHITE", update=True)
				#主轴移动到安全距离
				self.Axis = gp_Trsf()  # 变换类
				self.Axis.SetTranslation(gp_Vec(0, 0, 50))  # 设置变换类为平移
				self.Axis_Toploc = TopLoc_Location(self.Axis)
				self.canva._display.Context.SetLocation(self.show_Machine_spindle_shape[0], self.Axis_Toploc)
				self.canva._display.Context.UpdateCurrentViewer()
				self.canva._display.FitAll()
				self.statusBar().showMessage("状态：机床载入成功")  ###
			except:
				pass
				#self.show = self.canva._display.DisplayShape(self.import_shape, color="WHITE", update=True)
				#self.canva._display.FitAll()

			self.statusBar().showMessage('状态：软件运行正常')
		except:
			pass
	def pause_continun_fun(self):
		self.pause = self.pause * -1
		if self.pause == -1:
			self.pushButton_4.setText("继续")
			self.statusBar().showMessage('状态：仿真暂停')
		else:
			self.pushButton_4.setText("暂停")
			self.statusBar().showMessage('状态：仿真进行中')
	def finish_button_fun(self):
		self.finish=-1
		self.fitall=1
		self.textBrowser.ensureCursorVisible()  # 游标可用
		self.cursor = self.textBrowser.textCursor()  # 设置游标
		# self.tetxBrowser.moveCursor(self.cursor.setPos(0,0))  # 光标移到最后，这样就会自动显示出来
		self.cursor.setPosition(0)
		self.textBrowser.setTextCursor(self.cursor)
		QtWidgets.QApplication.processEvents()  # 一定加上这个功能，不然有卡顿
	def clear_path_button_fun(self):
		self.clear_path=-1
		self.fitall=1
		self.canva._display.EraseAll()
		self.canva._display.hide_triedron()
		self.canva._display.display_triedron()
		self.canva._display.Repaint()

	def G_code_run_Thread(self):
		t=threading.Thread(target=self.G_code_run,args=[])
		t.start()
	def G_code_run(self):
		# self.textBrowser.ensureCursorVisible()  # 游标可用
		# cursor = self.textBrowser.cursor()  # 设置游标
		self.machining = {"spindle_speed": 0, "feet_speed": 0, "status_G": "G0", "x": 0, "y": 0, "z": 0, "x0": 0,
						  "y0": 0, "z0": 0, "i": 0, "j": 0, "k": 0}
		# new_Create_path=Create_Path()
		self.textBrowser.clear()
		self.my_cylinder = BRepPrimAPI_MakeCylinder(10.0, 50).Shape()
		self.tool = TopoDS_Shape(self.my_cylinder)  # 建立刀具
		for code, G_Ccode in zip(self.interpreter_G_code.Out_NC_simple, self.textBrowser_list):
			try:
				if self.pause == -1:
					while True:
						QtWidgets.QApplication.processEvents()
						self.statusBar().showMessage('状态：仿真暂停')
						if self.pause == 1 or self.finish == -1 or self.clear_path == -1:
							break
					if self.finish == -1 or self.clear_path == -1:
						self.pushButton_4.setText("暂停")
						break
				#time.sleep(0.02)
				if code == []:
					continue
				print(code)
				#self.textBrowser.append(G_Ccode)
				
				self.textBrowser.setTextColor(QtGui.QColor(1,1,1))
				self.textBrowser.append(
					"<font color='red'>" + '{}'.format(code) + "<font>")
				
				if code[0] == "G01":
					x0 = float(self.machining["x0"])  # 当前X坐标
					y0 = float(self.machining["y0"])  # 当前y坐标
					z0 = float(self.machining["z0"])  # 当前z坐标
					x1 = float(code[1])  # 目标X坐标
					y1 = float(code[2])  # 目标X坐标
					z1 = float(code[3])  # 目标X坐标
					path_pnt_list = Get_Linear_interpolation_point([x0, y0, z0], [x1, y1, z1], step=0.31)
					# print(path_pnt_list)
				elif code[0] == "G00":
					x0 = float(self.machining["x0"])  # 当前X坐标
					y0 = float(self.machining["y0"])  # 当前y坐标
					z0 = float(self.machining["z0"])  # 当前z坐标
					x1 = float(code[1])  # 目标X坐标
					y1 = float(code[2])  # 目标X坐标
					z1 = float(code[3])  # 目标X坐标
					path_pnt_list = [gp_Pnt(x1, y1, z1)]
					# print(path_pnt_list)
				elif code[0] == "G02" or code[0] == "G03":

					x0 = float(self.machining["x0"])  # 当前X坐标
					y0 = float(self.machining["y0"])  # 当前y坐标
					z0 = float(self.machining["z0"])  # 当前z坐标
					x1 = float(code[1])  # 目标X坐标
					y1 = float(code[2])  # 目标y坐标
					z1 = float(code[3])  # 目标z坐标
					i = float(code[4])  # 目标I坐标
					j = float(code[5])  # 目标J坐标
					k = float(code[6])  # 目标K坐标
					path_pnt_list = Get_Arc_interpolation_point([x0, y0, z0], [x1, y1, z1], [i, j, k])
					# self.canva._display.DisplayShape(path)
					print("显示成功")
				self.machining["x0"] = x1
				self.machining["y0"] = y1
				self.machining["z0"] = z1

				for path_pnt in path_pnt_list:
					pass
					x = path_pnt.X()
					y = path_pnt.Y()
					z = path_pnt.Z()
					self.Axis_move(distance_x=x, distance_y=y, distance_z=z)
					QtWidgets.QApplication.processEvents()  # 一定加上这个功能，不然有卡顿
					self.statusBar().showMessage('状态：仿真进行中')
					# self.tetxBrowser.moveCursor(self.cursor.setPos(0,0))  # 光标移到最后，这样就会自动显示出来
					# self.cursor.setPosition((self.textBrowser_list.index(code))*60)
					# self.textBrowser.setTextCursor(self.cursor)
					# QtWidgets.QApplication.processEvents()



			except Exception as e:
				print(e)
	def Mill_cut_Simulation(self):
		# self.textBrowser.ensureCursorVisible()  # 游标可用
		# cursor = self.textBrowser.cursor()  # 设置游标
		self.machining = {"spindle_speed": 0, "feet_speed": 0, "status_G": "G0", "x": 0, "y": 0, "z": 0, "x0": 0,
						  "y0": 0, "z0": 0,"i":0,"j":0,"k":0}
		# new_Create_path=Create_Path()
		self.textBrowser.clear()
		self.my_cylinder = BRepPrimAPI_MakeCylinder(10, 50).Shape()
		self.tool = TopoDS_Shape(self.my_cylinder)  # 建立刀具
		print("开始切削")
		for code,G_Ccode  in zip(self.interpreter_G_code.Out_NC_simple,self.textBrowser_list):
			try:
				if self.pause == -1:
					while True:
						QtWidgets.QApplication.processEvents()
						self.statusBar().showMessage('状态：仿真暂停')
						if self.pause == 1 or self.finish == -1 or self.clear_path == -1:
							break
					if self.finish == -1 or self.clear_path == -1:
						self.pushButton_4.setText("暂停")
						break
				#time.sleep(0.03)
				if code == []:
					continue
				self.textBrowser.append(G_Ccode)

				
				G_Ccode=G_Ccode.split(" ")
				print(G_Ccode,)
				start_time=time.time()
				if G_Ccode[0][0]=="G":
					if G_Ccode[0] in ["G00","G01","G02","G03"]:
						self.machining["status_G"]=G_Ccode[0]
				for code in G_Ccode:
					if code[0]=="X":
						self.machining["x"]=code.replace("X","")
					elif code[0]=="Y":
						self.machining["y"]=code.replace("Y","")
					elif code[0]=="Z":
						self.machining["z"]=code.replace("Z","")
					elif code[0]=="I":
						self.machining["i"]=code.replace("I","")
					elif code[0]=="J":
						self.machining["j"]=code.replace("J","")
					elif code[0]=="K":
						self.machining["k"]=code.replace("K","")
					

				
				#print(self.machining)
				if self.machining["status_G"]=="G01" :
					x0 = float(self.machining["x0"])  # 当前X坐标
					y0 = float(self.machining["y0"])  # 当前y坐标
					z0 = float(self.machining["z0"])  # 当前z坐标
					x1 = float(self.machining["x"])  # 目标X坐标
					y1 = float(self.machining["y"])  # 目标X坐标
					z1 = float(self.machining["z"])  # 目标X坐标
					path_pnt_list=Get_Linear_interpolation_point([x0,y0,z0],[x1,y1,z1],step=2)

					
				elif  self.machining["status_G"]=="G00":
					x0 = float(self.machining["x0"])  # 当前X坐标
					y0 = float(self.machining["y0"])  # 当前y坐标
					z0 = float(self.machining["z0"])  # 当前z坐标
					x1 = float(self.machining["x"])  # 目标X坐标
					y1 = float(self.machining["y"])  # 目标X坐标
					z1 = float(self.machining["z"])  # 目标X坐标
					path_pnt_list=Get_Linear_interpolation_point([x0,y0,z0],[x1,y1,z1],step=1)
					#print(path_pnt_list)
				elif self.machining["status_G"]=="G02" or self.machining["status_G"]=="G03":

					x0 = float(self.machining["x0"])  # 当前X坐标
					y0 = float(self.machining["y0"])  # 当前y坐标
					z0 = float(self.machining["z0"])  # 当前z坐标
					x1 = float(self.machining["x"])  # 目标X坐标
					y1 = float(self.machining["y"])  # 目标X坐标
					z1 = float(self.machining["z"])  # 目标X坐标
					i = float(self.machining["i"]) # 目标I坐标
					j = float(self.machining["j"])  # 目标j坐标
					k=float(self.machining["k"])  # 目标K坐标
					path_pnt_list=Get_Arc_interpolation_point([x0,y0,z0],[x1,y1,z1],[i,j,k],Direction=self.machining["status_G"])

					#self.canva._display.DisplayShape(path)
				x0=float(self.machining["x0"])#当前X坐标
				y0=float(self.machining["y0"])#当前X坐标
				z0=float(self.machining["z0"])#当前X坐标

				x=float(self.machining["x"])#目标X坐标
				y=float(self.machining["y"])#目标X坐标
				z=float(self.machining["z"])#目标X坐标

				if self.machining["status_G"] in ["G02","G03","G01"]:
					#print(path_pnt_list)
					print(x0,y0,z0,x,y,z)
					self.Create_sweep_tool_path(x0,y0,z0+self.offset_Z,x,y,z+self.offset_Z)

				self.machining["x0"] = self.machining["x"]
				self.machining["y0"] = self.machining["y"]
				self.machining["z0"] = self.machining["z"]

				
				
				end_time=time.time()
				#print("时间",end_time-start_time)
				for path_pnt_num in range(len(path_pnt_list)):
					pass
					try:
						#print("看这里",path_pnt_num)

						if path_pnt_num==0:
							continue

						x0=path_pnt_list[path_pnt_num-1].X()
						y0=path_pnt_list[path_pnt_num-1].Y()
						z0=path_pnt_list[path_pnt_num-1].Z()

						x=path_pnt_list[path_pnt_num].X()
						y=path_pnt_list[path_pnt_num].Y()
						z=path_pnt_list[path_pnt_num].Z()
						start_time=time.time()
						if self.machining["status_G"] in ["G02","G03","G01"]:
							#self.Create_sweep_tool_path(x0,y0,z0+self.offset_Z,x,y,z+self.offset_Z)
							self.Mill_cut(x, y, z+self.offset_Z)
							#self.Create_sweep_tool_path(x0,y0,z0+self.offset_Z,x,y,z+self.offset_Z)
						else:
							#self.Create_sweep_tool_path(x0,y0,z0+self.offset_Z,x,y,z+self.offset_Z)
							self.Mill_cut(x, y, z+self.offset_Z)

						end_time=time.time()
						#print("时间",end_time-start_time)
						QtWidgets.QApplication.processEvents()  # 一定加上这个功能，不然有卡顿
						self.statusBar().showMessage('状态：仿真进行中')
						# self.tetxBrowser.moveCursor(self.cursor.setPos(0,0))  # 光标移到最后，这样就会自动显示出来
						# self.cursor.setPosition((self.textBrowser_list.index(code))*60)
						# self.textBrowser.setTextCursor(self.cursor)
						# QtWidgets.QApplication.processEvents()
					except 	Exception as e:
						print(e)
						pass




			except Exception as e:
				print(e)




	def Axis_move(self,distance_x=None,distance_y=None,distance_z=None):
		pass
		try:
			self.Axis = gp_Trsf()  # 变换类
			self.Axis.SetTranslation(gp_Vec(distance_x, distance_y, distance_z))  # 设置变换类为平移
			self.Axis_Toploc = TopLoc_Location(self.Axis)
			self.tool.Location(self.Axis_Toploc)
			self.canva._display.Context.SetLocation(self.show_Machine_spindle_shape[0], self.Axis_Toploc)
			self.canva._display.Context.UpdateCurrentViewer()
		except  Exception as e:
			print(e)

	
	def Automatic_run(self,distance=[]):
		pass
		self.Mill_cut()


	def Automatic_run_threading(self):
		t=threading.Thread(target=self.Automatic_run,args=[])
		t.start()

	def Create_tool_profile(self,x0,y0,z0,x,y,z,tool_diameter=10,tool_height=30,mode=None):
		#create rectange 
		point0=[0,0,0]
		point1=[0,0,0]
		point2=[0,0,0]
		point3=[0,0,0]
		v1=gp_Vec(gp_Pnt(x0,y0,z0),gp_Pnt(x,y,z));#计算两点之间的向量
		print(v1.X(),v1.Y(),v1.Z())
		v2=v1.Rotated(gp_Ax1(gp_Pnt(x0,y0,z0),gp_Dir(0,0,1)),math.pi/2)#计算向量旋转90度的向量
		print(v2.X(),v2.Y(),v2.Z())
		v3=v2.Reversed()#计算向量反向的向量
		point0[0]=x0+tool_diameter/2*v2.X()#计算矩形的起点
		point0[1]=y0+tool_diameter/2*v2.Y()#计算矩形的起个点
		point0[2]=z0+tool_diameter/2*v2.Z()#计算矩形的起个点

		point3[0]=x0+tool_diameter/2*v3.X()#计算矩形的终点
		point3[1]=y0+tool_diameter/2*v3.Y()#计算矩形的起终点
		point3[2]=z0+tool_diameter/2*v3.Z()#计算矩形的起终点
		
		point1[0]=point0[0]
		point1[1]=point0[1]
		point1[2]=point0[2]+tool_height

		point2[0]=point3[0]
		point2[1]=point3[1]
		point2[2]=point3[2]+tool_height
	
		edge0=BRepBuilderAPI_MakeEdge(gp_Pnt(point0[0],point0[1],point0[2]),gp_Pnt(point1[0],point1[1],point1[2])).Edge()
		edge1=BRepBuilderAPI_MakeEdge(gp_Pnt(point1[0],point1[1],point1[2]),gp_Pnt(point2[0],point2[1],point2[2])).Edge()
		edge2=BRepBuilderAPI_MakeEdge(gp_Pnt(point2[0],point2[1],point2[2]),gp_Pnt(point3[0],point3[1],point3[2])).Edge()
		edge3=BRepBuilderAPI_MakeEdge(gp_Pnt(point3[0],point3[1],point3[2]),gp_Pnt(point0[0],point0[1],point0[2])).Edge()

		rectange=BRepBuilderAPI_MakeWire(edge0,edge1,edge2,edge3).Wire()
		#self.canva._display.DisplayShape(rectange)

		return rectange




	#@profile
	def Create_sweep_tool_path(self,x0,y0,z0,x,y,z,mode=None):
		#create leading line
		point1 = gp_Pnt(float(x0),float(y0),float(z0))
		point2 = gp_Pnt(float(x),float(y),float(z))
		edge = BRepBuilderAPI_MakeEdge(point1,point2).Edge()
		wire=BRepBuilderAPI_MakeWire(edge).Wire()
		
		ais_shape=AIS_Shape(edge)
		self.canva._display.Context.Display(ais_shape,True)
		self.canva._display.Context.UpdateCurrentViewer()
	
		#create profile 
		profile_wire=self.Create_tool_profile(x0,y0,z0,x,y,z)
		profile_face = BRepBuilderAPI_MakeFace(profile_wire).Face()
		self.pipe = BRepOffsetAPI_MakePipe(wire, profile_face).Shape()
		ais_shape=AIS_Shape(self.pipe)
		self.canva._display.Context.Display(ais_shape,True)
		return self.pipe


	def Mill_cut(self,x=0,y=0,z=0):
		try:
			self.Axis_move(distance_x=x, distance_y=y, distance_z=z)
			#Cutting_result = BRepAlgoAPI_Cut(self.Blank, self.tool)
			#Cutting_result.SimplifyResult()
			#self.Blank = Cutting_result.Shape()
			#self.show_Blank[0].SetShape(self.Blank)  # 将已经显示的零件设置成另外一个新零件
			#self.canva._display.Context.Redisplay(self.show_Blank[0], True, False)  # 重新计算更新已经显示的物体
		except Exception as e:
			pass
			print(e)
			self.statusBar().showMessage('错误：请确认机床组件已经导入')

	def Create_Blank(self):
		try:
			#self.Delete_Blank()
			L=float(self.lineEdit_8.text())
			W = float(self.lineEdit_9.text())
			H = float(self.lineEdit_10.text())
			self.Blank=BRepPrimAPI_MakeBox(L, W, H).Shape()
			self.Blank = TopoDS_Shape(self.Blank)
			T = gp_Trsf()
			location_X = -L/2 # 把键槽移动到合适的位置
			location_Y = -W / 2  # 把键槽移动到合适的位置
			T.SetTranslation(gp_Vec(location_X,location_Y, 0))
			loc = TopLoc_Location(T)
			self.Blank.Location(loc)
			self.show_Blank = self.canva._display.DisplayShape(self.Blank,transparency=0.5,update=True)

			change=self.show_Blank[0].Shape()


			self.offset_Z=H
			print(self.offset_Z)
		except Exception as e:
			print(e)
	def Delete_Blank(self):
		try:
			#self.canva._display.Context.Remove(self.show_Blank[0],True)
			#self.lineEdit_8.clear()
			#self.lineEdit_9.clear()
			#self.lineEdit_10.clear()
			t1=time.time()
			#self.canva._display.Context.Erase(self.show_Blank[0], True)
			#self.canva._display.Context.Remove(self.show_Blank[0],True)
			t2=time.time()
			print(t2-t1)

			box = BRepPrimAPI_MakeBox(float(self.lineEdit_8.text()), float(self.lineEdit_9.text()), float(self.lineEdit_10.text())).Shape()
			# Fillet
			fillet = BRepFilletAPI_MakeFillet(box)
			for e in TopologyExplorer(box).edges():
				fillet.Add(20, e)
			blended_box = ((fillet.Shape()))
			self.show_Blank[0].SetShape(blended_box)#将已经显示的零件设置成另外一个新零件
			self.canva._display.Context.Redisplay(self.show_Blank[0],True,False)#重新计算更新已经显示的物体
			self.canva._display.FitAll()
			#self.canva._display.Repaint()


		except Exception as e:
			print(e)
			pass
	def line_clicked(self, shp, *kwargs):
		try:
			if self.measure_signal == 1:
				self.canva._display.SetSelectionMode(TopAbs_SOLID)
				for i in shp:  # 获取最大尺寸
					self.select_shape = i
				self.measure_signal = 0

		except:
			pass

	def Quit(self):#退出
		self.close()

	def Vision(self):#版本显示
		pass

class Cnc_code_status_Show(object):
	def __init__(self,myself):
		pass





# following couple of lines is a tweak to enable ipython --gui='qt'
if __name__ == '__main__':
	app = QtWidgets.QApplication.instance()  # checks if QApplication already exists
	if not app:  # create QApplication if it doesnt exist
		app = QtWidgets.QApplication(sys.argv)
	#启动界面
	QApplication.setStyle(QStyleFactory.create('Fusion'))
	splash = QtWidgets.QSplashScreen(QtGui.QPixmap("Pic\\setup_pic.jpg"))#启动图片设置
	splash.show()
	splash.showMessage("软件启动中......")
	time.sleep(0.5)
	#--------------------
	win = Mywindown()
	win.show()
	win.centerOnScreen()
	win.canva.InitDriver()
	win.resize(size[0], size[1])
	win.canva.qApp = app

	display = win.canva._display
	display.display_triedron()
	display.register_select_callback(win.line_clicked)
	if background_gradient_color1 and background_gradient_color2:
	# background gradient
		display.set_bg_gradient_color(background_gradient_color1, background_gradient_color2)

	win.raise_()  # make the application float to the top
	splash.finish(win)
	app.exec_()