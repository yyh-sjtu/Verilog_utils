<div style="text-align: center;">
    <h1>Verilog_utils</h1>
</div>

<div style="text-align: right;">
    <div style="display: inline-block; text-align: left;">
        <span>Author: Yunhao Zhou</span></br>
        <span>Date: 2024-11-08</span>
    </div>
</div>

## 1. Usage
```python
import Verilog_utils
verilog_obj = Verilog_utils.Verilog_Processor('<Verilog Design Dir>')
```

## 2. Introduction
```python
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
```