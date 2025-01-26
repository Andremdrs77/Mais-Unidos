from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, obter_conexao

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPERSECRETO'

login_manager = LoginManager()
login_manager.login_view = 'login_and_register'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/loginandregister', methods=['GET', 'POST'])
def login_and_register():
    if request.method == 'POST':
        # Identificar se é login ou registro
        action = request.form.get('action')

        if action == 'login':
            # Processar o login
            email = request.form['l_email']
            senha = request.form['l_password']
            user = User.get_by_email(email)

            if user and check_password_hash(user.password, senha):
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Email ou senha incorretos', 'danger')
        
        elif action == 'register':
            # Processar o registro
            name = request.form['r_name']
            email = request.form['r_email']
            telephone = request.form['r_telefone']
            password = request.form['r_password']
            confirm_password = request.form['r_confirmpassword']

            # Validar campos
            if password != confirm_password:
                flash('As senhas não coincidem!', 'danger')
                return redirect(url_for('login_and_register'))
            
            # Verificar se o email já está registrado
            existing_user = User.get_by_email(email)
            if existing_user:
                flash('Esse email já está cadastrado!', 'danger')
                return redirect(url_for('login_and_register'))

            # Criar usuário
            hashed_password = generate_password_hash(password)
            User.create(name=name, email=email, telephone=telephone, password=hashed_password)
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('index'))

    return render_template('login_register.html')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/campaign')
@login_required
def campaign():
    return render_template('campaign.html')

@app.route('/create-campaign')
@login_required
def create_campaign():
    return render_template('create_campaign.html')

@app.route('/donations')
@login_required
def donations():
    return render_template('donations.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_and_register'))


if __name__ == '__main__':
    app.run(debug=True)

