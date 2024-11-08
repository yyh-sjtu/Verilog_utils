"""
Author: Yunhao Zhou
Date: 2024-8-11
"""

import re
from glob import glob
import os
import json

def remove_comments(text):
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text

def module_dict_extractor(text) -> dict :
    text = remove_comments(text)
    module_dict = {}
    pattern = r'module\s+[^\(\s]+\s*(?:#\s*\(.*?\))?\s*\(.*?\)\s*;\s*?(?:(?!module\s).)*?\bendmodule'
    verilog_code_extracted = re.findall(pattern, text, re.DOTALL)
    
    for module in verilog_code_extracted:
        # module_name = re.search(r'module\s+([^\(\s]+)', module).group(1)
        module_name = re.findall(r'module\s+([^\(\s]+)', module, re.DOTALL)[0]
        module_dict[module_name] = module

    return module_dict

def module_dict_extractor_from_file_list(file_list: list):
    """
    Extract module from filt_list
    """
    file_list = [x for x in file_list if x != '' and x != ' ']
    text = ''
    for file in file_list:
        with open(file, 'r', encoding="utf-8", errors="ignore") as f:
            text += f.read()
    
    return module_dict_extractor(text)
        
def verilog_extractor(text) -> str:
    verilog = ""
    endmodule_count = text.count("endmodule")
    
    pattern = r'module\s+[^\(\s]+\s*(?:#\s*\(.*?\))?\s*\(.*?\)\s*;\s*?(?:(?!module\s).)*?\bendmodule'
    verilog_code_extracted = re.findall(pattern, text, re.DOTALL)
    for module in verilog_code_extracted:
        verilog += (module + '\n\n')
            
    if endmodule_count > len(verilog_code_extracted):
        print("Warning: Risk of missing some modules while extracting Verilog code.")
            
    return verilog

def verilog_extractor_from_file_list(file_list) -> str:
    verilog = ""
    for file in file_list:
        with open(file, 'r', encoding="utf-8", errors="ignore") as f:
            verilog += verilog_extractor(f.read()) + '\n'
            
    return verilog

def find_top_module_from_module_dict(module_dict) -> list:
    instant_dict = {module_name: 0 for module_name in module_dict}
    instanted_dict = {module_name: 0 for module_name in module_dict}
    for module_name in module_dict:
        state_list = module_dict[module_name].split(';')
        state_first_word_list = [state.strip().split(' ')[0] for state in state_list]
        for word in state_first_word_list:
            if word in module_dict:
                instant_dict[module_name] += 1
                instanted_dict[word] += 1
        
        state_list = module_dict[module_name].split('\n')
        state_first_word_list = [state.strip().split(' ')[0] for state in state_list]
        for word in state_first_word_list:
            if word in module_dict:
                instant_dict[module_name] += 1
                instanted_dict[word] += 1
    
    top_module_candidate = []
    for module_name in instant_dict:
        if not instant_dict[module_name] == 0 and instanted_dict[module_name] == 0:
            top_module_candidate.append(module_name)
            
    # if len(top_module_candidate) > 1:
        # print('Warning: Multiple top module candidates')
    if len(top_module_candidate) > 0:
        return top_module_candidate
    
    for module_name in instant_dict:
        if instanted_dict[module_name] == 0:
            top_module_candidate.append(module_name)
    return top_module_candidate

def find_top_module_and_clk_from_module_dict(module_dict):

    top_module_candidate = find_top_module_from_module_dict(module_dict)
    top_module_clk = []
    for top_module in top_module_candidate:
        clk = get_clk(module_dict[top_module])
        top_module_clk.append(clk)
        
    return top_module_candidate, top_module_clk

def find_top_module_from_verilog(text):
    return find_top_module_from_module_dict(module_dict_extractor(text))

def get_module_header(text):
    pattern = r'module\s+[^\(\s]+\s*(?:#\s*\(.*?\))?\s*\(.*?\)\s*;'
    verilog_code = re.findall(pattern, text, re.DOTALL)[0]
    return verilog_code
def get_module_name_from_header(header):
    pattern = r'module\s+([^\(\s]+)'
    module_name = re.findall(pattern, header, re.DOTALL)[0]
    return module_name

def get_header_var_list(header):
    pattern = r'[^#]\s*\((.*)\)'
    input_list = re.findall(pattern, header, re.DOTALL)[0]
    input_list = input_list.split(',')
    # input_list = [x.strip() for x in input_list]
    input_list = [x.strip() for x in input_list]
    var_list = []
    for var in input_list:
        if not ']' in var: var_list.append(var.split(' ')[-1])
        else: var_list.append(var.split(']')[-1].strip(' ').strip('\t'))
    return var_list

def get_clk(text):
    module_header = get_module_header(text)
    var_list = get_header_var_list(module_header)
    for var in var_list:
        if 'clk' in var.lower() or 'clock' in var.lower():
            return var.split(' ')[-1].strip('\t')

def search_files_recursively(base_dir, target_extension=None) -> list:
    file_paths = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if target_extension is None or file.endswith(target_extension):
                absolute_path = os.path.join(root, file)
                file_paths.append(absolute_path)
    return file_paths

def filter_out_tb_files(file_list: list) -> list:
    file_wo_tb = []
    for file in file_list:
        with open(file, 'r', encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if 'initial' in text: continue
        file_wo_tb.append(file)
        
    return file_wo_tb
        

def read_verilog_from_dir(dir_path, filter_out_tb=True):
    file_path = search_files_recursively(dir_path, '.v')
    if filter_out_tb:
        file_path = filter_out_tb_files(file_path)
        
class Verilog_Processor:
    def __init__(self, design_dir=None, filter_out_tb=True, log_file='Verilog_Processor.log'):
        self.design_dir = design_dir
        self.file_list = search_files_recursively(design_dir, '.v')
        if filter_out_tb:
            self.file_list = filter_out_tb_files(self.file_list)
        self.verilog_code = verilog_extractor_from_file_list(self.file_list)
        self.module_dict = module_dict_extractor(self.verilog_code)
        self.top_module_candidates, self.top_module_clk = find_top_module_and_clk_from_module_dict(self.module_dict)
        self.log(log_file)
        
    def log(self, log_path):
        self.log = open(log_path, 'a')
        content_dict = {'design_dir': self.design_dir, 'file_list': self.file_list, 'top_module_candidates': self.top_module_candidates, 'top_module_clk': self.top_module_clk}
        self.log.write(json.dumps(content_dict) + '\n')
        self.log.flush()
        self.log.close()
        
if __name__ == '__main__':
    verilog_obj = Verilog_Processor('all_filtered_design/riscv-src')
    print(verilog_obj.top_module_candidates, verilog_obj.top_module_clk)