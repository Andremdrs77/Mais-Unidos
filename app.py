from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Item, Campaign, obter_conexao


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
        action = request.form.get('action')

        if action == 'login':
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
            name = request.form['r_name']
            email = request.form['r_email']
            telephone = request.form['r_telefone']
            password = request.form['r_password']
            confirm_password = request.form['r_confirmpassword']

            if password != confirm_password:
                flash('As senhas não coincidem!', 'danger')
                return redirect(url_for('login_and_register'))
            
            existing_user = User.get_by_email(email)
            if existing_user:
                flash('Esse email já está cadastrado!', 'danger')
                return redirect(url_for('login_and_register'))

            hashed_password = generate_password_hash(password)
            User.create(name=name, email=email, telephone=telephone, password=hashed_password)
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('index'))

    return render_template('login_register.html')


@app.route('/')
@login_required
def index():
    campaigns = Campaign.get_all()
    campaigns_data = []

    for campaign in campaigns:
        user = User.get(campaign.usr_id)
        user_name = user.name if user else "Usuário desconhecido"

        # Calcular o progresso
        progress = (campaign.reached_meta / campaign.meta_value * 100) if campaign.meta_value > 0 else 0

        # Atualizar status se a meta foi atingida
        if progress >= 100 and campaign.status != "Concluída":
            campaign.status = "Concluída"
            Campaign.update(campaign.id, status="Concluída")

        # Formatar progresso para a exibição
        visual_progress = min(progress, 100)  # Limita visualmente a barra a 100%

        # Formatar datas
        created_at = campaign.created_at.strftime('%d/%m/%Y %H:%M:%S') if campaign.created_at else "Data não disponível"
        deadline = campaign.deadline.strftime('%d/%m/%Y') if campaign.deadline else "Prazo não definido"

        # Formatar meta
        if campaign.tipo == "Financeiro":
            meta = f"R$ {campaign.meta_value:.2f}"
        elif campaign.tipo == "Itens":
            items_data = Item.get_by_campaign(campaign.id)
            meta = ", ".join([f"{item['quantity']} {item['name']}" for item in items_data])
        elif campaign.tipo == "Itens e Financeiro":
            items_data = Item.get_by_campaign(campaign.id)
            item_meta = ", ".join([f"{item['quantity']} {item['name']}" for item in items_data])
            meta = f"{item_meta} ou R$ {campaign.meta_value:.2f}"
        else:
            meta = "Meta não definida"

        # Adicionar os dados formatados na lista
        campaigns_data.append({
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "tipo": campaign.tipo,
            "status": campaign.status,
            "created_at": created_at,
            "user_name": user_name,
            "deadline": deadline,
            "meta": meta,
            "progress": progress,  # Porcentagem real
            "visual_progress": visual_progress  # Barra de progresso limitada a 100%
        })

    return render_template('index.html', campaigns=campaigns_data)




@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/campaign')
@login_required
def campaign():
    return render_template('campaign.html')


@app.route('/create-campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        print("Dados recebidos:", request.form.to_dict())

        title = request.form['title']
        description = request.form['description']
        deadline = request.form['deadline']
        goal_type = request.form['goalType']
        user_id = current_user.id

        if goal_type == 'financial':
            goal_type = 'Financeiro'
            meta_value = float(request.form['financialGoal'])
            Campaign.create(title, description, deadline, meta_value, goal_type, user_id)

        elif goal_type == 'items':
            goal_type = 'Itens'
            items = request.form.getlist('itemName[]')
            quantities = request.form.getlist('itemQuantity[]')
            meta_value = sum(int(quantity) for quantity in quantities)

            campaign_id = Campaign.create(title, description, deadline, meta_value, goal_type, user_id)

            for item_name, quantity in zip(items, quantities):
                Item.create(item_name, int(quantity), campaign_id)
                
        elif goal_type == 'items-financial':
            goal_type = 'Itens e Financeiro'
            items = request.form.getlist('itemName[]')
            quantities = request.form.getlist('itemQuantity[]')
            values = request.form.getlist('itemValue[]')
            meta_value = sum(float(quantity) * float(value) for quantity, value in zip(quantities, values))

            campaign_id = Campaign.create(title, description, deadline, meta_value, goal_type, user_id)

            for item_name, quantity, value in zip(items, quantities, values):
                Item.create(item_name, int(quantity), campaign_id, float(value))

        flash('Campanha criada com sucesso!', 'success')
        return redirect(url_for('campaign'))

    return render_template('create_campaign.html')


@app.route('/edit-campaign')
@login_required
def edit_campaign():
    return render_template('edit_campaign.html')


@app.route('/donations')
@login_required
def donations():
    return render_template('donations.html')


@app.route('/donations/<int:campaign_id>')
@login_required
def make_donations(campaign_id):
    campaign = Campaign.get(campaign_id)
    if not campaign:
        return "Campanha não encontrada", 404

    # Buscar os itens da campanha, se aplicável
    items = Item.get_by_campaign(campaign_id) if campaign.tipo in ["Itens", "Itens e Financeiro"] else []

    return render_template('make_donations.html', campaign=campaign, items=items)


@app.route('/process_donation', methods=['POST'])
@login_required
def process_donation():
    campaign_id = request.form.get('campaign_id')
    donation_value = request.form.get('donation_value')

    if not donation_value:  # Verifica se o valor foi fornecido
        flash("O valor da doação não pode ser vazio.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    try:
        donation_value = float(donation_value)
    except ValueError:
        flash("Por favor, insira um valor válido para a doação.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    # Adicione a lógica para registrar a doação
    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('index'))

    # Atualize os valores arrecadados na campanha
    Campaign.update(campaign_id, reached_meta=campaign.reached_meta + donation_value)

    flash("Doação realizada com sucesso!", "success")
    return redirect(url_for('index'))



@app.route('/process_item_donation', methods=['POST'])
@login_required
def process_item_donation():
    campaign_id = request.form.get('campaign_id')
    item_id = request.form.get('item_id')
    item_quantity = int(request.form.get('item_quantity'))

    # Validar os dados recebidos
    if not campaign_id or not item_id or not item_quantity:
        flash("Dados inválidos para doação de itens.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    # Verificar se o item pertence à campanha
    item = Item.get(item_id)
    if not item or int(item['campaign_id']) != int(campaign_id):
        flash("Item não encontrado ou não pertence à campanha.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    # Atualizar a quantidade arrecadada do item
    new_quantity = item['reached_quantity'] + item_quantity
    if new_quantity > item['quantity']:
        new_quantity = item['quantity']  # Não ultrapassar a meta do item

    Item.update_quantity(item_id, new_quantity)

    # Atualizar a quantidade total arrecadada na campanha (cam_reachedMeta)
    campaign = Campaign.get(campaign_id)
    if campaign:
        new_campaign_reached_meta = campaign.reached_meta + item_quantity
        Campaign.update(campaign_id, reached_meta=new_campaign_reached_meta)

    flash('Doação de itens realizada com sucesso!', 'success')
    return redirect(url_for('make_donations', campaign_id=campaign_id))



@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_and_register'))


@app.context_processor
def utility_processor():
    return dict(min=min)


if __name__ == '__main__':
    app.run(debug=True)

