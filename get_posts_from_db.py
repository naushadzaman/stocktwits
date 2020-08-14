import sqlite3

con = sqlite3.connect('stocktwits.db')

def sql_fetch(con):
    cursorObj = con.cursor()
    cursorObj.execute('SELECT * FROM post')
    rows = cursorObj.fetchall()
    for row in rows:
        print(row)

sql_fetch(con)