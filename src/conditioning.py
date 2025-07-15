import re



class conditioner:
    def __init__(self, design, sdc_file, temp_dir="./temp"):
        self.design = design
        self.sdc_file = sdc_file
        print(f"temp_dir: {temp_dir}")
        self.temp_file = temp_dir + f"/{design}_tuned.sdc"

    def tune_sdc(self, variation):
        # 读取原始SDC文件
        with open(self.sdc_file, 'r') as file:
            content = file.read()

        # 匹配 create_clock 行，提取周期和下降沿
        pattern = re.compile(
            r"(create_clock\s+-name\s+clk\s+-period\s+)([\d\.]+)(\s+\[get_ports\s+\S+\])"
        )
        match = pattern.search(content)

        if match:
            original_period = float(match.group(2))  # 只取周期数字并转为float
            new_period = original_period * (1 + variation)

            print(f"Original period: {original_period}, New period: {new_period}")

            new_clock_line = (
                f"{match.group(1)}{new_period:.3f}{match.group(3)}"
            )
            new_content = pattern.sub(new_clock_line, content)

            with open(self.temp_file, 'w') as temp:
                temp.write(new_content)
        else:
            raise ValueError(f"Clock definition not found in SDC file. file name: {self.sdc_file}")
        # 读取原始SDC文件
    #     with open(self.sdc_file, 'r') as file:
    #         content = file.read()

    #     # 匹配 create_clock 行，提取周期和下降沿
    #     pattern = re.compile(
    #         r"create_clock\s+\[get_ports\s+\{([^\}]+)\}\]\s+-name\s+([^\s]+)\s+-period\s+([\d\.]+)\s+-waveform\s+\{[\d\.]+\s+([\d\.]+)\}"
    #     )
    #     match = pattern.search(content)

    #     if match:
    #         port_name = match.group(1)
    #         clk_name = match.group(2)
    #         original_period = float(match.group(3))
    #         original_fall_edge = float(match.group(4))

    #         new_period = original_period * (1 + variation)
    #         new_fall_edge = new_period / 2  # 通常下降沿为周期一半

    #         print(f"Original period: {original_period}, New period: {new_period}")
    #         print(f"Original fall edge: {original_fall_edge}, New fall edge: {new_fall_edge}")

    #         new_clock_line = (
    #             f"create_clock [get_ports {{{port_name}}}] "
    #             f"-name {clk_name} -period {new_period:.3f} "
    #             f"-waveform {{0.000000 {new_fall_edge:.3f}}}"
    #         )
    #         new_content = pattern.sub(new_clock_line, content)

    #         with open(self.temp_file, 'w') as temp:
    #             temp.write(new_content)
    #     else:
    #         raise ValueError(f"Clock definition not found in SDC file. file name: {self.sdc_file}")


    def size(self):
        




# Test condition the sdc
# if __name__ == "__main__":
#     # Example usage
#     design = "ac96_top"
#     sdc_file = "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/config/ac97_top/ac97_top.sdc"
#     temp_dir = "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/temp"
#     variation = 0.05  # Example variation of 5%
#     cond = conditioner(design, sdc_file, temp_dir)
#     try:
#         cond.tune_sdc(variation)
#         print(f"SDC file tuned successfully for design {design} with variation {variation}.")
#     except ValueError as e:
#         print(f"Error tuning SDC file: {e}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")