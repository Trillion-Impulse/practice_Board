from flask import Flask, request, render_template, redirect, url_for, flash
from flask_mysqldb import MySQL
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def main():
    cur = mysql.connection.cursor()
    cur.execute("SELECT post_id, name, post_title, created_at FROM posts ORDER BY created_at DESC")
    Posts = cur.fetchall()
    cur.close()
    return render_template('main.html', posts=Posts)

@app.route('/write')
def write_post():
    # 게시글 작성 페이지 렌더링
    return render_template('write.html')

@app.route('/add', methods=['POST'])
def add_post():
    # 브라우저에서 데이터 가져오기
    UserName = request.form.get('user-name')
    PostTitle = request.form.get('post-title')
    Content = request.form.get('content')
    
    # 유효성 검사
    if not UserName or not PostTitle or not Content:
        return "이름, 제목, 내용을 모두 입력해주세요",400
    if len(UserName)>12:
        return "이름은 12자 이하로 입력해주세요",400
    if len(PostTitle)>25:
        return "제목은 25자 이하로 입력해주세요",400
    if len(Content)>500:
        return "내용은 500자 이하로 입력해주세요",400

    # DB 저장
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO posts (name, post_title, content) VALUES (%s, %s, %s)",
        (UserName, PostTitle, Content))
    mysql.connection.commit()
    cur.close()

    # Flash 메시지
    flash(f"{UserName}님의 게시글 작성 완료")

    return redirect(url_for('main'))

@app.route('/post/<int:post_id>')
def view_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM posts WHERE post_id = %s", (post_id,))
    Post = cur.fetchone()
    cur.close()

    if not Post:
        return "게시글을 찾을 수 없습니다", 404

    return render_template('post.html', post=Post)

if __name__ == '__main__':
    app.run(debug=True)