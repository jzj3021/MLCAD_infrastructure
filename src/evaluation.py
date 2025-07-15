from openroad import Tech, Design, Timing
import pdn, odb, utl
import openroad as ord
from pathlib import Path
import os, argparse, shutil, re, sys
import re


class Evaluator:
	def __init__(self, design: Design, work_dir: str = "../temp", design_name: str = ""):
		self.design = design
		self.work_dir = work_dir
		self.design_name = design_name

	def e2e_evaluate(self, fname = "", design_name = ""):
		if fname == "":
			fname = self.work_dir + "/gr_results.csv"
		else:	
			fname = self.work_dir + "/" + fname
		# Get all timing metrices, this evaluation should be run after the design is routed      
		timing = Timing(self.design)
		corner = timing.getCorners()[0]
		
		self.design.evalTclString(f"report_tns > {self.work_dir}/evaluation_temp.txt")
		with open (f"{self.work_dir}/evaluation_temp.txt", "r") as file:
			for line in file:
				tns = float(line.split()[-1]) / 1000
		os.remove(f"{self.work_dir}/evaluation_temp.txt")
		
		self.design.evalTclString(f"report_wns > {self.work_dir}/evaluation_temp.txt")
		with open (f"{self.work_dir}/evaluation_temp.txt", "r") as file:
			for line in file:
				wns = float(line.split()[-1]) / 1000
		os.remove(f"{self.work_dir}/evaluation_temp.txt")

		slew_viol_count = 0
		cap_viol_count = 0
		slew = 0
		cap = 0
		leakage = 0
		
		for pin_ in self.design.getBlock().getITerms():
			if pin_.getNet() != None:
				if pin_.getNet().getSigType() != 'POWER' and pin_.getNet().getSigType() != 'GROUND' and pin_.getNet().getSigType() != 'CLOCK' and not re.match(".*/SETN$", pin_.getName()) and not re.match(".*/RESETN$", pin_.getName()) :
					library_cell_pin = [MTerm for MTerm in pin_.getInst().getMaster().getMTerms() if (pin_.getInst().getName() + "/" + MTerm.getName()) == pin_.getName()][0]
					if timing.getMaxSlewLimit(library_cell_pin) < timing.getPinSlew(pin_):
						diff = abs(timing.getMaxSlewLimit(library_cell_pin) - timing.getPinSlew(pin_)) * 1e9
						slew += diff
						slew_viol_count += 1
					if pin_.isOutputSignal():
						if timing.getMaxCapLimit(library_cell_pin) < timing.getNetCap(pin_.getNet(), corner, timing.Max):
							diff = abs(timing.getMaxCapLimit(library_cell_pin) - timing.getNetCap(pin_.getNet(), corner, timing.Max)) * 1e15
							cap += diff
							cap_viol_count += 1
		db = ord.get_db()
		swapped_master = {}

		insts = self.design.getBlock().getInsts()
		for inst in insts:
			leakage += timing.staticPower(inst, corner)
			if not inst.getMaster().isBlock() and self.design.isSequential(inst.getMaster()):
				swapped_master[inst.getName()] = inst.getMaster().getName()
		leakage *= 1e6
		leakageBeforeSwap = 0
		
		design_name = self.design.getBlock().getName()
		total_insts = len(insts)

		# self.design.evalTclString("report_tns")

		grt = self.design.getGlobalRouter()
		# print("GlobalRouter attributes and methods:", dir(grt))
		overflow = grt.getOverflow()

		out_str = design_name+","+str(total_insts)+","+str(wns)+","+str(tns)+","+str(slew)+","+str(slew_viol_count)+","+str(cap)+","+str(cap_viol_count)+","+str(leakage)+","+str(overflow)+'\n'
		with open(fname,'a') as fp:
				fp.write(out_str)

		return leakage, tns, slew, cap, overflow
	
	def post_place_evaluate(self, fname = "", design_name = ""):
		# Get all timing metrices, this evaluation should be run after the design is routed      
		if fname == "":
			fname = self.work_dir + "/post_place_results.csv"
		else:
			fname = self.work_dir + "/" + fname
		timing = Timing(self.design)
		corner = timing.getCorners()[0]
		
		self.design.evalTclString(f"report_tns > {self.design_name}_evaluation_temp.txt")
		with open (f"{self.design_name}_evaluation_temp.txt", "r") as file:
			for line in file:
				tns = float(line.split()[-1]) / 1000
		os.remove(f"{self.design_name}_evaluation_temp.txt")
		
		self.design.evalTclString(f"report_tns > {self.design_name}_evaluation_temp.txt")
		with open (f"{self.design_name}_evaluation_temp.txt", "r") as file:
			for line in file:
				wns = float(line.split()[-1]) / 1000
		os.remove(f"{self.design_name}_evaluation_temp.txt")

		slew_viol_count = 0
		cap_viol_count = 0
		slew = 0
		cap = 0
		leakage = 0
		
		for pin_ in self.design.getBlock().getITerms():
			if pin_.getNet() != None:
				if pin_.getNet().getSigType() != 'POWER' and pin_.getNet().getSigType() != 'GROUND' and pin_.getNet().getSigType() != 'CLOCK' and not re.match(".*/SETN$", pin_.getName()) and not re.match(".*/RESETN$", pin_.getName()) :
					library_cell_pin = [MTerm for MTerm in pin_.getInst().getMaster().getMTerms() if (pin_.getInst().getName() + "/" + MTerm.getName()) == pin_.getName()][0]
					if timing.getMaxSlewLimit(library_cell_pin) < timing.getPinSlew(pin_):
						diff = abs(timing.getMaxSlewLimit(library_cell_pin) - timing.getPinSlew(pin_)) * 1e9
						slew += diff
						slew_viol_count += 1
					if pin_.isOutputSignal():
						if timing.getMaxCapLimit(library_cell_pin) < timing.getNetCap(pin_.getNet(), corner, timing.Max):
							diff = abs(timing.getMaxCapLimit(library_cell_pin) - timing.getNetCap(pin_.getNet(), corner, timing.Max)) * 1e15
							cap += diff
							cap_viol_count += 1
		db = ord.get_db()
		swapped_master = {}

		insts = self.design.getBlock().getInsts()
		for inst in insts:
			leakage += timing.staticPower(inst, corner)
			if not inst.getMaster().isBlock() and self.design.isSequential(inst.getMaster()):
				swapped_master[inst.getName()] = inst.getMaster().getName()
		leakage *= 1e6
		leakageBeforeSwap = 0
		
		design_name = self.design.getBlock().getName() if design_name == "" else design_name
		total_insts = len(insts)

		# self.design.evalTclString("report_tns")

		overflow = 0	# Placeholder for overflow, as it is not available in post-place evaluation

		out_str = design_name+","+str(total_insts)+","+str(wns)+","+str(tns)+","+str(slew)+","+str(slew_viol_count)+","+str(cap)+","+str(cap_viol_count)+","+str(leakage)+","+str(overflow)+'\n'
		with open(fname,'a') as fp:
				fp.write(out_str)

		return leakage, tns, slew, cap, overflow