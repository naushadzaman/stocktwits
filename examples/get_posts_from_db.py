import json 
import sqlite3

con = sqlite3.connect('stocktwits.db')

def sql_fetch(con):
    cursorObj = con.cursor()
    cursorObj.execute('SELECT * FROM post')
    rows = cursorObj.fetchall()
    for i,row in enumerate(rows):
        # print(json.dumps(json.loads(row[2]), indent=3))
        _json = json.loads(row[2])
        print(_json["created_at"], _json["body"], _json["entities"]["sentiment"])
        # if i > 0: break 
    print("total", i)
sql_fetch(con)