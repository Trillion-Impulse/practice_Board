from flask import Flask, request, render_template
from flask_mysqldb import MySQL
import config

app = Flask(__name__)

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/add', methods=['POST'])
def add_post():
    # 브라우저에서 데이터 가져오기
    UserName = request.form.get('user-name')
    Content = request.form.get('content')
    
    # 유효성 검사
    if not UserName or not Content:
        return "이름과 내용을 모두 입력해주세요",400
    if len(UserName)>12:
        return "이름은 12자 이하로 입력해주세요",400
    if len(Content)>500:
        return "내용은 500자 이하로 입력해주세요",400

    # DB 저장
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO posts (name, content) VALUES (%s, %s)",(UserName, Content))
    mysql.connection.commit()
    cur.close()
    return f"{UserName}의 게시물 포스팅 완료"

@app.route('/posts')
def select_posts():
    cur = mysql.connection.cursor()

    # 작성일 기준으로 내림차순 조회
    cur.execute("SELECT * FROM posts ORDER BY created_at DESC")

    rows = cur.fetchall()
    cur.close()
    return {'posts': rows}

if __name__ == '__main__':
    app.run(debug=True)