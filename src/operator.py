from openroad import Tech, Design, Timing
import pdn, odb, utl
import openroad as ord
from pathlib import Path
import os, argparse, shutil, re, sys
import re

class ModularizedDesign(Design):
    '''
    Split openroad repair_timing command into subcommands.
    When designer uses "repair_timing" command, if [-recover_power percent_of_paths_with_slack] flag is not set, "repair_timing -setup" and "repair_timing -hold" are executed sequentially.
    The default flow of "repair_timing -setup" is remove_buffer -> upsize_driver(mandatory) -> swap_pin -> gate_clone -> split_load -> last_gasp.
    '''
    def remove_buffer(self):
        self.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffering -skip_last_gasp")
    def upsize_driver(self):
        self.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffering -skip_buffer_removal -skip_last_gasp")
    def swap_pin(self):
        self.evalTclString("repair_timing -setup -skip_gate_cloning -skip_buffering -skip_buffer_removal -skip_last_gasp")
    def gate_clone(self):
        self.evalTclString("repair_timing -setup -skip_pin_swap -skip_buffering -skip_buffer_removal -skip_last_gasp")
    def split_load(self):
        self.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffer_removal -skip_last_gasp")
    def last_gasp(self):
        self.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffering -skip_buffer_removal -skip_last_gasp")
		
class Operator:
	def __init__(self, design: ModularizedDesign, work_dir: str = "../temp"):
		"""
		Initialize the Operator with a Design object.
		Args:
			design (Design): The Design object to operate on.
		"""
		self.design = design
		self.work_dir = work_dir

		"""
		In this framework, we list available actions as follows:
			1: gate sizing
			2: gate cloning
			3: pin swapping
			4: buffering
			5: load splitting
		"""
		self.available_operators = [
			"gate_sizing",
			"gate_cloning",
			"pin_swapping",
			"buffering",
			"load_splitting"
		]

		self.num_operators = len(self.available_operators)
	
	def operate(self, operator_index, verbose: bool = 0, *args):
		if operator_index > len(self.available_operators):
			raise ValueError("Invalid operator index. Please choose a valid operator.")
		if operator_index < 0:
			raise ValueError("Invalid operator index. Please choose a valid operator.")
		
		operator_name = self.available_operators[operator_index]
		if operator_index == 0:
			# Perform gate sizing
			self.gateSizing()
		elif operator_index == 1:
			# Perform gate cloning
			self.gateCloning()
		elif operator_index == 2:
			# Perform pin swapping
			self.pinSwapping()
		elif operator_index == 3:
			# Perform buffering
			self.buffering()
		else:
			pass
		
	def load_splitting(self):
		"""
		Perform load splitting operation.
		"""
		self.design.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffer_removal -skip_last_gasp")
  
	def gateSizing(self):
		"""
		Perform gate sizing operation.
		"""
		print("Performing gate sizing operation...")
		# Implement gate sizing logic here
		self.design.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffering -skip_buffer_removal -skip_last_gasp")

	def gateCloning(self):
		"""
		Perform gate cloning operation.
		"""
		print("Performing gate cloning operation...")
		# Implement gate cloning logic here
		self.design.evalTclString("repair_timing -setup -skip_pin_swap -skip_buffering -skip_buffer_removal -skip_last_gasp")

	def pinSwapping(self):
		"""
		Perform pin swapping operation.
		"""
		print("Performing pin swapping operation...")
		# Implement pin swapping logic here
		self.design.evalTclString("repair_timing -setup -skip_gate_cloning -skip_buffering -skip_buffer_removal -skip_last_gasp")

	def buffering(self):
		"""
		Perform buffering operation.
		"""
		print("Performing buffering operation...")
		# Implement buffering logic here
		self.design.evalTclString("repair_timing -setup -skip_pin_swap -skip_gate_cloning -skip_buffer_removal -skip_last_gasp")

	
