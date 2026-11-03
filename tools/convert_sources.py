"""Reproduce the demonstration XLSX to CSV transformation, or verify it."""
import argparse,csv,datetime,json
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
P=argparse.ArgumentParser();P.add_argument('--output',type=Path);A=P.parse_args()
FILES={'Products_import.xlsx':('products.csv','category,subcategory,image_path,name,manufacturer,description,composition,price'),'Sizes_import.xlsx':('sizes.csv','label'),'Stock_Items_import.xlsx':('stock.csv','name,manufacturer,size,available'),'Users_import.xlsx':('users.csv','last_name,first_name,patronymic,login,role'),'Orders_import.xlsx':('orders.csv','order_id,ordered_at,full_name,category,name,manufacturer,size,quantity,unit_price')}
changes=[]
def convert(v,f,row,col):
 if isinstance(v,datetime.datetime):return v.strftime('%Y-%m-%d %H:%M:%S')
 if v is None:return ''
 s=str(v)
 if s!=s.strip():changes.append(dict(file=f,row=row,column=col,change='Удалены внешние пробелы или переносы',before=s,after=s.strip()))
 return s.strip()
for name,(csvname,headers) in FILES.items():
 sheet=openpyxl.load_workbook(ROOT/'data/original'/name,data_only=True,read_only=True).active
 rows=[headers.split(',')]+[[convert(v,name,i,j) for j,v in enumerate(row,1)] for i,row in enumerate(list(sheet.values)[1:],2)]
 if A.output:
  A.output.mkdir(parents=True,exist_ok=True)
  with (A.output/csvname).open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(rows)
 else:
  with (ROOT/'data/demo'/csvname).open(encoding='utf-8-sig',newline='') as f:actual=list(csv.reader(f))
  assert rows==actual,(name,'CSV differs from declared transformations')
print(json.dumps(dict(files=5,whitespace_changes=changes,check='PASS'),ensure_ascii=False,indent=2))
