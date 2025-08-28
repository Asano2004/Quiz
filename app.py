from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import pymysql
import json
import hashlib
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# データベース接続設定
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'quiz_user'),
        password=os.getenv('MYSQL_PASSWORD', 'quiz_password'),
        database=os.getenv('MYSQL_DATABASE', 'quiz_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        init_command="SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', 
                      (username, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('dashboard'))
        else:
            flash('ユーザー名またはパスワードが間違っています', 'error')
        
        conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', 
                          (username, password))
            flash('登録が完了しました', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError:
            flash('このユーザー名は既に使用されています', 'error')
        
        conn.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ユーザーの統計を取得
    cursor.execute('''
        SELECT COUNT(*) as total_answers,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
        FROM answers WHERE user_id = %s
    ''', (session['user_id'],))
    user_stats = cursor.fetchone()
    
    # 最近のクイズを取得
    cursor.execute('''
        SELECT q.id, q.question, q.category, q.difficulty 
        FROM quizzes q 
        ORDER BY q.created_at DESC 
        LIMIT 5
    ''')
    recent_quizzes = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         user_stats=user_stats, 
                         recent_quizzes=recent_quizzes)

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        question = request.form['question']
        choices = [
            request.form['choice1'],
            request.form['choice2'],
            request.form['choice3'],
            request.form['choice4']
        ]
        answer = int(request.form['answer'])
        category = request.form['category']
        difficulty = request.form['difficulty']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quizzes (user_id, question, choices, answer, category, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (session['user_id'], question, json.dumps(choices), answer, category, difficulty))
        
        conn.close()
        flash('クイズが作成されました', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_quiz.html')

@app.route('/take_quiz')
def take_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    category = request.args.get('category', 'all')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if category == 'all':
        cursor.execute('SELECT * FROM quizzes ORDER BY RAND() LIMIT 1')
    else:
        cursor.execute('SELECT * FROM quizzes WHERE category = %s ORDER BY RAND() LIMIT 1', 
                      (category,))
    
    quiz = cursor.fetchone()
    
    if not quiz:
        flash('利用可能なクイズがありません', 'error')
        return redirect(url_for('dashboard'))
    
    # 選択肢をJSONから解析
    quiz['choices'] = json.loads(quiz['choices'])
    
    # カテゴリ一覧を取得
    cursor.execute('SELECT DISTINCT category FROM quizzes')
    categories = [row['category'] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('take_quiz.html', quiz=quiz, categories=categories)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quiz_id = request.form['quiz_id']
    selected = int(request.form['selected'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # クイズの正解を取得
    cursor.execute('SELECT answer FROM quizzes WHERE id = %s', (quiz_id,))
    correct_answer = cursor.fetchone()['answer']
    
    is_correct = (selected == correct_answer)
    
    # 回答を記録
    cursor.execute('''
        INSERT INTO answers (user_id, quiz_id, selected, is_correct)
        VALUES (%s, %s, %s, %s)
    ''', (session['user_id'], quiz_id, selected, is_correct))
    
    conn.close()
    
    result = {
        'correct': is_correct,
        'correct_answer': correct_answer,
        'selected': selected
    }
    
    return render_template('quiz_result.html', result=result)

@app.route('/ranking')
def ranking():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ランキングを取得
    cursor.execute('''
        SELECT u.username, 
               COUNT(a.id) as total_answers,
               SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
               CASE 
                   WHEN COUNT(a.id) > 0 THEN 
                       ROUND(SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(a.id), 1)
                   ELSE 0 
               END as accuracy
        FROM users u
        LEFT JOIN answers a ON u.id = a.user_id
        GROUP BY u.id, u.username
        HAVING total_answers > 0
        ORDER BY accuracy DESC, total_answers DESC
        LIMIT 10
    ''')
    rankings = cursor.fetchall()
    
    conn.close()
    
    return render_template('ranking.html', rankings=rankings)

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('管理者権限が必要です', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 全クイズを取得
    cursor.execute('''
        SELECT q.*, u.username as creator
        FROM quizzes q
        JOIN users u ON q.user_id = u.id
        ORDER BY q.created_at DESC
    ''')
    quizzes = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin.html', quizzes=quizzes)

@app.route('/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('管理者権限が必要です', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 関連する回答も削除
    cursor.execute('DELETE FROM answers WHERE quiz_id = %s', (quiz_id,))
    cursor.execute('DELETE FROM quizzes WHERE id = %s', (quiz_id,))
    
    conn.close()
    
    flash('クイズが削除されました', 'success')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)