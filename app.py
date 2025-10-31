from flask import Flask, request, render_template, redirect, url_for, flash
from flask_mysqldb import MySQL
import config
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# 비밀번호 해시 생성/검증 기능 초기화
bcrypt = Bcrypt(app)

# 로그인 기능 초기화
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 유저 객체
class User(UserMixin):
    def __init__(self, UserId, UserName, UserEmail):
        self.id=UserId
        self.name = UserName
        self.email = UserEmail

@login_manager.user_loader
def load_user(UserId):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=%s", (UserId,))
    UserData = cur.fetchone()
    cur.close()
    if UserData:
        return User(UserData['user_id'], UserData['user_name'], UserData['email'])
    return None

@app.route('/')
def main():
    cur = mysql.connection.cursor()
    cur.execute("SELECT post_id, name, post_title, created_at FROM posts ORDER BY created_at DESC")
    Posts = cur.fetchall()
    cur.close()
    return render_template('main.html', posts=Posts)

@app.route('/register', methods=['GET','POST'])
def register_user():
    if request.method == 'POST':
        UserName = request.form.get('user-name')
        Email = request.form.get('e-mail')
        Password = request.form.get('password')
        Password2 = request.form.get('password2')

        # 비밀번호 확인
        if Password != Password2:
            flash("비밀번호가 일치하지 않습니다.")
            return render_template('register.html')
        
        # 비밀번호 해싱
        HashedPassword = bcrypt.generate_password_hash(Password).decode('utf-8')

        # DB 저장
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (user_name, email, password_hash) VALUES (%s, %s, %s)",
                        (UserName, Email, HashedPassword))
            mysql.connection.commit()
        except:
            cur.close()
            flash("이미 존재하는 이메일입니다.")
            return render_template('register.html')
        cur.close()

        flash("회원가입 완료")

        return redirect(url_for('main'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        Email = request.form.get('e-mail')
        Password = request.form.get('password')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (Email,))
        UserData = cur.fetchone()
        cur.close()

        # DB에 UserData가 존재하고, 비밀번호가 맞으면
        if UserData and bcrypt.check_password_hash(UserData['password_hash'],Password):
            # User 객체 생성
            LoginUser = User(UserData['user_id'], UserData['user_name'], UserData['email'])
            # 로그인 세션 생성
            login_user(LoginUser)

            flash("로그인 성공")

            return redirect(url_for('main'))
        else:
            flash("이메일 또는 비밀번호가 올바르지 않습니다")
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    # 로그인 세션 종료
    logout_user()

    flash("로그아웃 완료")

    return redirect(url_for('main'))

@app.route('/write')
def write_post():
    # 게시글 작성 페이지 렌더링
    return render_template('write.html')

@app.route('/add', methods=['POST'])
@login_required
def add_post():
    # 브라우저에서 데이터 가져오기
    # 작성자 이름은 로그인 세션에서 가져옴
    UserName = current_user.name
    # 나머지는 write.html의 form에서 가져옴
    PostTitle = request.form.get('post-title')
    Content = request.form.get('content')
    
    # 유효성 검사
    if not PostTitle or not Content:
        flash("제목과 내용을 모두 입력해주세요")
        return render_template('write.html', post_title=PostTitle, content=Content)
    if len(PostTitle)>25:
        flash("제목은 25자 이하로 입력해주세요")
        return render_template('write.html', post_title=PostTitle, content=Content)
    if len(Content)>500:
        flash("내용은 500자 이하로 입력해주세요")
        return render_template('write.html', post_title=PostTitle, content=Content)

    # DB 저장
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO posts (user_id, name, post_title, content) VALUES (%s, %s, %s, %s)",
        (current_user.id, UserName, PostTitle, Content))
    mysql.connection.commit()
    cur.close()

    # Flash 메시지
    flash(f"{UserName}님의 게시글 작성 완료")

    return redirect(url_for('main'))

@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    # 삭제 후 리다이렉트할 URL
    RedirectTo = request.form.get('redirect-to', url_for('main'))

    # 삭제 할 게시글 정보 가져오기
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id FROM posts WHERE post_id = %s", (post_id,))
    Post = cur.fetchone()

    # 유효성 검사
    if not Post:
        cur.close()
        return "게시글이 존재하지 않습니다", 404
    if Post['user_id'] != current_user.id:
        cur.close()
        return "권한이 없습니다", 403
    
    # 삭제
    cur.execute("DELETE FROM posts WHERE post_id = %s", (post_id,))
    mysql.connection.commit()
    cur.close()

    flash("게시글이 삭제되었습니다")

    return redirect(RedirectTo)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM posts WHERE post_id = %s", (post_id,))
    Post = cur.fetchone()
    cur.close()

    if not Post:
        return "게시글을 찾을 수 없습니다", 404

    return render_template('post.html', post=Post)

@app.route('/my_posts')
@login_required
def my_posts():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT post_id, name, post_title, created_at FROM posts WHERE user_id = %s ORDER BY created_at DESC", 
        (current_user.id,)
                )
    Posts = cur.fetchall()
    cur.close()

    return render_template('my_posts.html', posts=Posts)

if __name__ == '__main__':
    app.run(debug=True)