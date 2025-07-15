from openroad import Tech, Design, Timing
import pdn, odb, utl
import openroad as ord
from pathlib import Path
import os, argparse, shutil, re, sys

sys.path.insert(0, "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src")

# Import src
from src.conditioning import conditioner
import OpenROAD_flow as evaluator


base_file="/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks"
temp_dir=f"{base_file}/src/evaluation/temp"

def config_gnc(design):
    for net in design.getBlock().getNets():
        if net.getSigType() == "POWER" or net.getSigType() == "GROUND":
            net.setSpecial()

    VDD_net = design.getBlock().findNet("VDD")
    VSS_net = design.getBlock().findNet("VSS")

    # Create VDD/VSS nets if they don't exist
    if VDD_net == None:
        VDD_net = odb.dbNet_create(design.getBlock(), "VDD")
        VDD_net.setSpecial()
        VDD_net.setSigType("POWER")
        odb.dbBTerm_create(VDD_net , 'VDD')

    if VSS_net == None:
        VSS_net = odb.dbNet_create(design.getBlock(), "VSS")
        VSS_net.setSpecial()
        VSS_net.setSigType("GROUND")
        odb.dbBTerm_create(VSS_net , 'VSS')
    
    # Connect power pins to global nets
    design.getBlock().addGlobalConnect(region = None,
        instPattern = ".*", 
        pinPattern = "^VDD$",
        net = VDD_net, 
        do_connect = True)
    design.getBlock().addGlobalConnect(region = None,
        instPattern = ".*",
        pinPattern = "^VDDPE$",
        net = VDD_net,
        do_connect = True)
    design.getBlock().addGlobalConnect(region = None,
        instPattern = ".*",
        pinPattern = "^VDDCE$",
        net = VDD_net,
        do_connect = True)
    design.getBlock().addGlobalConnect(region = None,
        instPattern = ".*",
        pinPattern = "^VSS$",
        net = VSS_net, 
        do_connect = True)
    design.getBlock().addGlobalConnect(region = None,
        instPattern = ".*",
        pinPattern = "^VSSE$",
        net = VSS_net,
        do_connect = True)
    design.getBlock().globalConnect()

def run_flow(design_name, lefDir, libDir, sdc_file, outputDir):
    # This is the flow to run placement and global routing using OpenROAD.
    # The same flow will be used during evaluation phase.
    
    # Initialize OpenROAD objects and read technology files
    tech = Tech()
    # Set paths to library and design files
    designDir = Path(f"{base_file}/designs/%s/EDA_files/"%design_name)

    # Read all liberty (.lib) and LEF files from the library directories
    libFiles = libDir.glob("*.lib")
    techLefFiles = lefDir.glob("*tech*.lef")
    lefFiles = lefDir.glob('*.lef')
    
    # Load liberty timing libraries
    for libFile in libFiles:
        tech.readLiberty(libFile.as_posix())
    
    # Load technology and cell LEF files  
    for techLefFile in techLefFiles:
        tech.readLef(techLefFile.as_posix())
    
    for lefFile in lefFiles:
        tech.readLef(lefFile.as_posix())
    
    design = Design(tech)

    # Read netlist
    verilogFile = "%s/%s.v"%(designDir.as_posix(), design_name)
    design.readVerilog(verilogFile)
    design.link(design_name)
    
    # Config Global Net Connect
    config_gnc(design)

    # Read floorplan def file
    defFile = "%s/%s_fp.def.gz"%(designDir.as_posix(), design_name)
    design.evalTclString("read_def -floorplan_initialize "+defFile)
    #design.readDef(defFile)
   
    # Read the SDC file
    #sdcFile = "%s/%s.sdc"%(designDir.as_posix(), design_name)
    # sdcFile = f"./config/ac97_top/{design_name}/{design_name}.sdc"
    design.evalTclString("read_sdc %s"%sdc_file)
    design.evalTclString("source ../../platform/ASAP7/setRC.tcl")

    print("###run pre-placement repair design###")
    sys.stdout.flush()
    # Run pre-placement repair design
    # design.evalTclString("remove_buffers")
    # design.evalTclString("estimate_parasitics -placement")
    # design.evalTclString("repair_design -pre_placement -slew_margin 10 -cap_margin 10 -verbose")
    
    ## Configure and run global placement
    #print("###run global placement###")
    #sys.stdout.flush()
#
    #design.evalTclString("global_placement -routability_driven -init_density_penalty 0.05 -initial_place_max_iter 10")
    ##design.evalTclString("global_placement -timing_driven")
#
    ## Run initial detailed placement
    #site = design.getBlock().getRows()[0].getSite()
    #max_disp_x = int((design.getBlock().getBBox().xMax() - design.getBlock().getBBox().xMin()) / site.getWidth())
    #max_disp_y = int((design.getBlock().getBBox().yMax() - design.getBlock().getBBox().yMin()) / site.getHeight())
    #print("###run legalization###")
    #sys.stdout.flush()
    #design.getOpendp().detailedPlacement(max_disp_x, max_disp_y, "")
    ##design.evalTclString("estimate_parasitics -placement")
    #
    ## Run Global Routing and Estimate Global Routing RC
    #signal_low_layer = design.getTech().getDB().getTech().findLayer("M1").getRoutingLevel()
    #signal_high_layer = design.getTech().getDB().getTech().findLayer("M8").getRoutingLevel()
    #clk_low_layer = design.getTech().getDB().getTech().findLayer("M1").getRoutingLevel()
    #clk_high_layer = design.getTech().getDB().getTech().findLayer("M8").getRoutingLevel()
    #grt = design.getGlobalRouter()
    #grt.clear()
    #grt.setAllowCongestion(True)
    #grt.setMinRoutingLayer(signal_low_layer)
    #grt.setMaxRoutingLayer(signal_high_layer)
    #grt.setMinLayerForClock(clk_low_layer)
    #grt.setMaxLayerForClock(clk_high_layer)
    #grt.setAdjustment(0.5)
    #grt.setVerbose(True)
    #print("###run global routing###")
    #sys.stdout.flush()
    #grt.globalRoute(False)
#
    ##design.evalTclString("set_routing_layers -signal M1-M8 -clock M1-M8")
    ##design.evalTclString("set_global_routing_layer_adjustment * 0.5")
    ##design.evalTclString("global_route -allow_congestion")
    #design.evalTclString("estimate_parasitics -global_routing")
#
    ## Modified by user. Use openroad to optimize timing
    ##design.evalTclString("remove_buffers")
    #print("###run repair design###")
    #sys.stdout.flush()
    #design.evalTclString("repair_design -verbose")
    #print("###run repair timing###")
    #design.evalTclString("repair_timing -verbose")

    print("###run global placement###")
    sys.stdout.flush()

    design.evalTclString("global_placement -routability_driven -init_density_penalty 0.05 -initial_place_max_iter 10")
    #design.evalTclString("global_placement -timing_driven")

    # Run initial detailed placement
    site = design.getBlock().getRows()[0].getSite()
    max_disp_x = int((design.getBlock().getBBox().xMax() - design.getBlock().getBBox().xMin()) / site.getWidth())
    max_disp_y = int((design.getBlock().getBBox().yMax() - design.getBlock().getBBox().yMin()) / site.getHeight())
    print("###run legalization###")
    sys.stdout.flush()
    design.getOpendp().detailedPlacement(max_disp_x, max_disp_y, "")
    
    # Run Global Routing and Estimate Global Routing RC
    # signal_low_layer = design.getTech().getDB().getTech().findLayer("M1").getRoutingLevel()
    # signal_high_layer = design.getTech().getDB().getTech().findLayer("M8").getRoutingLevel()
    # clk_low_layer = design.getTech().getDB().getTech().findLayer("M1").getRoutingLevel()
    # clk_high_layer = design.getTech().getDB().getTech().findLayer("M8").getRoutingLevel()
    # grt = design.getGlobalRouter()
    # grt.clear()
    # grt.setAllowCongestion(True)
    # grt.setMinRoutingLayer(signal_low_layer)
    # grt.setMaxRoutingLayer(signal_high_layer)
    # grt.setMinLayerForClock(clk_low_layer)
    # grt.setMaxLayerForClock(clk_high_layer)
    # grt.setAdjustment(0.5)
    # grt.setVerbose(True)
    # print("###run global routing###")
    # sys.stdout.flush()
    # grt.globalRoute(False)

    #design.evalTclString("set_routing_layers -signal M1-M8 -clock M1-M8")
    #design.evalTclString("set_global_routing_layer_adjustment * 0.5")
    #design.evalTclString("global_route -allow_congestion")
    # design.evalTclString("estimate_parasitics -global_routing")

    # Modified by user. Use openroad to optimize timing
    print("###run repair design###")
    sys.stdout.flush()
    
    # design.evalTclString("repair_design -verbose")
    print("###run repair timing###")
    sys.stdout.flush()
    # design.evalTclString("repair_timing -verbose -repair_tns 100")

    #os.system(f"cp {verilogFile} backup_{design_name}.v")
    #design.evalTclString("write_verilog %s"%verilogFile)
    design.evalTclString(f"write_verilog {outputDir}/{design_name}.v")
    # exit()
    os._exit(0)

    #os.system(f"../../OpenROAD/build/src/openroad -python OpenROAD_flow.py -d {design_name}")
    #os.system(f"cp backup_{design_name}.v {verilogFile} && rm backup_{design_name}.v")

if __name__ == "__main__":   
    parser = argparse.ArgumentParser(description="Options to run Floorplan to Global route in OpenROAD. Give design name.")
    parser.add_argument("-design", default="ac97_top", help="Design name")
    parser.add_argument("-lef", default=f"{base_file}/platform/ASAP7/lef/", help="Path to LEF files")
    parser.add_argument("-lib", default=f"{base_file}/platform/ASAP7/lib/", help="Path to Liberty files")
    parser.add_argument("-output", default=f"{base_file}/src/evaluation/results/", help="Output directory for resynthesized netlist")
    parser.add_argument("-timing_tune", default=0.0, help="Ratio to tune timing in SDC file, e.g., 0.05 for 5% increase in clock period")
    args = parser.parse_args()

    timing_difference = float(args.timing_tune)
    # Condition the SDC file
    cond = conditioner(args.design, f"{base_file}/src/evaluation/config/{args.design}/{args.design}.sdc", temp_dir)
    cond.tune_sdc(timing_difference)


    log_file = f"./logs/{args.design}_run_flow.log"
    log_f = open(log_file, "w")
    os.dup2(log_f.fileno(), 1)  # 重定向 stdout
    os.dup2(log_f.fileno(), 2)
    with open("run_flow_output.log", "w") as f:
        sys.stdout = f
        try:
            run_flow(args.design, Path(args.lef), Path(args.lib), cond.temp_file, args.output)
            evaluator.run_flow(args.design, f"{args.output}/{args.design}.v")
        finally:
            sys.stdout = sys.__stdout__ 