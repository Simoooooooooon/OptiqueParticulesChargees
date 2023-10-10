# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 13:32:05 2023

@author: cayez
Test en lecture et ecriture usb pyvisa sur alim Instek

"""




import pyvisa

rm = pyvisa.ResourceManager()

rm.list_resources()

# rm = pyvisa.ResourceManager()

print('-----------------------------')
print(rm.list_resources())

print('-----------------------------')

my_instrument = rm.open_resource('ASRL8::INSTR')

print(my_instrument.query('*IDN?'))
print('CH1 curent setting (A) : ',my_instrument.query('ISET1?'))

my_instrument.write('VSET1:5.23')
print('CH1 voltage setting (V) : ',my_instrument.query('VSET1?'))
my_instrument.write('VSET1:0.0')
print('CH1 voltage setting (V) : ',my_instrument.query('VSET1?'))

