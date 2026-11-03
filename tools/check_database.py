"""Exercise all supplied datasets on a disposable MariaDB instance.

Creates only fresh databases with the chosen prefix. Never drops existing databases.
"""
import argparse,csv,datetime,json,subprocess
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--mysql',required=True);p.add_argument('--port',type=int,default=3306);p.add_argument('--output',required=True);p.add_argument('--prefix',default='up11qa_'+datetime.datetime.now().strftime('%H%M%S')+'_');p.add_argument('--demo-db')
A=p.parse_args()
if not A.prefix.startswith('up11qa_') or not A.prefix.replace('_','').isalnum():raise ValueError('Disposable prefix must start with up11qa_')
def sql(query,db=None,ok=True):
 args=[A.mysql,'-h','127.0.0.1','-P',str(A.port),'-u','root','--default-character-set=utf8mb4','--local-infile=1','-N','-B','--raw']+([db] if db else [])
 r=subprocess.run(args,input=query,encoding='utf-8',capture_output=True)
 if ok and r.returncode:raise RuntimeError(r.stderr)
 if not ok and not r.returncode:raise AssertionError('Expected database rejection')
 return r.stdout.strip(),r.stderr.strip()
def create(db,folder,mutate=''):
 if not db.replace('_','').isalnum():raise ValueError('Invalid database identifier')
 sql(f'CREATE DATABASE `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;')
 for name in ['01_schema.sql','02_staging.sql']:sql((ROOT/'project'/name).read_text(encoding='utf-8'),db)
 for source in sorted(folder.glob('*.csv')):
  with source.open(encoding='utf-8-sig',newline='') as f: cols=next(csv.reader(f))
  path=source.resolve().as_posix().replace("'","''")
  ending='\\r\\n' if b'\r\n' in source.read_bytes() else '\\n'
  sql(f"LOAD DATA LOCAL INFILE '{path}' INTO TABLE stg_{source.stem} CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' ESCAPED BY '\"' LINES TERMINATED BY '{ending}' IGNORE 1 LINES ({','.join(cols)});",db)
 if mutate:sql(mutate,db)
 return db
script=(ROOT/'project/03_import.sql').read_text(encoding='utf-8')
tables=['product','size','stock_item','customer','sales_order','order_line']
results={'server':sql('SELECT VERSION();')[0],'datasets':[],'checks':[]}
for folder in [ROOT/'data/demo',*sorted((ROOT/'data').glob('variant-*'))]:
 name=folder.name
 db=A.demo_db if name=='demo' and A.demo_db else A.prefix+name.replace('-','_')
 create(db,folder)
 sql(script,db)
 sql((ROOT/'project/04_queries.sql').read_text(encoding='utf-8'),db)
 expected=json.loads((folder/('expected.json' if name=='demo' else 'context.json')).read_text(encoding='utf-8'))
 counts=list(map(int,sql('SELECT '+','.join(f'(SELECT COUNT(*) FROM {t})' for t in tables)+';',db)[0].split('\t')))
 row=expected['rows']; ec=[row['products'],row['sizes'],row['stock'],row['users'],expected.get('orders',1),row['orders']]
 assert counts==ec,(name,counts,ec)
 hist=Decimal(sql('SELECT SUM(quantity*unit_price) FROM order_line;',db)[0])
 with (folder/'stock.csv').open(encoding='utf-8-sig',newline='') as f:source_stock=sum(int(r['available']) for r in csv.DictReader(f))
 assert int(sql('SELECT SUM(available) FROM stock_item;',db)[0])==source_stock
 assert hist==Decimal(str(expected.get('order_total',expected.get('historical_order_total'))))
 original=hist
 out,_=sql('START TRANSACTION; UPDATE product SET price=price+17 WHERE product_id=(SELECT product_id FROM stock_item WHERE item_id=(SELECT item_id FROM order_line LIMIT 1)); SELECT SUM(quantity*unit_price) FROM order_line; ROLLBACK;',db)
 assert Decimal(out)==hist
 for bad,errno in [('UPDATE stock_item SET available=-1 LIMIT 1',4025),('INSERT INTO stock_item(product_id,size_id,available) SELECT product_id,size_id,1 FROM stock_item LIMIT 1',1062),('INSERT INTO stock_item(product_id,size_id,available) VALUES(999999,1,1)',1452)]:
  _,err=sql(bad+';',db,ok=False);assert str(errno) in err,err
 _,err=sql('CALL import_checked();',db,ok=False);assert 'Target must be empty' in err
 result=dict(dataset=name,database=db,counts=dict(zip(tables,counts)),historical_total=str(hist),available_total=source_stock,history_price_preserved=True,constraints_rejected=True,reimport_rejected=True)
 results['datasets'].append(result)

invalid=[('link_quantity',"UPDATE stg_stock SET name='Несуществующая модель' WHERE source_row=2; UPDATE stg_orders SET quantity='0' WHERE source_row=2;",['stock_link','quantity_price']),('duplicate',"INSERT INTO stg_products(category,subcategory,image_path,name,manufacturer,description,composition,price) SELECT category,subcategory,image_path,name,manufacturer,description,composition,price FROM stg_products WHERE source_row=2;",['product_duplicate']),('date',"UPDATE stg_orders SET ordered_at='2026-02-31 00:00:00' WHERE source_row=2;",['order_date']),('missing_customer',"UPDATE stg_orders SET full_name='Нет такого клиента' WHERE source_row=2;",['order_customer']),('missing_file','TRUNCATE TABLE stg_sizes;',['missing_data']),('long_text',"UPDATE stg_products SET name=REPEAT('x',201) WHERE source_row=2;",['text_length'])]
for name,mutation,codes in invalid:
 db=create(A.prefix+name,ROOT/'data/variant-01',mutation)
 _,err=sql(script,db,ok=False);assert 'Import rejected' in err,err
 journal=sql('SELECT source_file,source_row,issue_code,reason FROM import_issue ORDER BY source_file,source_row,issue_code;',db)[0]
 for code in codes:assert code in journal,journal
 for table in tables:assert sql(f'SELECT COUNT(*) FROM {table};',db)[0]=='0'
 result=dict(case=name,database=db,target_empty=True,journal=journal)
 if name=='link_quantity':
  source=ROOT/'data/variant-01'
  with (source/'stock.csv').open(encoding='utf-8-sig',newline='') as f:stock=next(csv.DictReader(f))
  with (source/'orders.csv').open(encoding='utf-8-sig',newline='') as f:order=next(csv.DictReader(f))
  escaped=stock['name'].replace("'","''")
  sql(f"UPDATE stg_stock SET name='{escaped}' WHERE source_row=2; UPDATE stg_orders SET quantity='{order['quantity']}' WHERE source_row=2; CALL import_checked();",db)
  assert sql('SELECT COUNT(*) FROM order_line;',db)[0]=='1'
  result['recovery_passed']=True
 results['checks'].append(result)
db=create(A.prefix+'rollback',ROOT/'data/variant-01')
sql("CREATE TRIGGER fail_product BEFORE INSERT ON product FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Controlled target failure';",db)
_,err=sql(script,db,ok=False);assert 'Controlled target failure' in err
for table in ['category','subcategory','manufacturer','size','app_role',*tables]:
 assert sql(f'SELECT COUNT(*) FROM {table};',db)[0]=='0',table
results['checks'].append(dict(case='target_failure',database=db,all_target_tables_empty=True))
out=Path(A.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS:',len(results['datasets']),'datasets; history, constraints, repeat protection;',len(results['checks']),'rejection cases and recovery')
