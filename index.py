from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3
import hashlib
import os
from werkzeug.utils import secure_filename #  отвечает за

app = Flask(__name__)
app.secret_key = 'password'

# Путь для сохранения изображений
path_to_save_images = os.path.join(app.root_path, 'static', 'imgs')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_conn():
       conn = sqlite3.connect('database.db')
       conn.row_factory = sqlite3.Row
       return conn


@app.route('/')
def home():
    conn = get_db_conn()
    blocks = conn.execute('SELECT * FROM content').fetchall()
    conn.close()

    blocks_list = [dict(ix) for ix in blocks]
    # print(blocks_list)

    json_data = {}
    
    for raw in blocks_list:
        if raw['idblock'] not in json_data:
            json_data[raw['idblock']] = []

        json_data[raw['idblock']].append({
            'id': raw['id'],
            'short_title': raw['short_title'],
            'img': raw['img'],
            'altimg': raw['altimg'],
            'title': raw['title'],
            'contenttext': raw['contenttext'],
            'author': raw['author'],
            'timestampdata': raw['timestampdata']
        })

    return render_template('index.html', json_data=json_data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            conn = get_db_conn()

            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            print(user)

            if user and user['password'] == hashed_password:
                session['user_id'] = user['id']
                print('YES')
                return redirect(url_for('admin'))
            else:
                error = 'Неправильное имя пользователя или пароль'
    return render_template('login.html', error = error)

@app.route('/logout')
def logout():
    # Удаление данных пользователя из сессии
    session.clear()
    # Перенаправление на главную страницу или страницу входа
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
        if 'user_id' not in session:
             return redirect(url_for('login'))
        
        conn = get_db_conn()
        blocks = conn.execute('SELECT * FROM content').fetchall()
        conn.close()

        blocks_list = [dict(ix) for ix in blocks]
        # print(blocks_list)

        json_data = {}
        
        for raw in blocks_list:
            if raw['idblock'] not in json_data:
                json_data[raw['idblock']] = []

            json_data[raw['idblock']].append({
                'id': raw['id'],
                'short_title': raw['short_title'],
                'img': raw['img'],
                'altimg': raw['altimg'],
                'title': raw['title'],
                'contenttext': raw['contenttext'],
                'author': raw['author'],
                'timestampdata': raw['timestampdata']
            })

        print(json_data)
        return render_template('admin.html', json_data = json_data)


@app.route('/update_content', methods=['POST'])
def update_content():
    if request.method == "POST":
        content_id = request.form['id']
        short_title = request.form['short_title']
        title = request.form['title']
        altimg = request.form.get('altimg')
        contenttext = request.form['contenttext']
    else:
        return redirect(url_for("admin.html")) 

    # Обработка загруженного файла
    file = request.files['img']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(path_to_save_images, filename)
        imgpath = "/static/imgs/"+filename
        file.save(save_path)
        # Обновите путь изображения в вашей базе данных

    # Обновление данных в базе
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if file:
        cursor.execute('UPDATE content SET short_title=?, img=?, altimg=?, title=?, contenttext=? WHERE id=?',
                   (short_title, imgpath, altimg, title, contenttext, content_id))
    else:
        cursor.execute('UPDATE content SET short_title=?, altimg=?, title=?, contenttext=? WHERE id=?',
                       (short_title, altimg, title, contenttext, content_id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
