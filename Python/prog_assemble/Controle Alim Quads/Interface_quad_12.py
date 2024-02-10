
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 14:13:53 2021

@author: Louise
"""
import datetime
from functools import partial
import numpy as np
import os
import serial
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfile
from tkinter import filedialog
from tkinter.ttk import Label
from threading import Thread, Lock
import time




class Positive_Entry(object):
	"""Class that creates an entry field to send postive voltage to the supply"""
	def __init__(self,port,fenetre,c,r,alimnumber,symmetry, Entry,Vmax):
		#Textbox initialisation
		self.text=tk.StringVar()
		self.text.set("0")
		self.textbox=ttk.Entry(fenetre, textvariable=self.text)
		if alimnumber==1:
			self.textbox.bind('<Return>',self.Return_pressed1)
		elif alimnumber==3:
			self.textbox.bind('<Return>',self.Return_pressed3)
		self.textbox.state(['disabled'])
		
		
		#Slider initialisation
		self.slid_var=tk.DoubleVar()
		self.Vmax=Vmax
		if alimnumber==1:
			self.slider=ttk.Scale(fenetre,from_=0, to=self.Vmax,variable=self.slid_var, command=self.Slider1_changed)
		elif alimnumber==3:
			self.slider=ttk.Scale(fenetre,from_=0, to=self.Vmax,variable=self.slid_var, command=self.Slider3_changed)
		self.slider.state(['disabled'])
		
		self.Min_bound=tk.StringVar()
		self.Min_bound.set("0")
		self.Left_bound=tk.Entry(fenetre,textvariable=self.Min_bound, width=4, bd=0, state='disabled')
		
		self.Max_bound=tk.StringVar()
		self.Max_bound.set("Vmax")
		self.Right_bound=tk.Entry(fenetre,textvariable=self.Max_bound, width=6, bd=0, state='disabled')
		
		self.Reduce_interval_var=tk.StringVar()
		self.Reduce_interval_check=ttk.Checkbutton(fenetre, text='Interval', command=self.Reduce_interval_cmd, variable=self.Reduce_interval_var, onvalue='On', offvalue='Off')
		self.Reduce_interval_var.set('Off')
		
		self.Interval_var=tk.StringVar()
		self.Interval_var.set(self.Vmax)
		self.Interval_entry=ttk.Entry(fenetre, textvariable=self.Interval_var,width=6)
		
		self.Position(fenetre,c,r)
		
		#Communication port initialisation
		self.port=port
		self.symmetry=symmetry
		self.Entry=Entry


	def Position(self,fenetre,c,r):
		#Textbox postition
		self.textbox.grid(column=c, row=r)
		self.label=Label(fenetre,text='U+',font=('bold'))
		self.label.grid(column=c,row=r, sticky=tk.W, padx=80)
		self.Reduce_interval_check.grid(column=c,row=r, sticky='ne')
		self.Interval_entry.grid(column=c,row=r, sticky='e')
		
		#Slider position
		self.slider.grid(column=c, row=r+1, sticky='we', padx=60)
		self.Left_bound.grid(column=c, row=r+1, sticky='sw', padx=60)
		self.Right_bound.grid(column=c, row=r+1, sticky='se', padx=60)

	def Return_pressed1(self,event):
		self.Voltage=self.text.get()
		if float(self.Voltage)>=0.0 and float(self.Voltage)<=self.Vmax:
			if self.symmetry==0:
				self.slid_var.set(float(self.Voltage))
				self.port.write(b'>1,1,%f,0\r'%float(self.Voltage))
				print('ça marche')
				print(float(self.Voltage))
				print(self.port)
				ligne=self.port.readline()
				if ligne!=b'>1,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
			if self.symmetry==1:
				if self.Reduce_interval_var.get()=='Off':
					self.slid_var.set(float(self.Voltage))
					self.port.write(b'>1,1,%f,0\r'%float(self.Voltage))
					ligne=self.port.readline()
					if ligne!=b'>1,1,1\r':
						tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
					self.Entry.slid_var.set(-float(self.Voltage))
					self.Entry.text.set(-float(self.Voltage))
					self.port.write(b'>2,1,-%f,0\r'%float(self.Voltage))
					ligne=self.port.readline()
					if ligne!=b'>2,1,1\r':
						tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V2')
				elif self.Reduce_interval_var.get()=='On':
					Offset=int(self.Min_bound.get())
					self.Voltage=int(self.Voltage)*(int(self.Interval_var.get())/self.Vmax)+Offset
					self.text.set(int(self.Voltage))
					self.port.write(b'>1,1,%i,0\r'%int(self.Voltage))
					ligne=self.port.read(size=9)
					if ligne!=b'>1,1,1\r':
						tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
					self.Entry.text.set(-int(self.Voltage))
					self.Entry.slid_var.set(-self.Voltage)
					self.port.write(b'>2,1,-%i,0\r'%int(self.Voltage))
					ligne=self.port.read(size=9)
					if ligne!=b'>2,1,1\r':
						tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V2')
					
		else :
			tk.messagebox.showinfo(title='Invalid value', message='Please enter a positive value smaller than Vmax')

	def Return_pressed3(self,event):
		self.Voltage=self.text.get()
		if float(self.Voltage)>=0.0 and float(self.Voltage)<=self.Vmax:
			if self.symmetry==0:
				self.slid_var.set(float(self.Voltage))
				self.port.write(b'>3,1,%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>3,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V3')
			if self.symmetry==1:
				self.slid_var.set(float(self.Voltage))
				self.port.write(b'>3,1,%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>3,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V3')
				self.Entry.slid_var.set(-float(self.Voltage))
				self.Entry.text.set(-float(self.Voltage))
				self.port.write(b'>4,1,-%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>4,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V4')
		else :
			tk.messagebox.showinfo(title='Invalid value', message='Please enter a positive value smaller than Vmax')

	def Slider1_changed(self, event):
		self.Voltage=int(self.slid_var.get())
		if self.symmetry==0:
			if self.Reduce_interval_var.get()=='Off':
				self.text.set(self.Voltage)
				self.port.write(b'>1,1,%i,0\r'%int(self.Voltage))
				ligne=self.port.read(size=9) # a la fin n'oublie de choisir une fctread pour tout le prog
				if ligne!=b'>1,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
			elif self.Reduce_interval_var.get()=='On':
				Offset=int(self.Min_bound.get())
				self.Voltage=self.Voltage*(int(self.Interval_var.get())/self.Vmax)+Offset
				self.text.set(int(self.Voltage))
				self.port.write(b'>1,1,%i,0\r'%int(self.Voltage))
				ligne=self.port.read(size=9) # a la fin n'oublie de choisir une fctread pour tout le prog
				if ligne!=b'>1,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
				
		elif self.symmetry==1:
			if self.Reduce_interval_var.get()=='Off':
				self.text.set(self.Voltage)
				self.port.write(b'>1,1,%i,0\r'%int(self.Voltage))
				ligne=self.port.read(size=9)
				if ligne!=b'>1,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
				self.Entry.text.set(-int(self.Voltage))
				self.Entry.slid_var.set(-int(self.Voltage))
				self.port.write(b'>2,1,-%i,0\r'%int(self.Voltage))
				ligne=self.port.read(size=9)
				if ligne!=b'>2,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V2')
			elif self.Reduce_interval_var.get()=='On':
				Offset=int(self.Min_bound.get())
				self.Voltage=self.Voltage*(int(self.Interval_var.get())/self.Vmax)+Offset
				self.text.set(int(self.Voltage))
				self.port.write(b'>1,1,%i,0\r'%int(self.Voltage))
				ligne=self.port.read(size=9)
				if ligne!=b'>1,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V1')
				self.Entry.text.set(-int(self.Voltage))
				self.Entry.slid_var.set(-self.Voltage)
				self.port.write(b'>2,1,-%i,0\r'%int(self.Voltage))
				ligne=self.port.read(size=9)
				if ligne!=b'>2,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V2')
	
	def Slider3_changed(self, event):
		if self.symmetry==0:
			self.Voltage=int(self.slid_var.get())
			self.text.set(self.Voltage)
			self.port.write(b'>3,1,%i,0\r'%int(self.Voltage))
			ligne=self.port.read(size=9)
			if ligne!=b'>3,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V3')
		elif self.symmetry==1:
			self.Voltage=int(self.slid_var.get())
			self.text.set(self.Voltage)
			self.port.write(b'>3,1,%i,0\r'%int(self.Voltage))
			ligne=self.port.read(size=9)
			if ligne!=b'>3,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V3')
			self.Entry.text.set(-self.Voltage)
			self.Entry.slid_var.set(-self.Voltage)
			self.port.write(b'>4,1,-%i,0\r'%int(self.Voltage))
			ligne=self.port.read(size=9)
			if ligne!=b'>4,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V4')
				
	def Reduce_interval_cmd(self):
		if self.Reduce_interval_var.get()=='Off':
			self.Min_bound.set(0)
			self.Max_bound.set(self.Vmax)
			self.slid_var.set(self.text.get())
		if self.Reduce_interval_var.get()=='On':
			Int=np.abs(int(self.Interval_var.get()))
			current_value=int(self.slid_var.get())
			Min_bound=int(current_value-Int/2)
			Max_bound=int(current_value+Int/2)
			if Min_bound>=0 and Max_bound<=self.Vmax:
				self.Min_bound.set(Min_bound)
				self.Max_bound.set(Max_bound)
				self.slid_var.set(self.Vmax/2)
			else:
				tk.messagebox.showinfo(title='Error', message='Invalid interval value : please choose a smaller interval')

class Negative_Entry(object):
	"""Class that creates an entry field to send postive voltage to the supply"""
	def __init__(self,port,fenetre,c,r,alimnumber,Vmax):
		#Initialisation de la textbox
		self.text=tk.StringVar()
		self.text.set("0")
		self.textbox=ttk.Entry(fenetre, textvariable=self.text)
		if alimnumber==2:
			self.textbox.bind('<Return>',self.Return_pressed2)
		elif alimnumber==4:
			self.textbox.bind('<Return>',self.Return_pressed4)
		self.textbox.state(['disabled'])
		
		#Slider initialisation
		self.slid_var=tk.DoubleVar()
		self.Vmax=Vmax
		if alimnumber==2:
			self.slider=ttk.Scale(fenetre,from_=0, to=-self.Vmax,variable=self.slid_var, command=self.Slider2_changed)
		elif alimnumber==4:
			self.slider=ttk.Scale(fenetre,from_=0, to=-self.Vmax,variable=self.slid_var, command=self.Slider4_changed)
		self.slider.state(['disabled'])
		
		self.Min_bound=tk.StringVar()
		self.Min_bound.set("0")
		self.Left_bound=tk.Entry(fenetre,textvariable=self.Min_bound, width=4, bd=0, state='disabled')
		
		self.Max_bound=tk.StringVar()
		self.Max_bound.set("-Vmax")
		self.Right_bound=tk.Entry(fenetre,textvariable=self.Max_bound, width=6, bd=0, state='disabled')
		
		self.Reduce_interval_var=tk.StringVar()
		self.Reduce_interval_check=ttk.Checkbutton(fenetre, text='Interval', command=self.Reduce_interval_cmd, variable=self.Reduce_interval_var, onvalue='On', offvalue='Off')
		self.Reduce_interval_var.set('Off')
		
		self.Interval_var=tk.StringVar()
		self.Interval_var.set(self.Vmax)
		self.Interval_entry=ttk.Entry(fenetre, textvariable=self.Interval_var,width=6)
		
		self.Position(fenetre,c,r)
		#Communication port initialisation
		self.port=port

	def Position(self,fenetre,c,r):
		#Textbox position
		self.textbox.grid(column=c, row=r)
		self.label=Label(fenetre,text='U-',font=('bold'))
		self.label.grid(column=c,row=r, sticky=tk.W, padx=80)
		self.Reduce_interval_check.grid(column=c,row=r, sticky='ne')
		self.Interval_entry.grid(column=c,row=r, sticky='e')
		#Slider position
		self.slider.grid(column=c, row=r+1, sticky='we', padx=60)
		self.Left_bound.grid(column=c, row=r+1, sticky='sw', padx=60)
		self.Right_bound.grid(column=c, row=r+1, sticky='se', padx=60)

	def Return_pressed2(self,event):
		self.Voltage=float(self.text.get())
		if np.abs(self.Voltage)<=self.Vmax:
			if self.Voltage<=0.0:
				self.slid_var.set(self.Voltage)
				self.port.write(b'>2,1,%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>2,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V2')
			else:
				self.Voltage= -self.Voltage
				self.text.set(self.Voltage)
				self.slid_var.set(self.Voltage)
				self.port.write(b'>2,1,%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>2,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V2')
		else :
			tk.messagebox.showinfo(title='Invalid value', message='Please enter a value smaller than Vmax')

	def Return_pressed4(self,event):
		self.Voltage=float(self.text.get())
		if np.abs(self.Voltage)<=self.Vmax:
			if self.Voltage<=0.0:
				self.slid_var.set(self.Voltage)
				self.port.write(b'>4,1,%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>4,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V4')
			else:
				self.Voltage= -self.Voltage
				self.text.set(self.Voltage)
				self.slid_var.set(self.Voltage)
				self.port.write(b'>4,1,%f,0\r'%float(self.Voltage))
				ligne=self.port.readline()
				if ligne!=b'>4,1,1\r':
					tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage on V4')
		else :
			tk.messagebox.showinfo(title='Invalid value', message='Please enter a value smaller than Vmax')
			
	def Slider2_changed(self, event):
		self.Voltage=int(self.slid_var.get())
		if self.Reduce_interval_var.get()=='Off':
			self.text.set(self.Voltage)
			self.port.write(b'>2,1,%i,0\r'%int(self.Voltage))
			ligne=self.port.readline()
			if ligne!=b'>2,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage')
		elif self.Reduce_interval_var.get()=='On':
			Offset=int(self.Min_bound.get())
			self.Voltage=self.Voltage*(int(self.Interval_var.get())/self.Vmax)+Offset
			self.text.set(int(self.Voltage))
			self.port.write(b'>2,1,%i,0\r'%int(self.Voltage))
			ligne=self.port.readline()
			if ligne!=b'>2,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage')

	def Slider4_changed(self, event):
		self.Voltage=int(self.slid_var.get())
		if self.Reduce_interval_var.get()=='Off':
			self.text.set(self.Voltage)
			self.port.write(b'>4,1,%i,0\r'%int(self.Voltage))
			ligne=self.port.readline()
			if ligne!=b'>4,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage')
		elif self.Reduce_interval_var.get()=='On':
			Offset=int(self.Min_bound.get())
			self.Voltage=self.Voltage*(int(self.Interval_var.get())/self.Vmax)+Offset
			self.text.set(int(self.Voltage))
			self.port.write(b'>4,1,%i,0\r'%int(self.Voltage))
			ligne=self.port.readline()
			if ligne!=b'>4,1,1\r':
				tk.messagebox.showinfo(title='Error', message='Couldn\'t set voltage')

	def Reduce_interval_cmd(self):
		if self.Reduce_interval_var.get()=='Off':
			self.Min_bound.set(0)
			self.Max_bound.set(-self.Vmax)
			self.slid_var.set(self.text.get())
		if self.Reduce_interval_var.get()=='On':
			Int=np.abs(int(self.Interval_var.get()))
			current_value=int(self.slid_var.get())
			Min_bound=int(current_value+Int/2)
			Max_bound=int(current_value-Int/2)
			if Min_bound<=0 and Max_bound>=-self.Vmax:
				self.Min_bound.set(Min_bound)
				self.Max_bound.set(Max_bound)
				self.slid_var.set(-self.Vmax/2)
			else:
				tk.messagebox.showinfo(title='Error', message='Invalid interval value : please choose a smaller interval')


#Class that creates main window
class Window (object):
	
	def __init__(self):
		"""Main window definition"""
		#_____________________Main window configuration___________________________________
		self.root=tk.Tk()
		self.root.title('Control of the high voltage supply of the quadrupoles')
		
		
		#Here the window is placed in the center of user screen, is made expandable and in the foreground
		self.screen_width=self.root.winfo_screenwidth()
		self.screen_height=self.root.winfo_screenheight()
		self.window_width=self.screen_width-100
		self.window_height=self.screen_height-100
		self.x=int(self.screen_width/2-self.window_width/2)
		self.y=int(self.screen_height/2-self.window_height/2)
		self.root.geometry(f'{self.window_width}x{self.window_height}+{self.x}+{self.y}')
		self.root.resizable(True,True)
		self.root.attributes('-topmost',1)
		# Notebook allows to create tabs (=frames)
		self.notebook=tk.ttk.Notebook(self.root, width=self.window_width, height=self.window_height)
		self.frame1=tk.Frame(self.notebook)
		self.frame2=tk.Frame(self.notebook)
		self.frame3=tk.Frame(self.notebook)
		#self.root.iconbitmap('./Un-éclair.ico')
		self.frame1.columnconfigure(0, weight=1)
		self.frame1.columnconfigure(1,weight=1)
		self.frame1.columnconfigure(2,weight=1)
		self.frame1.rowconfigure(0,weight=1)
		self.frame1.rowconfigure(1,weight=1)
		self.frame1.rowconfigure(2,weight=1)
		self.frame1.rowconfigure(3,weight=1)
		self.frame1.rowconfigure(4,weight=1)
		self.frame1.rowconfigure(5,weight=1)
		self.frame1.rowconfigure(6,weight=1)
		self.frame1.rowconfigure(7,weight=1)
		self.frame1.rowconfigure(8,weight=1)
		self.frame1.rowconfigure(9,weight=1)
		self.frame1.rowconfigure(10,weight=1)
		self.frame1.rowconfigure(11,weight=1)
		
		self.frame2.columnconfigure(0, weight=2)
		self.frame2.columnconfigure(1,weight=2)
		self.frame2.columnconfigure(2,weight=1)
		self.frame2.columnconfigure(3,weight=2)
		self.frame2.rowconfigure(0,weight=1)
		self.frame2.rowconfigure(1,weight=1)
		self.frame2.rowconfigure(2,weight=1)
		self.frame2.rowconfigure(3,weight=1)
		self.frame2.rowconfigure(4,weight=1)
		self.frame2.rowconfigure(5,weight=1)
		self.frame2.rowconfigure(6,weight=1)
		self.frame2.rowconfigure(7,weight=1)
		self.frame2.rowconfigure(8,weight=1)
		self.frame2.rowconfigure(9,weight=1)
		self.frame2.rowconfigure(10,weight=1)
		self.frame2.rowconfigure(11,weight=1)
		
		
		self.frame3.columnconfigure(0, weight=1)
		self.frame3.columnconfigure(1,weight=1)
		self.frame3.columnconfigure(2,weight=1)
		self.frame3.columnconfigure(3,weight=1)
		self.frame3.columnconfigure(4,weight=1)
		self.frame3.columnconfigure(5,weight=2)
		self.frame3.rowconfigure(0,weight=1)
		self.frame3.rowconfigure(1,weight=1)
		self.frame3.rowconfigure(2,weight=1)
		self.frame3.rowconfigure(3,weight=1)
		self.frame3.rowconfigure(4,weight=1)
		self.frame3.rowconfigure(5,weight=1)
		self.frame3.rowconfigure(6,weight=1)
		self.frame3.rowconfigure(7,weight=1)
		self.frame3.rowconfigure(8,weight=1)
		self.frame3.rowconfigure(9,weight=1)

		
		
		#_____________________________________FRAME 1____________________________________
		#2 comboboxes allow selection of ports connected to computer's USB ports 
		self.labelport1=Label(self.frame1, text='Port on which the first quad is connected :')
		self.labelport1.grid(column=1,row=2,sticky='w', padx=80)
		self.labelport2=Label(self.frame1, text='Port on which the second quad is connected :')
		self.labelport2.grid(column=1,row=4,sticky='w', padx=80)
		
		
		self.Port1_var=tk.StringVar()
		self.Ports=('None','COM1','COM2','COM3','COM4','COM5','COM6')
		self.combo_port1=ttk.Combobox(self.frame1, textvariable=self.Port1_var)
		self.combo_port1['values']=self.Ports
		self.combo_port1['state']='readonly'
		self.combo_port1.bind('<<ComboboxSelected>>', self.Port1_changed)
		self.combo_port1.set('None')
		self.combo_port1.grid(column=1, row=3)
		self.combo_port1.state(['disabled'])
		
		self.Port2_var=tk.StringVar()
		self.combo_port2=ttk.Combobox(self.frame1, textvariable=self.Port2_var)
		self.combo_port2['values']=self.Ports
		self.combo_port2['state']='readonly'
		self.combo_port2.bind('<<ComboboxSelected>>', self.Port2_changed)
		self.combo_port2.set('None')
		self.combo_port2.grid(column=1, row=5)
		self.combo_port2.state(['disabled'])
		
		#Communication is initialised with false value
		self.Comcheck1=False
		self.Comcheck2=False
		#création du bouton de sortie
		self.exit_button1=ttk.Button(self.frame1,text='Exit',command=self.confirm)
		self.exit_button1.grid(column=2, row=11, sticky='e',padx=80)
		self.exit_button2=ttk.Button(self.frame2,text='Exit',command=self.confirm)
		self.exit_button2.grid(column=3, row=11, sticky='e',padx=80)
		self.exit_button3=ttk.Button(self.frame3,text='Exit',command=self.confirm)
		self.exit_button3.grid(column=5, row=20, sticky='e',padx=80)
		
		#Creation of communication button
		self.Com1='None'
		self.Com2='None'
		self.labelcom1=Label(self.frame1, text='Connection on the first port')
		self.labelcom1.grid(column=1, row=6, sticky='w', padx=80)
		self.Com1_button=tk.Button(self.frame1, text='Try connection :', command=self.Connect1)
		self.Com1_button.grid(column=1,row=7, sticky='w')
		
		self.labelcom2=Label(self.frame1, text='Connection on the second port')
		self.labelcom2.grid(column=1, row=8, sticky='w', padx=80)
		self.Com2_button=tk.Button(self.frame1, text='Try connection :', command=self.Connect2)
		self.Com2_button.grid(column=1,row=9, sticky='w')
		
		self.text_Voltage_Max=tk.StringVar()
		self.Voltage_Max=ttk.Entry(self.frame1,textvariable=self.text_Voltage_Max)
		self.text_Voltage_Max.set('100')
		self.Voltage_Max.grid(column=2,row=3, sticky='w')
		self.label_Voltage_Max=Label(self.frame1,text='Maximum Voltage (V)')
		self.label_Voltage_Max.grid(column=2,row=2, sticky='w')
		self.Voltage_Max.bind('<Return>',self.Return_pressed_Voltage)
		
		self.Save_Button=ttk.Button(self.frame1,text='Save connection parameters',command=self.Save_File)
		self.Save_Button.grid(column=2,row=7, sticky='w')
		
		self.Load_Previous_Connection=ttk.Button(self.frame1, text='Load previous connection parameters from', command=self.Load_Connection_Parameters)
		self.Load_Previous_Connection.grid(column=2,row=8, sticky='w')
		
		#___________________________________FRAME 2_______________________________________
		
		self.label_quad1=Label(self.frame2, text='Quadrupole 1 :', font=("Times",14), foreground='blue')
		self.label_quad1.grid(column=0,row=0,sticky=tk.W,padx=40)
		self.label_quad2=Label(self.frame2, text='Quadrupole 2 :', font=("Times",14), foreground='blue')
		self.label_quad2.grid(column=0,row=3,sticky=tk.W,padx=40)
		self.label_quad3=Label(self.frame2, text='Quadrupole 3 :', font=("Times",14), foreground='blue')
		self.label_quad3.grid(column=0,row=6,sticky=tk.W,padx=40)
		self.label_quad4=Label(self.frame2, text='Quadrupole 4 :', font=("Times",14), foreground='blue')
		self.label_quad4.grid(column=0,row=9,sticky=tk.W,padx=40)
		#Entry button creation
		self.port1=None
		self.port2=None
		self.symmetry=0
		# Vmax = maximal voltage delivered default value = 100 V
		self.Vmax=100
		self.Entry5=Negative_Entry(self.port1,self.frame2,1,1,2,self.Vmax)
		self.Entry6=Negative_Entry(self.port1,self.frame2,1,4,4,self.Vmax)
		self.Entry7=Negative_Entry(self.port2,self.frame2,1,7,2,self.Vmax)
		self.Entry8=Negative_Entry(self.port2,self.frame2,1,10,4,self.Vmax)
		self.Entry1=Positive_Entry(self.port1,self.frame2,0,1,1,self.symmetry,self.Entry5,self.Vmax)
		self.Entry2=Positive_Entry(self.port1,self.frame2,0,4,3,self.symmetry,self.Entry6,self.Vmax)
		self.Entry3=Positive_Entry(self.port2,self.frame2,0,7,1,self.symmetry, self.Entry7,self.Vmax)
		self.Entry4=Positive_Entry(self.port2,self.frame2,0,10,3,self.symmetry, self.Entry8,self.Vmax)

		self.check1=tk.StringVar()
		self.Checkbutton1=ttk.Checkbutton(self.frame2,text='Symmetrical power supply',command=self.symmetrical1_changed,variable=self.check1,onvalue='Symmetrical',offvalue='Asymmetrical')
		self.Checkbutton1.grid(column=1,row=0,sticky=tk.W)
		self.check1.set('Asymmetrical')
		
		self.check2=tk.StringVar()
		self.Checkbutton2=ttk.Checkbutton(self.frame2,text='Symmetrical power supply',command=self.symmetrical2_changed,variable=self.check2,onvalue='Symmetrical',offvalue='Asymmetrical')
		self.Checkbutton2.grid(column=1,row=3,sticky=tk.W)
		self.check2.set('Asymmetrical')
		
		self.check3=tk.StringVar()
		self.Checkbutton3=ttk.Checkbutton(self.frame2,text='Symmetrical power supply',command=self.symmetrical3_changed,variable=self.check3,onvalue='Symmetrical',offvalue='Asymmetrical')
		self.Checkbutton3.grid(column=1,row=6,sticky=tk.W)
		self.check3.set('Asymmetrical')
		
		self.check4=tk.StringVar()
		self.Checkbutton4=ttk.Checkbutton(self.frame2,text='Symmetrical power supply',command=self.symmetrical4_changed,variable=self.check4,onvalue='Symmetrical',offvalue='Asymmetrical')
		self.Checkbutton4.grid(column=1,row=9,sticky=tk.W)
		self.check4.set('Asymmetrical')
		
		self.Button_Wobbler_ON_1=ttk.Button(self.frame2,text='ON',command=partial(self.Wobbler_ON,1))
		self.Button_Wobbler_ON_1.grid(column=3, row=0, sticky='e',padx=20)
		self.Button_Wobbler_OFF_1=ttk.Button(self.frame2,text='OFF',command=partial(self.Wobbler_OFF,1))
		self.Button_Wobbler_OFF_1.grid(column=3, row=1, sticky='e',padx=20)
		self.Button_Wobbler_ON_1.state(['disabled'])
		self.Button_Wobbler_OFF_1.state(['disabled'])
		self.label_Wobbler_1=Label(self.frame2, text='Wobbler 1')
		self.label_Wobbler_1.grid(column=3,row=0, sticky='w')
		self.LED1=tk.Button(self.frame2, text= '      ',background='red')
		self.LED1.grid(column=3,row=1, sticky='nw')

		self.Button_Wobbler_ON_2=ttk.Button(self.frame2,text='ON',command=partial(self.Wobbler_ON,2))
		self.Button_Wobbler_ON_2.grid(column=3, row=3, sticky='e',padx=20)
		self.Button_Wobbler_OFF_2=ttk.Button(self.frame2,text='OFF',command=partial(self.Wobbler_OFF,2))
		self.Button_Wobbler_OFF_2.grid(column=3, row=4, sticky='e',padx=20)
		self.Button_Wobbler_ON_2.state(['disabled'])
		self.Button_Wobbler_OFF_2.state(['disabled'])
		self.label_Wobbler_2=Label(self.frame2, text='Wobbler 2')
		self.label_Wobbler_2.grid(column=3,row=3, sticky='w')
		self.LED2=tk.Button(self.frame2, text= '      ',background='red')
		self.LED2.grid(column=3,row=4, sticky='nw')

		self.Button_Wobbler_ON_3=ttk.Button(self.frame2,text='ON',command=partial(self.Wobbler_ON,3))
		self.Button_Wobbler_ON_3.grid(column=3, row=6, sticky='e',padx=20)
		self.Button_Wobbler_OFF_3=ttk.Button(self.frame2,text='OFF',command=partial(self.Wobbler_OFF,3))
		self.Button_Wobbler_OFF_3.grid(column=3, row=7, sticky='e',padx=20)
		self.Button_Wobbler_ON_3.state(['disabled'])
		self.Button_Wobbler_OFF_3.state(['disabled'])
		self.label_Wobbler_3=Label(self.frame2, text='Wobbler 3')
		self.label_Wobbler_3.grid(column=3,row=6, sticky='w')
		self.LED3=tk.Button(self.frame2, text= '      ',background='red')
		self.LED3.grid(column=3,row=7, sticky='nw')

		self.Button_Wobbler_ON_4=ttk.Button(self.frame2,text='ON',command=partial(self.Wobbler_ON,4))
		self.Button_Wobbler_ON_4.grid(column=3, row=9, sticky='e',padx=20)
		self.Button_Wobbler_OFF_4=ttk.Button(self.frame2,text='OFF',command=partial(self.Wobbler_OFF,4))
		self.Button_Wobbler_OFF_4.grid(column=3, row=10, sticky='e',padx=20)
		self.Button_Wobbler_ON_4.state(['disabled'])
		self.Button_Wobbler_OFF_4.state(['disabled'])
		self.label_Wobbler_4=Label(self.frame2, text='Wobbler 4')
		self.label_Wobbler_4.grid(column=3,row=9, sticky='w')
		self.LED4=tk.Button(self.frame2, text= '      ',background='red')
		self.LED4.grid(column=3,row=10, sticky='nw')

		
		self.text_Amp1=tk.StringVar()
		self.text_Amp1.set("10")
		self.Entry_Amplitude1=ttk.Entry(self.frame2, textvariable=self.text_Amp1, width=6)
		self.Entry_Amplitude1.bind('<Return>',self.Amp_Wobbler_changed_1)
		self.Entry_Amplitude1.grid(column=3,row=0)
		self.Entry_Amplitude1.state(['disabled'])
		self.label_Amplitude1=Label(self.frame2, text='Amplitude [0;2000V]')
		self.label_Amplitude1.grid(column=3,row=0, sticky='n')
		
		self.Freq_var1=tk.StringVar()
		self.Freq=('0.25','0.5','1','2.5','5')
		self.Combo_freq1=ttk.Combobox(self.frame2, textvariable=self.Freq_var1, width=6)
		self.Combo_freq1['values']=self.Freq
		self.Combo_freq1['state']='readonly'
		self.Combo_freq1.bind('<<ComboboxSelected>>', self.Combo_freq_changed1)
		self.Combo_freq1.set('1')
		self.Combo_freq1.state(['disabled'])
		self.Combo_freq1.grid(column=3, row=1, sticky='s')
		self.label_Frequency1=Label(self.frame2, text='Frequency [0.25;5 Hz]')
		self.label_Frequency1.grid(column=3,row=1)
		
		self.text_Amp2=tk.StringVar()
		self.text_Amp2.set("10")
		self.Entry_Amplitude2=ttk.Entry(self.frame2, textvariable=self.text_Amp2, width=6)
		self.Entry_Amplitude2.bind('<Return>',self.Amp_Wobbler_changed_2)
		self.Entry_Amplitude2.grid(column=3,row=3)
		self.Entry_Amplitude2.state(['disabled'])
		self.label_Amplitude2=Label(self.frame2, text='Amplitude [0;2000V]')
		self.label_Amplitude2.grid(column=3,row=3, sticky='n')
		
		self.Freq_var2=tk.StringVar()
		self.Combo_freq2=ttk.Combobox(self.frame2, textvariable=self.Freq_var2, width=6)
		self.Combo_freq2['values']=self.Freq
		self.Combo_freq2['state']='readonly'
		self.Combo_freq2.bind('<<ComboboxSelected>>', self.Combo_freq_changed2)
		self.Combo_freq2.set('1')
		self.Combo_freq2.state(['disabled'])
		self.Combo_freq2.grid(column=3, row=4, sticky='s')
		self.label_Frequency2=Label(self.frame2, text='Frequency [0.25;5 Hz]')
		self.label_Frequency2.grid(column=3,row=4)
		
		self.text_Amp3=tk.StringVar()
		self.text_Amp3.set("10")
		self.Entry_Amplitude3=ttk.Entry(self.frame2, textvariable=self.text_Amp3, width=6)
		self.Entry_Amplitude3.bind('<Return>',self.Amp_Wobbler_changed_3)
		self.Entry_Amplitude3.grid(column=3,row=6)
		self.Entry_Amplitude3.state(['disabled'])
		self.label_Amplitude3=Label(self.frame2, text='Amplitude [0;2000V]')
		self.label_Amplitude3.grid(column=3,row=6, sticky='n')
		
		self.Freq_var3=tk.StringVar()
		self.Combo_freq3=ttk.Combobox(self.frame2, textvariable=self.Freq_var3, width=6)
		self.Combo_freq3['values']=self.Freq
		self.Combo_freq3['state']='readonly'
		self.Combo_freq3.bind('<<ComboboxSelected>>', self.Combo_freq_changed3)
		self.Combo_freq3.set('1')
		self.Combo_freq3.state(['disabled'])
		self.Combo_freq3.grid(column=3, row=7, sticky='s')
		self.label_Frequency3=Label(self.frame2, text='Frequency [0.25;5 Hz]')
		self.label_Frequency3.grid(column=3,row=7)
		
		self.text_Amp4=tk.StringVar()
		self.text_Amp4.set("10")
		self.Entry_Amplitude4=ttk.Entry(self.frame2, textvariable=self.text_Amp4, width=6)
		self.Entry_Amplitude4.bind('<Return>',self.Amp_Wobbler_changed_4)
		self.Entry_Amplitude4.grid(column=3,row=9)
		self.Entry_Amplitude4.state(['disabled'])
		self.label_Amplitude4=Label(self.frame2, text='Amplitude [0;2000V]')
		self.label_Amplitude4.grid(column=3,row=9, sticky='n')
		
		self.Freq_var4=tk.StringVar()
		self.Combo_freq4=ttk.Combobox(self.frame2, textvariable=self.Freq_var4, width=6)
		self.Combo_freq4['values']=self.Freq
		self.Combo_freq4['state']='readonly'
		self.Combo_freq4.bind('<<ComboboxSelected>>', self.Combo_freq_changed4)
		self.Combo_freq4.set('1')
		self.Combo_freq4.state(['disabled'])
		self.Combo_freq4.grid(column=3, row=10, sticky='s')
		self.label_Frequency4=Label(self.frame2, text='Frequency [0.25;5 Hz]')
		self.label_Frequency4.grid(column=3,row=10)
		
		
		self.Save_As_Frame2=ttk.Button(self.frame2, text='Save as', command=self.Save_as)
		self.Save_As_Frame2.grid(column=2, row=1, sticky='nw')
		
		self.Load_Frame2=ttk.Button(self.frame2, text='Load from previous file', command=self.Load_Voltage_Parameters)
		self.Load_Frame2.grid(column=2, row=1, sticky='ne')
		
		#__________________ FRAME 3 _________________________________________
		
		self.label_x_Frame3=Label(self.frame3, text='Focus/defocus along x axis')
		self.label_x_Frame3.grid(column=0,row=0)
		self.label_Quad1_Frame3=Label(self.frame3, text='Quad 1')
		self.label_Quad1_Frame3.grid(column=0,row=1)
		self.label_Quad2_Frame3=Label(self.frame3, text='Quad 2')
		self.label_Quad2_Frame3.grid(column=0,row=2)
		self.label_Quad3_Frame3=Label(self.frame3, text='Quad 3')
		self.label_Quad3_Frame3.grid(column=0,row=3)
		self.label_Quad4_Frame3=Label(self.frame3, text='Quad 4')
		self.label_Quad4_Frame3.grid(column=0,row=4)
		
		self.Defocus_Quad1=tk.Button(self.frame3, text= '  D  ',command=partial(self.Defocus,1))
		self.Defocus_Quad1.grid(column=0, row=1,sticky='e')
		self.Focus_Quad1=tk.Button(self.frame3, text= '  F  ',command=partial(self.Focus,1))
		self.Focus_Quad1.grid(column=1, row=1)
		self.Defocus_Quad2=tk.Button(self.frame3, text= '  D  ',command=partial(self.Defocus,2))
		self.Defocus_Quad2.grid(column=0, row=2,sticky='e')
		self.Focus_Quad2=tk.Button(self.frame3, text= '  F  ',command=partial(self.Focus,2))
		self.Focus_Quad2.grid(column=1, row=2)
		self.Defocus_Quad3=tk.Button(self.frame3, text= '  D  ',command=partial(self.Defocus,3))
		self.Defocus_Quad3.grid(column=0, row=3,sticky='e')
		self.Focus_Quad3=tk.Button(self.frame3, text= '  F  ',command=partial(self.Focus,3))
		self.Focus_Quad3.grid(column=1, row=3)
		self.Defocus_Quad4=tk.Button(self.frame3, text= '  D  ',command=partial(self.Defocus,4))
		self.Defocus_Quad4.grid(column=0, row=4,sticky='e')
		self.Focus_Quad4=tk.Button(self.frame3, text= '  F  ',command=partial(self.Focus,4))
		self.Focus_Quad4.grid(column=1, row=4)
		
		self.label_x0_Frame3=Label(self.frame3, text='x0')
		self.label_x0_Frame3.grid(column=0,row=5)
		self.text_x0_Frame3=tk.StringVar()
		self.Entry_x0=ttk.Entry(self.frame3, textvariable=self.text_x0_Frame3, width=6)
		self.Entry_x0.bind('<Return>',partial(self.Parameters,'x0'))
		self.Entry_x0.grid(column=0,row=5, sticky='e')
		self.x0=None
		
		self.label_a0_Frame3=Label(self.frame3, text='a0')
		self.label_a0_Frame3.grid(column=1,row=5)
		self.text_a0_Frame3=tk.StringVar()
		self.Entry_a0=ttk.Entry(self.frame3, textvariable=self.text_a0_Frame3, width=6)
		self.Entry_a0.bind('<Return>',partial(self.Parameters,'a0'))
		self.Entry_a0.grid(column=1,row=5, sticky='e')
		self.a0=None
		
		self.label_WD_Frame3=Label(self.frame3, text='WD')
		self.label_WD_Frame3.grid(column=2,row=5)
		self.text_WD_Frame3=tk.StringVar()
		self.Entry_WD=ttk.Entry(self.frame3, textvariable=self.text_WD_Frame3, width=6)
		self.Entry_WD.bind('<Return>',partial(self.Parameters,'WD'))
		self.Entry_WD.grid(column=2,row=5, sticky='e')
		self.WD=None
		
		self.label_E_Frame3=Label(self.frame3, text='E')
		self.label_E_Frame3.grid(column=3,row=5)
		self.text_E_Frame3=tk.StringVar()
		self.Entry_E=ttk.Entry(self.frame3, textvariable=self.text_E_Frame3, width=6)
		self.Entry_E.bind('<Return>',partial(self.Parameters,'E'))
		self.Entry_E.grid(column=3,row=5, sticky='e')
		self.E=None
		
		self.label_d_Frame3=Label(self.frame3, text='d')
		self.label_d_Frame3.grid(column=0,row=6)
		self.text_d_Frame3=tk.StringVar()
		self.Entry_d=ttk.Entry(self.frame3, textvariable=self.text_d_Frame3, width=6)
		self.Entry_d.bind('<Return>',partial(self.Parameters,'d'))
		self.Entry_d.grid(column=0,row=6,sticky='e')
		self.d=None
		
		self.label_m_Frame3=Label(self.frame3, text='m')
		self.label_m_Frame3.grid(column=0,row=7)
		self.text_m_Frame3=tk.StringVar()
		self.Entry_m=ttk.Entry(self.frame3, textvariable=self.text_m_Frame3, width=6)
		self.Entry_m.bind('<Return>',partial(self.Parameters,'m'))
		self.Entry_m.grid(column=0,row=7,sticky='e')
		self.m=None
		
		self.label_e_Frame3=Label(self.frame3, text='e')
		self.label_e_Frame3.grid(column=0,row=8)
		self.text_e_Frame3=tk.StringVar()
		self.Entry_e=ttk.Entry(self.frame3, textvariable=self.text_e_Frame3, width=6)
		self.Entry_e.bind('<Return>',partial(self.Parameters,'e'))
		self.Entry_e.grid(column=0,row=8,sticky='e')
		self.e=None
		
		self.label_L_Frame3=Label(self.frame3, text='L')
		self.label_L_Frame3.grid(column=0,row=9)
		self.text_L_Frame3=tk.StringVar()
		self.Entry_L=ttk.Entry(self.frame3, textvariable=self.text_L_Frame3, width=6)
		self.Entry_L.bind('<Return>',partial(self.Parameters,'L'))
		self.Entry_L.grid(column=0,row=9,sticky='e')
		self.L=None
		
		#self.canvas=tk.Canvas(self.frame3,width=300, height=800)
		#self.canvas.grid(column=5, row=1, rowspan=18)
		#self.Microscope=tk.PhotoImage(file='Microscope.gif')
		#self.Image_Microscope=ttk.Label(self.frame3, image=self.Microscope)
		#self.Image_Microscope.grid(column=5, row=1, rowspan=9)
		#self.Image_Microscope.width=25
		#self.Microscope.resize((200,400))
		#self.canvas.create_image(200,400,anchor='e', image=self.Microscope)
		
		#Mainloop permettant l'affichage de la fenêtre, pack permet l'affichage dans les onglets
		self.notebook.add(self.frame1,text="Connection settings")
		self.notebook.add(self.frame2,text="Voltage")
		self.notebook.add(self.frame3, text="Trajectory parameters")
		self.notebook.pack()
		
		self.port1_survive=True
		self.port2_survive=True
		self.root.mainloop()
		
	def Save_File(self):
		date=datetime.datetime.now()
		file=open('Connection_Parameters','w')
		file.write('CONNECTION PARAMETERS SAVED : '+date.strftime("%d/%m/%Y %X")+'\n\n')
		file.write('Communication port quad 1 : '+self.Port1_var.get()+'\n')
		file.write('Communication port quad 2 : '+self.Port2_var.get()+'\n\n')
		file.write('Maximum Voltage chosen : '+self.Voltage_Max.get()+'\n')
		file.close()
	
	def Load_Connection_Parameters(self):
		try :
			file=open('Connection_Parameters','r')
			line=file.readline()
			line=file.readline()
			line=file.readline()
			Port1=line.split(': ')[1][:4]
			self.Port1_var.set(Port1)
			self.Port1_changed(self)
			line=file.readline()
			Port2=line.split(": ")[1][:4]
			self.Port2_var.set(Port2)
			self.Port2_changed(self)
			line=file.readline()
			line=file.readline()
			Vmax=line.split(":")[1]
			self.text_Voltage_Max.set(int(Vmax))
			self.Return_pressed_Voltage(self)
			file.close()
		except :
			tk.messagebox.showinfo(title='Error', message='Couldn\'t find Connection_Parameters file')
		

# 	def Combo_freq_changed(self,event,number):
# 		if number==1:
# 			self.Wobbler_ON(1)
# 		elif number==2:
# 			self.Wobbler_ON(2)
# 		elif number==3:
# 			self.Wobbler_ON(3)
# 		elif number==4:
# 			self.Wobbler_ON(4)

	def Combo_freq_changed1(self,event):
		self.Wobbler_ON(1)
	
	def Combo_freq_changed2(self,event):
		self.Wobbler_ON(2)
	
	def Combo_freq_changed3(self,event):
		self.Wobbler_ON(3)
	
	def Combo_freq_changed4(self,event):
		self.Wobbler_ON_4(4)

	def Return_pressed_Voltage(self,event):
		self.Vmax_entered=int(self.text_Voltage_Max.get())
		self.Register_Value1=int(self.Entry1.slid_var.get())
		self.Register_Value2=self.Entry2.slid_var.get()
		self.Register_Value3=self.Entry3.slid_var.get()
		self.Register_Value4=self.Entry4.slid_var.get()
		self.Register_Value5=self.Entry5.slid_var.get()
		self.Register_Value6=self.Entry6.slid_var.get()
		self.Register_Value7=self.Entry7.slid_var.get()
		self.Register_Value8=self.Entry8.slid_var.get()
		
		self.Entry5=Negative_Entry(self.port1,self.frame2,1,1,2,self.Vmax_entered)
		self.Entry5.slid_var.set(self.Register_Value5)
		self.Entry5.text.set(self.Register_Value5)
		self.Entry6=Negative_Entry(self.port1,self.frame2,1,4,4,self.Vmax_entered)
		self.Entry6.slid_var.set(self.Register_Value6)
		self.Entry6.text.set(self.Register_Value6)
		self.Entry7=Negative_Entry(self.port2,self.frame2,1,7,2,self.Vmax_entered)
		self.Entry7.slid_var.set(self.Register_Value7)
		self.Entry7.text.set(self.Register_Value7)
		self.Entry8=Negative_Entry(self.port2,self.frame2,1,10,4,self.Vmax_entered)
		self.Entry8.slid_var.set(self.Register_Value8)
		self.Entry8.text.set(self.Register_Value8)
		self.Entry1=Positive_Entry(self.port1,self.frame2,0,1,1,self.symmetry,self.Entry5,self.Vmax_entered)
		self.Entry1.slid_var.set(self.Register_Value1)
		self.Entry1.text.set(f'{self.Register_Value1}')
		self.Entry2=Positive_Entry(self.port1,self.frame2,0,4,3,self.symmetry,self.Entry6,self.Vmax_entered)
		self.Entry2.slid_var.set(self.Register_Value2)
		self.Entry2.text.set(self.Register_Value2)
		self.Entry3=Positive_Entry(self.port2,self.frame2,0,7,1,self.symmetry, self.Entry7,self.Vmax_entered)
		self.Entry3.slid_var.set(self.Register_Value3)
		self.Entry3.text.set(self.Register_Value3)
		self.Entry4=Positive_Entry(self.port2,self.frame2,0,10,3,self.symmetry, self.Entry8,self.Vmax_entered)
		self.Entry4.slid_var.set(self.Register_Value4)
		self.Entry4.text.set(self.Register_Value4)
		
		self.Entry1.Max_bound.set(self.Vmax_entered)
		self.Entry2.Max_bound.set(self.Vmax_entered)
		self.Entry3.Max_bound.set(self.Vmax_entered)
		self.Entry4.Max_bound.set(self.Vmax_entered)
		self.Entry5.Max_bound.set(-self.Vmax_entered)
		self.Entry6.Max_bound.set(-self.Vmax_entered)
		self.Entry7.Max_bound.set(-self.Vmax_entered)
		self.Entry8.Max_bound.set(-self.Vmax_entered)
		
		self.combo_port1.state(['!disabled'])
		self.combo_port2.state(['!disabled'])
		if self.Comcheck1!=False:
			self.Entry1.textbox.state(['!disabled'])
			self.Entry1.text.set("0")
			self.Entry1.slider.state(['!disabled'])
			self.Entry2.textbox.state(['!disabled'])
			self.Entry2.text.set("0")
			self.Entry2.slider.state(['!disabled'])
			self.Entry5.textbox.state(['!disabled'])
			self.Entry5.text.set("0")
			self.Entry5.slider.state(['!disabled'])
			self.Entry6.textbox.state(['!disabled'])
			self.Entry6.text.set("0")
			self.Entry6.slider.state(['!disabled'])
		if self.Comcheck2!=False:
			self.Entry3.textbox.state(['!disabled'])
			self.Entry3.text.set("0")
			self.Entry3.slider.state(['!disabled'])
			self.Entry4.textbox.state(['!disabled'])
			self.Entry4.text.set("0")
			self.Entry4.slider.state(['!disabled'])
			self.Entry7.textbox.state(['!disabled'])
			self.Entry7.text.set("0")
			self.Entry7.slider.state(['!disabled'])
			self.Entry8.textbox.state(['!disabled'])
			self.Entry8.text.set("0")
			self.Entry8.slider.state(['!disabled'])

	def symmetrical1_changed(self):
		if self.check1.get()=='Symmetrical':
			#self.symmetry=1
			self.Entry1.symmetry=1;
			self.Entry5.text.set(f'-{self.Entry1.text.get()}')
			self.Entry5.slid_var.set(-float(self.Entry1.slid_var.get()))
			self.Entry1.Return_pressed1('<Return>')
			self.Entry5.textbox.state(['disabled'])
			self.Entry5.slider.state(['disabled'])
			self.Entry5.Min_bound.set(0)
			self.Entry5.Max_bound.set(-self.Vmax)
			self.Entry5.Reduce_interval_var.set("Off")
			self.Entry5.Interval_var.set(self.Vmax)
			self.Entry5.Reduce_interval_check.state(['disabled'])
			self.Entry5.Interval_entry.state(['disabled'])
		elif self.check1.get()=='Asymmetrical':
			#self.symmetry=0
			self.Entry1.symmetry=0;
			self.Entry5.textbox.state(['!disabled'])
			self.Entry5.slider.state(['!disabled'])
			self.Entry5.Reduce_interval_check.state(['!disabled'])
			self.Entry5.Interval_entry.state(['!disabled'])

	def symmetrical2_changed(self):
		if self.check2.get()=='Symmetrical':
			#self.symmetry=1
			self.Entry2.symmetry=1;
			self.Entry6.text.set(f'-{self.Entry2.text.get()}')
			self.Entry6.slid_var.set(-float(self.Entry2.slid_var.get()))
			self.Entry2.Return_pressed3('<Return>')
			self.Entry6.textbox.state(['disabled'])
			self.Entry6.slider.state(['disabled'])
			self.Entry6.Min_bound.set(0)
			self.Entry6.Max_bound.set(self.Vmax)
			self.Entry6.Reduce_interval_var.set("Off")
			self.Entry6.Interval_var.set(self.Vmax)
			self.Entry6.Reduce_interval_check.state(['disabled'])
			self.Entry6.Interval_entry.state(['disabled'])
		elif self.check2.get()=='Asymmetrical':
			#self.symmetry=0
			self.Entry2.symmetry=0;
			self.Entry6.textbox.state(['!disabled'])
			self.Entry6.slider.state(['!disabled'])
			self.Entry6.Reduce_interval_check.state(['!disabled'])
			self.Entry6.Interval_entry.state(['!disabled'])
			
	def symmetrical3_changed(self):
		if self.check3.get()=='Symmetrical':
			#self.symmetry=1
			self.Entry3.symmetry=1;
			self.Entry7.text.set(f'-{self.Entry1.text.get()}')
			self.Entry7.slid_var.set(-float(self.Entry3.slid_var.get()))
			self.Entry3.Return_pressed1('<Return>')
			self.Entry7.textbox.state(['disabled'])
			self.Entry7.slider.state(['disabled'])
			self.Entry7.Min_bound.set(0)
			self.Entry7.Max_bound.set(self.Vmax)
			self.Entry7.Reduce_interval_var.set("Off")
			self.Entry7.Interval_var.set(self.Vmax)
			self.Entry7.Reduce_interval_check.state(['disabled'])
			self.Entry7.Interval_entry.state(['disabled'])
		elif self.check3.get()=='Asymmetrical':
			#self.symmetry=0
			self.Entry3.symmetry=0;
			self.Entry7.textbox.state(['!disabled'])
			self.Entry7.slider.state(['!disabled'])
			self.Entry7.Reduce_interval_check.state(['!disabled'])
			self.Entry7.Interval_entry.state(['!disabled'])
			
	def symmetrical4_changed(self):
		if self.check4.get()=='Symmetrical':
			#self.symmetry=1
			self.Entry4.symmetry=1;
			self.Entry8.text.set(f'-{self.Entry1.text.get()}')
			self.Entry8.slid_var.set(-float(self.Entry4.slid_var.get()))
			self.Entry4.Return_pressed3('<Return>')
			self.Entry8.textbox.state(['disabled'])
			self.Entry8.slider.state(['disabled'])
			self.Entry8.Min_bound.set(0)
			self.Entry8.Max_bound.set(self.Vmax)
			self.Entry8.Reduce_interval_var.set("Off")
			self.Entry8.Interval_var.set(self.Vmax)
			self.Entry8.Reduce_interval_check.state(['disabled'])
			self.Entry8.Interval_entry.state(['disabled'])
		elif self.check4.get()=='Asymmetrical':
			self.symmetry=0
			self.Entry4.symmetry=0;
			self.Entry8.textbox.state(['!disabled'])
			self.Entry8.slider.state(['!disabled'])
			self.Entry8.Reduce_interval_check.state(['!disabled'])
			self.Entry8.Interval_entry.state(['!disabled'])

	def Port1_changed(self,event):
		self.Com1=self.Port1_var.get()
			
	def Port2_changed(self,event):
		self.Com2=self.Port2_var.get()
	#Définition de la commande liée au bouton de sortie

	def confirm(self):
		#Message demandant la confirmation de quitter à l'utilisateur
		answer=tk.messagebox.askyesno(title='Confirmation', message='Are you sure you want to quit?')
		#Si quitter et communication établie : mise à OFF puis vérification de réussite avant de fermer le port et de détruire la fenêtre IHM
		if answer and self.Comcheck1 and not self.Comcheck2:
			self.WritePortCom(self.port1, self.lock1, b'>1,4,0\r') #CMD_SET_WOBBLER -> OFF
			self.WritePortCom(self.port1, self.lock1, b'>2,4,0\r')
			self.WritePortCom(self.port1, self.lock1, b'>3,4,0\r')
			self.WritePortCom(self.port1, self.lock1, b'>4,4,0\r')
			
			
# 			self.port1.write(b'>1,4,0\r')
# 			self.port1.write(b'>2,4,0\r')
# 			self.port1.write(b'>3,4,0\r')
# 			self.port1.write(b'>4,4,0\r')
# 			self.port1.readline()
			line=self.WritePortCom(self.port1, self.lock1, b'>1,10,0\r')#CMD_SET_HT1_STATUS -> OFF
			print(line)
# 			self.port1.write(b'>1,10,0\r')
# 			ligne=self.port1.readline()
			#print(ligne)
			if line==b'>1,10,0\r':
				self.port1_survive=False
				self.port1.close()
				self.root.destroy()
			else:
				tk.messagebox.showinfo(title='Error', message='Error in gun state quad 1')
		#Si quitter sans avoir réussi la communication, destruction directe de la fenêtre
		elif answer and not self.Comcheck1 and not self.Comcheck2:
			self.root.destroy()
		elif answer and not self.Comcheck1 and self.Comcheck2:
			self.WritePortCom(self.port2, self.lock2, b'>1,4,0\r') #CMD_SET_WOBBLER -> OFF
			self.WritePortCom(self.port2, self.lock2, b'>2,4,0\r')
			self.WritePortCom(self.port2, self.lock2, b'>3,4,0\r')
			self.WritePortCom(self.port2, self.lock2, b'>4,4,0\r')
# 			self.port2.write(b'>1,4,0\r')
# 			self.port2.write(b'>2,4,0\r')
# 			self.port2.write(b'>3,4,0\r')
# 			self.port2.write(b'>4,4,0\r')
# 			self.port2.readline()
			line=self.WritePortCom(self.port2, self.lock2, b'>1,10,0\r')#CMD_SET_HT1_STATUS -> OFF
			print(line)
# 			self.port2.write(b'>1,10,0\r')
# 			ligne=self.port2.readline()
			#print(ligne)
			if line==b'>1,10,0\r':
				self.port2_survive=False
				self.port2.close()
				self.root.destroy()
			else:
				tk.messagebox.showinfo(title='Error', message='Error in gun state quad 2')
		elif answer and self.Comcheck1 and self.Comcheck2:
			self.WritePortCom(self.port1, self.lock1, b'>1,4,0\r') #CMD_SET_WOBBLER -> OFF
			self.WritePortCom(self.port1, self.lock1, b'>2,4,0\r')
			self.WritePortCom(self.port1, self.lock1, b'>3,4,0\r')
			self.WritePortCom(self.port1, self.lock1, b'>4,4,0\r')
# 			self.port1.write(b'>1,4,0\r')
# 			self.port1.write(b'>2,4,0\r')
# 			self.port1.write(b'>3,4,0\r')
# 			self.port1.write(b'>4,4,0\r')
# 			self.port1.readline()
			self.WritePortCom(self.port2, self.lock2, b'>1,4,0\r') #CMD_SET_WOBBLER -> OFF
			self.WritePortCom(self.port2, self.lock2, b'>2,4,0\r')
			self.WritePortCom(self.port2, self.lock2, b'>3,4,0\r')
			self.WritePortCom(self.port2, self.lock2, b'>4,4,0\r')
# 			self.port2.write(b'>1,4,0\r')
# 			self.port2.write(b'>2,4,0\r')
# 			self.port2.write(b'>3,4,0\r')
# 			self.port2.write(b'>4,4,0\r')
# 			self.port2.readline()
# 			self.port1.write(b'>1,10,0\r')
# 			ligne=self.port1.readline()
			line=self.WritePortCom(self.port1, self.lock1, b'>1,10,0\r')
			print(line)
			#print(ligne)
			if line==b'>1,10,0\r':
				self.port1_survive=False
				self.port1.close()
			else:
				tk.messagebox.showinfo(title='Error', message='Error in gun state quad 1')
			line=self.WritePortCom(self.port2, self.lock2, b'>1,10,0\r')
# 			self.port2.write(b'>1,10,0\r')
# 			line=self.port2.readline()
			#print(ligne)
			if line==b'>1,10,0\r':
				self.port2_survive=False
				self.port2.close()
				self.root.destroy()
			else:
				tk.messagebox.showinfo(title='Error', message='Error in gun state quad 2')
	
	#Définition de la commande liée au bouton de connexion
	def Connect1(self):
		#Tentative d'ouverture du port 1
		try:
			self.port1=serial.Serial(port='COM3', baudrate=57600, bytesize=8, timeout=0.05, stopbits=1)
			#print(self.port1)
			self.Comcheck1=True
			self.Entry1.port=self.port1
			self.Entry2.port=self.port1
			self.Entry5.port=self.port1
			self.Entry6.port=self.port1
			#On active la textbox et le slider puisque la communication est réalisée
			self.Entry1.textbox.state(['!disabled'])
			self.Entry1.text.set("0")
			self.Entry1.slider.state(['!disabled'])
			self.Entry2.textbox.state(['!disabled'])
			self.Entry2.text.set("0")
			self.Entry2.slider.state(['!disabled'])
			self.Entry5.textbox.state(['!disabled'])
			self.Entry5.text.set("0")
			self.Entry5.slider.state(['!disabled'])
			self.Entry6.textbox.state(['!disabled'])
			self.Entry6.text.set("0")
			self.Entry6.slider.state(['!disabled'])
			Com1_button=tk.Button(self.frame1, text='OK', background='green', foreground='white')
			Com1_button.grid(column=1,row=7)
			self.Button_Wobbler_ON_1.state(['!disabled'])
			self.Button_Wobbler_OFF_1.state(['!disabled'])
			self.Button_Wobbler_ON_2.state(['!disabled'])
			self.Button_Wobbler_OFF_2.state(['!disabled'])
			self.Combo_freq1.state(['!disabled'])
			self.Combo_freq2.state(['!disabled'])
			self.Entry_Amplitude1.state(['!disabled'])
			self.Entry_Amplitude2.state(['!disabled'])
			#print(self.Entry1.port)
		#Message d'erreur si port non ouvert
		except serial.SerialException:
			tk.messagebox.showinfo(title='Erreur', message="Port com quad 1 non trouvé: Serial Exception")
			self.Comcheck1=False
		#Si communication OK, mise à ON et vérification de réussite
		if self.Comcheck1:
			self.port1.write(b'>1,10,2\r')
			ligne=self.port1.readline()
			if ligne!= b'>1,10,2\r':
				tk.messagebox.showinfo(title='Error in gun state quad 1')
		self.lock1 = Lock()   # Creation d'un Lock object pour éviter que deux thread cherche à modifier une même variable, ce qui amène à une erreur.
		self.t1 = Thread(target=self.Readingloop1, args=(self.port1, self.lock1))  # Appel de la boucle de lecture dans un thread a part
		self.t1.start()


	def Connect2(self):
	#Tentative d'ouverture du port 2
		try:
			self.port2=serial.Serial(port=self.Com2, baudrate=57600, bytesize=8, timeout=0.05, stopbits=1)
			self.Comcheck2=True
			self.Entry3.port=self.port2
			self.Entry4.port=self.port2
			self.Entry7.port=self.port2
			self.Entry8.port=self.port2
			#On active la textbox et le slider puisque la communication est réalisée
			self.Entry3.textbox.state(['!disabled'])
			self.Entry3.text.set("0")
			self.Entry3.slider.state(['!disabled'])
			self.Entry4.textbox.state(['!disabled'])
			self.Entry4.text.set("0")
			self.Entry4.slider.state(['!disabled'])
			self.Entry7.textbox.state(['!disabled'])
			self.Entry7.text.set("0")
			self.Entry7.slider.state(['!disabled'])
			self.Entry8.textbox.state(['!disabled'])
			self.Entry8.text.set("0")
			self.Entry8.slider.state(['!disabled'])
			Com2_button=tk.Button(self.frame1, text='OK', background='green', foreground='white')
			Com2_button.grid(column=1,row=9)
			self.Button_Wobbler_ON_3.state(['!disabled'])
			self.Button_Wobbler_OFF_3.state(['!disabled'])
			self.Button_Wobbler_ON_4.state(['!disabled'])
			self.Button_Wobbler_OFF_4.state(['!disabled'])
			self.Combo_freq3.state(['!disabled'])
			self.Combo_freq4.state(['!disabled'])
			self.Entry_Amplitude3.state(['!disabled'])
			self.Entry_Amplitude4.state(['!disabled'])
			#print(self.Entry1.port)
		#Message d'erreur si port non ouvert
		except serial.SerialException:
			tk.messagebox.showinfo(title='Erreur', message="Port com quad 2 non trouvé: Serial Exception")
			self.Comcheck2=False
		#Si communication OK, mise à ON et vérification de réussite
		if self.Comcheck2:
			self.port2.write(b'>1,10,2\r')
			ligne=self.port2.readline()
			if ligne!= b'>1,10,2\r':
				tk.messagebox.showinfo(title='Error in gun state quad 2')
		self.lock2= Lock()   # Creation d'un Lock object pour éviter que deux thread cherche à modifier une même variable, ce qui amène à une erreur.
		self.t2 = Thread(target=self.Readingloop2, args=(self.port2, self.lock2))  # Appel de la boucle de lecture dans un thread a part
		self.t2.start()
	
	def Calculate_step_number(self,number):
		if number==1:
			Frequency=float(self.Freq_var1.get())
		elif number==2:
			Frequency=float(self.Freq_var2.get())
		elif number==3:
			Frequency=float(self.Freq_var3.get())
		elif number==4:
			Frequency=float(self.Freq_var4.get())
		Step_nb=int(1/(Frequency*4*0.05))
		return Step_nb

	def Amp_Wobbler_changed_1(self,event):
		self.Wobbler_ON(1)
		
	def Amp_Wobbler_changed_2(self,event):
		self.Wobbler_ON(2)
		
	def Amp_Wobbler_changed_3(self,event):
		self.Wobbler_ON(3)
		
	def Amp_Wobbler_changed_4(self,event):
		self.Wobbler_ON(4)

	def Wobbler_ON(self, number):
		if number==1:
			self.LED1.configure(bg='green')
			self.port1.write(b'>1,4,1,15,%i,%i\r'%(int(self.text_Amp1.get()),self.Calculate_step_number(1)))
			self.port1.write(b'>2,4,1,15,%i,%i\r'%(int(self.text_Amp1.get()),self.Calculate_step_number(1)))
			self.port1.readline()
		elif number==2:
			self.LED2.configure(bg='green')
			self.port1.write(b'>3,4,1,15,%i,%i\r'%(int(self.text_Amp2.get()),self.Calculate_step_number(2)))
			self.port1.write(b'>4,4,1,15,%i,%i\r'%(int(self.text_Amp2.get()),self.Calculate_step_number(2)))
			self.port1.readline()
		elif number==3:
			self.LED3.configure(bg='green')
			self.port2.write(b'>1,4,1,15,%i,%i\r'%(int(self.text_Amp3.get()),self.Calculate_step_number(3)))
			self.port2.write(b'>2,4,1,15,%i,%i\r'%(int(self.text_Amp3.get()),self.Calculate_step_number(3)))
			self.port2.readline()
		elif number==4:
			self.LED4.configure(bg='green')
			self.port2.write(b'>3,4,1,15,%i,%i\r'%(int(self.text_Amp4.get()),self.Calculate_step_number(4)))
			self.port2.write(b'>4,4,1,15,%i,%i\r'%(int(self.text_Amp4.get()),self.Calculate_step_number(4)))
			self.port2.readline()

	def Wobbler_OFF(self,number):
		if number==1:
			self.LED1.configure(bg='red')
			self.port1.write(b'>1,4,0\r')
			self.port1.write(b'>2,4,0\r')
			self.port1.readline()
		elif number==2:
			self.LED2.configure(bg='red')
			self.port1.write(b'>3,4,0\r')
			self.port1.write(b'>4,4,0\r')
			self.port1.readline()
		elif number==3:
			self.LED3.configure(bg='red')
			self.port2.write(b'>1,4,0\r')
			self.port2.write(b'>2,4,0\r')
			self.port2.readline()
		elif number==4:
			self.LED4.configure(bg='red')
			self.port2.write(b'>3,4,0\r')
			self.port2.write(b'>4,4,0\r')
			self.port2.readline()

	def Current_check(self):
		if self.Comcheck1==True:
			print(self.port1)
			self.port1.write(b'>1,34\r')
			print(self.port1.read())
			self.port1.write(b'>2,34\r')
			print(self.port1.read())
			self.port1.write(b'>3,34\r')
			print(self.port1.read())
			self.port1.write(b'>4,34\r')
			print(self.port1.read())
			self.port1.write(b'>16,34\r')
			print(self.port1.read())
			print("........................\n")
		if self.Comcheck2==True:
			self.port2.write(b'>1,34\r')
			print(self.port2.read())
			self.port2.write(b'>2,34\r')
			print(self.port2.read())
			self.port2.write(b'>3,34\r')
			print(self.port2.read())
			self.port2.write(b'>4,34\r')
			print(self.port2.read())
			self.port2.write(b'>16,34\r')
			print(self.port2.read())
			self.port2.write(b'>34,34\r')
			print(self.port2.read())
			
	def Save_as(self):
		data=[('All types(*.*)','*.*')]
		file=asksaveasfile(filetypes=data, defaultextension='.xml')
		date=datetime.datetime.now()
		file.write('VOLTAGE PARAMETERS SAVED : '+date.strftime("%d/%m/%Y %X")+'\n\n')
		file.write('Communication port quad 1 : '+self.Port1_var.get()+'\n')
		file.write('Communication port quad 2 : '+self.Port2_var.get()+'\n\n')
		file.write('Quadrupole 1 :\n')
		file.write('U+ = '+self.Entry1.text.get()+' V'+'\t\tU- = '+self.Entry5.text.get()+' V\n\n')
		file.write('Quadrupole 2 :\n')
		file.write('U+ = '+self.Entry2.text.get()+' V'+'\t\tU- = '+self.Entry6.text.get()+' V\n\n')
		file.write('Quadrupole 3 :\n')
		file.write('U+ = '+self.Entry3.text.get()+' V'+'\t\tU- = '+self.Entry7.text.get()+' V\n\n')
		file.write('Quadrupole 4 :\n')
		file.write('U+ = '+self.Entry4.text.get()+' V'+'\t\tU- = '+self.Entry8.text.get()+' V\n\n')
		file.close()
		
	def Load_Voltage_Parameters(self):
		if self.Comcheck1==False:
			print(self.Comcheck1)
			tk.messagebox.showinfo(title='Error', message='Please connect Port 1 first')
		elif self.Comcheck2==False:
			print(self.Comcheck2)
			tk.messagebox.showinfo(title='Error', message='Please connect Port 2 first')
		else:
			filename = filedialog.askopenfilename(initialdir = "/",title = "Select a File",filetypes = (("Text files","*.txt*"),("all files","*.*")))
			file=open(filename,'r')
			for i in range(7):
				line=file.readline()
			Tab=line.split(" ")
			self.Entry1.text.set(float(Tab[2]))
			self.Entry1.Return_pressed1(self)
			self.Entry5.text.set(float(Tab[-2]))
			self.Entry5.Return_pressed2(self)
			for i in range(3):
				line=file.readline()
			Tab=line.split(" ")
			self.Entry2.text.set(float(Tab[2]))
			self.Entry2.Return_pressed3(self)
			self.Entry6.text.set(float(Tab[-2]))
			self.Entry6.Return_pressed4(self)
			for i in range(3):
				line=file.readline()
			Tab=line.split(" ")
			self.Entry3.text.set(float(Tab[2]))
			self.Entry3.Return_pressed1(self)
			self.Entry7.text.set(float(Tab[-2]))
			self.Entry7.Return_pressed2(self)
			for i in range(3):
				line=file.readline()
			Tab=line.split(" ")
			self.Entry4.text.set(float(Tab[2]))
			self.Entry4.Return_pressed3(self)
			self.Entry8.text.set(float(Tab[-2]))
			self.Entry8.Return_pressed4(self)
			file.close()

#__________________FRAME 3 FUNCTIONS______________________________________

	def Defocus(self, numero):
		if numero==1:
			self.Defocus_Quad1.configure(background='green')
			self.Focus_Quad1.configure(background='white')
		if numero==2:
			self.Defocus_Quad2.configure(background='green')
			self.Focus_Quad2.configure(background='white')
		if numero==3:
			self.Defocus_Quad3.configure(background='green')
			self.Focus_Quad3.configure(background='white')
		if numero==4:
			self.Defocus_Quad4.configure(background='green')
			self.Focus_Quad4.configure(background='white')
			
	def Focus(self, numero):
		if numero==1:
			self.Defocus_Quad1.configure(background='white')
			self.Focus_Quad1.configure(background='green')
		if numero==2:
			self.Defocus_Quad2.configure(background='white')
			self.Focus_Quad2.configure(background='green')
		if numero==3:
			self.Defocus_Quad3.configure(background='white')
			self.Focus_Quad3.configure(background='green')
		if numero==4:
			self.Defocus_Quad4.configure(background='white')
			self.Focus_Quad4.configure(background='green')

	def Parameters(self, param, event):
		if param=='x0':
			self.x0=float(self.text_x0_Frame3.get())
		if param=='a0':
			self.a0=float(self.text_a0_Frame3.get())
		if param=='WD':
			self.WD=float(self.text_WD_Frame3.get())
		if param=='E':
			self.E=float(self.text_E_Frame3.get())
		if param=='d':
			self.d=float(self.text_d_Frame3.get())
		if param=='m':
			self.m=float(self.text_m_Frame3.get())
		if param=='e':
			self.e=float(self.text_e_Frame3.get())
		if param=='L':
			self.L=float(self.text_L_Frame3.get())
			
	
	def Readingloop1(self, port, lock):
		while self.port1_survive:
			lock.acquire()		  # On bloque l'acces au port com pour les autres thread
			port.write(b'>1,2\r') # GET STATUS
			print("1"+str(port.readline()))
			lock.release()		  # On débloque l'acces au port com
			time.sleep(1.1)		   # On attends 1 seconde entre deux lectures
			
	def Readingloop2(self, port, lock):
		while self.port2_survive:
			lock.acquire()		  # On bloque l'acces au port com pour les autres thread
			port.write(b'>1,2\r') # GET STATUS
			print("2"+str(port.readline()))
			lock.release()		  # On débloque l'acces au port com
			time.sleep(1.1)
	
	def WritePortCom(self,port,lock,message):
		lock.acquire()
		port.write(message)
		line=port.readline()
		lock.release()
		return line


#Programme principal
if __name__=='__main__':
	
	window=Window()

# 	def Create_Window():
# 		global window


# 	def create_T2():
# 		Boolean=True
# 		while Boolean==True:
# 			window.Current_check()
# 			if not(t1.is_alive()):
# 				Boolean=False
# 			time.sleep(2)


# 	t1=threading.Thread(target=Create_Window)
# 	t2=threading.Thread(target=create_T2)
# 	t1.start()
# 	t2.start()