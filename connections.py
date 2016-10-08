import MySQLdb


def connection():
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           db="giterest")
    c = conn.cursor()

    return c, conn