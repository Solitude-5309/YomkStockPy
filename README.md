# YomkStockPy 简介

## version
v0.0.19  

## linux

### src运行
cd src  
export PYTHONPATH=$HOME/YomkServer/install/lib/python3.10/site-packages:$PYTHONPATH  
python3 save_stock_by_code.py  
python3 get_stock_list.py   
python3 update_exist_stock.py  
python3 get_stock_by_code.py  
python3 active_scan_by_code.py    

### test运行
cd test  
export PYTHONPATH=$HOME/YomkServer/install/lib/python3.10/site-packages:$PYTHONPATH  
python3 test_stock_data_service.py  
python3 test_data_base_service.py  
python3 test_activity_score_service.py  