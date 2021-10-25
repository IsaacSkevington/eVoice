import mysql.connector
import pyodbc


#Change the details of the databases here:
#ADDR is the server address
#PORT is the port (not required for MSSQL)
#UN is the username
#PW is the password
#DB is the database - make sure this is created in the new location before execution

MYSQLADDR = "evoice.cermmtd1vgvf.eu-west-2.rds.amazonaws.com"
MYSQLPORT = 3306
MYSQLUN = "eVoice"
MYSQLPW = "latymerevoice"
MYSQLDB = "evoice"

MSSQLADDR = "evoicemicrosoft.cermmtd1vgvf.eu-west-2.rds.amazonaws.com"
MSSQLPORT = None
MSSQLUN = "eVoice"
MSSQLPW = "latymerevoice"
MSSQLDB = "evoice"


keys = []

columnTypes = {}

class Key:
    def __init__(self, ktype, tableName, colName, refTable, refColumn):
        self.type = self.getType(ktype)
        self.columnName = colName
        self.ref = str(refTable) + "(" + str(refColumn) + ")"
        self.table = tableName

    def getType(self, name):
        if name == "PRIMARY":
            return "p"
        else:
            return "f"


def isDate(string):
    string = str(string)
    if string is None:
        return False
    if len(string) != 10:
        return False
    if string[4] != "-" or string[7] != "-":
        return False
    try:
        int(string[:3])
        int(string[5:7])
        int(string[8:10])
    except:
        return False
    return True

def connectMicrosoftSQLDatabase():
    db = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + MSSQLADDR + ';DATABASE=' + MSSQLDB + ';UID=' + MSSQLUN + ';PWD=' + MSSQLPW)
    cursor = db.cursor()
    sql = "USE " + MSSQLDB
    cursor.execute(sql)
    return db, cursor



def connectMySQLDatabase():
    lines = ["" for i in range(6)]
    lines[0]=MYSQLADDR
    lines[1]=MYSQLPORT
    lines[2]=MYSQLUN
    lines[3]=MYSQLPW
    lines[4]=MYSQLDB
    db = mysql.connector.connect(
        host=lines[0],
        port = int(lines[1]),
        username=lines[2],
        password=lines[3]
    )
    cursor = db.cursor()
    sql = "USE " + lines[4]
    cursor.execute(sql)
    return db, cursor

def getTables():
    sql = "SHOW tables"
    mysqlcsr.execute(sql)
    return [i[0] for i in mysqlcsr.fetchall()]


def createTable(tableName):
    sql = ("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH "
          "FROM INFORMATION_SCHEMA.COLUMNS "
          "WHERE TABLE_NAME = '" + tableName + "'")
    mysqlcsr.execute(sql)
    tableData = mysqlcsr.fetchall()
    ct = {i:tableData[i][1] for i in range(len(tableData))}
    columnTypes[tableName] = ct
    sql = ("SELECT COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, TABLE_NAME "
        "FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
        "WHERE TABLE_NAME = '" + tableName + "'")
    mysqlcsr.execute(sql)
    keyData = mysqlcsr.fetchall()
    pKeys = []
    for key in keyData:
        k = Key(key[1], key[4], key[0], key[2], key[3])
        if k.type == "p":
            pKeys.append(k.columnName)
        keys.append(k)
    typesString = ""
    for data in tableData:
        addStr = ""
        if data[0] in pKeys:
            addStr = "NOT NULL"
        if data[2] is not None:
            typesString += data[0] + " " + data[1] + "(" + str(data[2]) + ") " + addStr + ", "
        else:
            typesString += data[0] + " " + data[1] + " " + addStr + ", "
    typesString = typesString[:-2]

    sql = "CREATE TABLE " + tableName + "(" + typesString + ")"
    mssqlcsr.execute(sql)
    mssqldb.commit()
    

def addKeys():
    pKeys = {}
    for k in keys:
        if k.type == "p":
            if k.table in pKeys.keys():
                pKeys[k.table].append(k.columnName)
            else:
                pKeys[k.table] = [k.columnName]
    for table in pKeys.keys():
        cols = ", ".join(pKeys[table])
        sql = "ALTER TABLE " + table + " ADD PRIMARY KEY (" + cols + ")"
        mssqlcsr.execute(sql)
        mssqldb.commit()
    for k in keys:
        if k.type == "f":
            sql = "ALTER TABLE " + k.table + " ADD FOREIGN KEY (" + k.columnName + ") REFERENCES " + k.ref
            mssqlcsr.execute(sql)
            mssqldb.commit()




def migrateTableData(tableName):
    sql = "SELECT * FROM " + tableName
    mysqlcsr.execute(sql)
    fullData = mysqlcsr.fetchall()
    insString = "INSERT INTO " + tableName + " VALUES "
    for data in fullData:
        insString += "("
        for i in range(len(data)):
            val = data[i]
            if val is None:
                val = "NULL"
            val = str(val)
            if columnTypes[tableName][i].lower() == "varchar" or columnTypes[tableName][i].lower() == "date":
                val = val.replace("'", "''")
                insString += "'" + val + "',"
            elif columnTypes[tableName][i].lower() == "int":
                insString += val + ","
            else:
                val = val.replace("'", "''")
                insString += "'" + val + "',"
                
        insString = insString[:-1] + "), "
    insString = insString[:-2]
    mssqlcsr.execute(insString)
    mssqldb.commit()
            
        

    

def main():
    count = 0
    for table in tables:
        print("Creating table " + table)
        createTable(table)

    for table in tables:
        print("Populating table " + table)
        migrateTableData(table)
    print("Setting keys")
    addKeys()


mysqldb, mysqlcsr = connectMySQLDatabase()
mssqldb, mssqlcsr = connectMicrosoftSQLDatabase()
tables = getTables()
main()