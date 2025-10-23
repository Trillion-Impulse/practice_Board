from flask import Flask
from flask_mysqldb import MySQL
import config

app = Flask(__name__)

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/add')
def add_user():
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (name) VALUES ('홍길동')")
    mysql.connection.commit()
    cur.close()
    return "홍길동 추가 완료!"

@app.route('/users')
def select_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    cur.close()
    return {'users': rows}

if __name__ == '__main__':
    app.run(debug=True)