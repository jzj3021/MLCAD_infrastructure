from openroad import Tech, Design, Timing
import pdn, odb, utl
import openroad as ord
from pathlib import Path
import os, argparse, shutil, re, sys
import re
import numpy as np
import random

# get the current file's path
current_file = Path(__file__).resolve()

# get the project root directory
project_root = current_file.parent.parent.parent

# add the project root directory to sys.path
sys.path.append(str(project_root))

import OpenROAD_flow as evaluation_flow
from src import evaluation
from src.list_of_design_flow import stages
from src.operator import Operator
from reward_buffer import Reward_buffer

class Agent:
	def __init__(self, design_dir, platflorm, verilog_file = "", work_dir = "../temp", output_verilog = "final.v"):
		"""
		Initialize the Agent with the design directory and platform.
		Args:
			design_dir (str): Path to the design directory.
			platflorm (str): Platform name (e.g., "ASAP7").
			verilog_file (str): Optional path to a specific Verilog file.
		"""
		self.design_dir = design_dir
		self.platform = platflorm
		self.work_dir = work_dir
		self.output_verilog = output_verilog
		self.design_stage = "post_synthesis"
		self.iteration = 0
  
		self.no_impro_iterations = 0

		self.best_score = float('inf')

		self.design_name = os.path.basename(design_dir)

		# Initialize the agent by loading the design and platform
		self.tech = Tech()
		# Set paths to library and design files
		libDir = Path(f"{self.platform}/ASAP7/lib/")
		lefDir = Path(f"{self.platform}/ASAP7/lef/")
		designDir = Path(self.design_dir) / "EDA_files"

		# Read all liberty (.lib) and LEF files from the library directories
		libFiles = libDir.glob("*.lib")
		techLefFiles = lefDir.glob("*tech*.lef")
		lefFiles = lefDir.glob('*.lef')
		
		for libFile in libFiles:
			self.tech.readLiberty(libFile.as_posix())
		
		# Load technology and cell LEF files  
		for techLefFile in techLefFiles:
			self.tech.readLef(techLefFile.as_posix())
		
		for lefFile in lefFiles:
			self.tech.readLef(lefFile.as_posix())
		
		# Initialize the design and operator
		self.design = Design(self.tech)
		self.operator = Operator(self.design, self.work_dir)
		# Read netlist
		if verilog_file == "":
			verilogFile = "%s/%s.v"%(designDir.as_posix(), self.design_name)
			sys.stdout.flush()
		else:
			verilogFile = verilog_file

		self.design.readVerilog(verilogFile)
		self.design.link(self.design_name)
		# Config Global Net Connect
		evaluation_flow.config_gnc(self.design)

		# Read floorplan def file
		defFile = "%s/%s_fp.def.gz"%(designDir.as_posix(), self.design_name)
		self.design.evalTclString("read_def -floorplan_initialize "+defFile)

		# Read the SDC file
		sdcFile = "%s/%s.sdc"%(designDir.as_posix(), self.design_name)
		self.design.evalTclString("read_sdc %s"%sdcFile)
		self.design.evalTclString("source ../../platform/ASAP7/setRC.tcl")

		# Initialize the reward buffer for reinforcement learning
		reward_buffer_size = 4 * self.operator.num_operators
		self.reward_buffer = Reward_buffer(self.operator.num_operators, reward_buffer_size = reward_buffer_size)

	def global_placement(self):
		"""
		Perform global placement on the design.
		"""
		# Run global placement
		self.design.evalTclString("global_placement -routability_driven -init_density_penalty 0.05 -initial_place_max_iter 10")
		self.design_stage = "global_placement"
		self.design.evalTclString("estimate_parasitics -placement")
  
	def repair_design(self, *args):
		self.design.evalTclString("repair_design")
  
	def repair_timing(self, *args):
		self.design.evalTclString("repair_timing")

	def detail_placement(self):
		"""
		Perform detailed placement on the design.
		"""
		if stages[self.design_stage] < stages["global_placement"]:
			print("Run global placement first")
			sys.stdout.flush()
			return None
		
		site = self.design.getBlock().getRows()[0].getSite()
		max_disp_x = int((self.design.getBlock().getBBox().xMax() - self.design.getBlock().getBBox().xMin()) / site.getWidth())
		max_disp_y = int((self.design.getBlock().getBBox().yMax() - self.design.getBlock().getBBox().yMin()) / site.getHeight())
		print("###run legalization###")
		sys.stdout.flush()
		self.design.getOpendp().detailedPlacement(max_disp_x, max_disp_y, "")
		pass

	def global_routing(self):
		"""
		Perform global routing on the design.
		"""
		if stages[self.design_stage] < stages["detail_placement"]:
			print("Run detailed placement first")
			sys.stdout.flush()
			return None
		
		# Run Global Routing and Estimate Global Routing RC
		signal_low_layer = self.design.getTech().getDB().getTech().findLayer("M1").getRoutingLevel()
		signal_high_layer = self.design.getTech().getDB().getTech().findLayer("M8").getRoutingLevel()
		clk_low_layer = self.design.getTech().getDB().getTech().findLayer("M1").getRoutingLevel()
		clk_high_layer = self.design.getTech().getDB().getTech().findLayer("M8").getRoutingLevel()
		grt = self.design.getGlobalRouter()
		grt.clear()
		grt.setAllowCongestion(True)
		grt.setMinRoutingLayer(signal_low_layer)
		grt.setMaxRoutingLayer(signal_high_layer)
		grt.setMinLayerForClock(clk_low_layer)
		grt.setMaxLayerForClock(clk_high_layer)
		grt.setAdjustment(0.5)
		grt.setVerbose(True)
		print("###run global routing###")
		sys.stdout.flush()
		grt.globalRoute(False)
		self.design_stage = "global_routing"
	
	def reinitialize(self, verilog_file = ""):
		self.operator = Operator(self.design, self.work_dir)
		# Read netlist
		if verilog_file == "":
			verilogFile = "%s/%s.v"%(self.design_dir.as_posix(), self.design_name)
		else:
			verilogFile = verilog_file
		
		self.design.readVerilog(verilogFile)
		self.design.link(self.design_name)
		# Config Global Net Connect
		evaluation_flow.config_gnc(self.design)

		# Read floorplan def file
		defFile = "%s/%s_fp.def.gz"%(self.design_dir.as_posix(), self.design_name)
		self.design.evalTclString("read_def -floorplan_initialize "+defFile)

		# Read the SDC file
		sdcFile = "%s/%s.sdc"%(self.design_dir.as_posix(), self.design_name)
		self.design.evalTclString("read_sdc %s"%sdcFile)
		self.design.evalTclString("source ../../platform/ASAP7/setRC.tcl")
 
	def get_timing(self):
		"""
		Report timing metrics of the design.
		"""
		print("###report slack###")
		self.design.evalTclString("report_worst_slack -min -digits 3")
		print("###report wns and tns###")
		self.design.evalTclString("report_wns -digits 3")
		self.design.evalTclString("report_tns -digits 3")
		sys.stdout.flush()
	
	def get_area(self):
		"""
		Report area metrics of the design.
		"""
		print("###report area###")
		self.design.evalTclString("report_area -digits 3")
		print("###report utilization###")
		self.design.evalTclString("report_utilization -digits 3")
		sys.stdout.flush()

	def get_score(self, design_name = "", return_metrics = False):
		"""
		Calculate the score of the design based on timing and power metrics.
		Returns:
			dict: A dictionary containing timing and power scores.
		"""
		if os.path.exists(self.work_dir):
			evaluator = evaluation.Evaluator(self.design, work_dir=self.work_dir, design_name=self.design_name)
			if stages[self.design_stage] < stages["global_placement"]:
				print("Run global placement first")
				sys.stdout.flush()
				return None
			elif stages[self.design_stage] < stages["global_routing"]:
				metrics = evaluator.post_place_evaluate(design_name = design_name)
			elif stages[self.design_stage] >= stages["global_routing"]:
				metrics = evaluator.e2e_evaluate(design_name = design_name)

			if return_metrics:
				return metrics
	
			score = evaluation_flow.compute_score(Path(self.work_dir) / "temp.score", *metrics)
		if score is None:
			raise Exception("Failed to compute score.")
		else:
			return score

	def operate(self, action, replace: bool = False, *args):
		"""
		Perform an operation based on the provided action.
		Args:
			action (str): The action to perform (e.g., "gate sizing, gate cloning, pin swapping, etc.").

			In this framework, we list available actions as follows:
			1: gate sizing
			2: gate cloning
			3: pin swapping
			4: buffering
			5: 
		"""
		self.operator.operate(action, *args)
		if replace:
			self.global_placement()
		else:
			self.design.evalTclString("estimate_parasitics -placement")
		self.iteration += 1

	def terminate(self):
		"""
		Check if the optimization process should terminate.
		Returns:
			bool: True if the process should terminate, False otherwise.
		"""
		terminate = False
		if self.iteration > 30:
			return True
		if self.no_impro_iterations > 5:
			terminate = True
		if self.iteration > 3:
			print("Reached maximum iterations. Check if continue.")
			sys.stdout.flush()
		
			pos = self.reward_buffer.get_pos()
			if pos > 1:
				buffer = self.reward_buffer.get_reward_buffer()
				last_score = buffer[pos-2]
				current_score = buffer[pos-1]
				if (current_score - last_score) < 1:
					self.no_impro_iterations += 1
					print("No significant improvement in score. Terminating the process.")
					sys.stdout.flush()

		return terminate
	
	def update_reward(self, action, score):
		"""
		Update the reward buffer with the new reward value.
		Args:
			reward (float): The new reward value to add to the buffer.
		"""
		self.reward_buffer.update_reward(action, score)

	def get_next_operator(self, rand: bool = False):
		"""
		Get the next operator to perform based on the current design stage.
		Returns:
			str: The index of the next operator to perform. If random is True, return random operator.
		"""
		if rand:
			return random.randint(0, self.operator.num_operators - 1)
		action_score = self.reward_buffer.get_action_score()
		best_operator = np.argmax(action_score)
		return best_operator

	def re_placement(self):
		"""
		Re-run the placement process to adjust the design layout.
		This function set all the instances to be unplaced and re-run the placement.
		"""
	
	def write_verilog(self, verilog_file):
		"""
		Write the design to a Verilog file.
		Args:
			verilog_file (str): The path to the output Verilog file.
		"""
		self.design.evalTclString("write_verilog %s"%(verilog_file))
		print("###write verilog to %s###"%(verilog_file))
		sys.stdout.flush()

	def record_design(self, score: float = 0.0):
		"""
		Record the current design state by saving the design to a verilog file.
		"""
		if not (Path(self.work_dir) / self.design_name).exists():
			os.makedirs(Path(self.work_dir) / self.design_name)
		action_seq = self.reward_buffer.get_action_trials()
		pos = self.reward_buffer.get_pos()
		fname = [str(action_seq[i]) for i in range(pos)]
		fname = self.design_name + "".join(fname)
		print("###record design to %s/%s.v###"%(Path(self.work_dir) / self.design_name, fname))
		self.design.evalTclString("write_verilog %s/%s_%f.v"%(Path(self.work_dir) / self.design_name, fname, score))

	def run(self):
		"""
		Run the design flow involving both physical design and optimization stages.
		"""
		self.global_placement()
		self.record_design()

		while(self.terminate() == False):
			# Get the next operator
			action = self.get_next_operator()
			if action is None:
				print("No more operators available.")
				sys.stdout.flush()
				break
			# Perform the operation
			self.operate(action)
			# Get the score after the operation
			action_seq = self.reward_buffer.get_action_trials()
			action_seq = [str(i) for i in action_seq]
			design_name = self.design_name + "_" + "".join(action_seq) 
			score = self.get_score(design_name)
			if score < self.best_score:
				self.write_verilog(self.output_verilog)
		
			if score is None:
				raise Exception("Failed to get score after operation.")
			self.update_reward(action, score)
			# self.record_design(score)
		
		self.detail_placement()
		self.global_routing()
		self.repair_design()
		self.repair_timing()
  
		###### Final evaluation ######
		self.design.evalTclString("exit")

if __name__ == "__main__":
	# Example usage
	design_base = Path("/app/MLCAD25-Contest-Scripts-Benchmarks/designs")
	platform = "/app/MLCAD25-Contest-Scripts-Benchmarks/platform"
	temp_dir = "/app/MLCAD25-Contest-Scripts-Benchmarks/src/MLCAD_infrastructure/temp"
	# agent = Agent(design_dir=design_dir, platflorm=platform, verilog_file="/app/MLCAD25-Contest-Scripts-Benchmarks/designs/ac97_top/EDA_files/ac97_top.v", work_dir=temp_dir)
	# agent.run()
	
	parser = argparse.ArgumentParser(description="Options to run agent. Give design name.")
	parser.add_argument("--design_name", type=str, default="ac97_top", help="Name of the design to run.")
	parser.add_argument("--output_verilog", type=str, default="final.v", help="Output Verilog file name.")
	args = parser.parse_args()
	agent = Agent(design_dir=design_base/args.design_name, platflorm=platform, work_dir=temp_dir, output_verilog=args.output_verilog)
	agent.run()
 
	# agent2 = Agent(design_dir=args.design_dir, platflorm=platform, work_dir=temp_dir)
	# agent2.run()
	# evaluation_flow.run_flow(design_name=agent.design_name, verilog_file=agent.output)