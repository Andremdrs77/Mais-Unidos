from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, obter_conexao
import smtplib
import email.message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPERSECRETO'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/loginandregister', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = User.get_by_email(email)

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Email ou senha incorretos', 'danger')
    
    return render_template('login_register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        idade = request.form['idade']

        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tb_usuarios WHERE usr_email = %s", (email,))
        existing_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if existing_user:
            flash('Esse email já está cadastrado!', 'error')
            return redirect(url_for('register'))

        senha_hashed = generate_password_hash(senha)
        
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tb_usuarios (usr_email, usr_senha, usr_nome, usr_idade) VALUES (%s, %s, %s, %s)",
                       (email, senha_hashed, nome, idade))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Usuário registrado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/campaign')
def campaign():
    return render_template('campaign.html')


@app.route('/donations')
def donations():
    return render_template('donations.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)