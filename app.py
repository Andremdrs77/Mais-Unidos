from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Item, Campaign, Donation, obter_conexao


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
    errors = {}         # Armazena erros específicos de cada campo
    active_form = None  # Indica qual form deve estar ativo (login ou register)
    
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'login':
            active_form = 'login'  # Indica que estamos tratando o login
            
            email = request.form['l_email']
            senha = request.form['l_password']
            user = User.get_by_email(email)

            # Verifica se o usuário existe
            if not user:
                # Mostra erro específico no campo de e-mail de login
                errors['l_email'] = 'E-mail não cadastrado!'
            # Se existe, verifica se a senha está correta
            elif not check_password_hash(user.password, senha):
                # Mostra erro específico no campo de senha de login
                errors['l_password'] = 'Senha incorreta!'
            else:
                # Login bem-sucedido: redireciona
                login_user(user)
                return redirect(url_for('index'))

        elif action == 'register':
            active_form = 'register'  # Indica que estamos tratando o registro
            
            name = request.form['r_name']
            email = request.form['r_email']
            telephone = request.form['r_telefone']
            password = request.form['r_password']
            confirm_password = request.form['r_confirmpassword']

            # Verifica se as senhas batem
            if password != confirm_password:
                errors['r_confirmpassword'] = 'As senhas não coincidem!'
            else:
                # Verifica se já existe um usuário com esse email
                existing_user = User.get_by_email(email)
                if existing_user:
                    errors['r_email'] = 'Este e-mail já está cadastrado!'
                else:
                    # Cria o usuário e redireciona
                    hashed_password = generate_password_hash(password)
                    User.create(
                        name=name, 
                        email=email, 
                        telephone=telephone, 
                        password=hashed_password,
                        itemDonations=0,
                        valueDonations=0,
                        engagedCampaigns=0
                    )
                    return redirect(url_for('index'))
        
        # Se chegamos até aqui, houve algum erro => renderiza o template mostrando os erros
        return render_template('login_register.html', errors=errors, active_form=active_form)
    
    # Se for GET, não exibe erro nenhum (errors vazio) e não força nenhum formulário ativo
    return render_template('login_register.html', errors={}, active_form=None)

@app.route('/')
@login_required
def index():
    # 1. Obter TODAS as campanhas
    campaigns = Campaign.get_all()

    # 2. Verificar se há parâmetro de busca na URL, ex.: ?q=algumaCoisa
    query = request.args.get('q', '')  # 'q' é o nome do parâmetro
    if query:
        # Filtrar localmente (comparando título e descrição)
        query_lower = query.lower()
        filtered = []
        for camp in campaigns:
            if (query_lower in camp.title.lower()) or (query_lower in camp.description.lower()):
                filtered.append(camp)
        campaigns = filtered

    # 3. Montar a lista campaigns_data (igual ao seu código atual)
    campaigns_data = []
    for campaign in campaigns:
        user = User.get(campaign.usr_id)
        user_name = user.name if user else "Usuário desconhecido"

        progress = (campaign.reached_meta / campaign.meta_value * 100) if campaign.meta_value > 0 else 0

        # Se a meta foi atingida, atualizar status
        if progress >= 100 and campaign.status != "Concluída":
            campaign.status = "Concluída"
            Campaign.update(campaign.id, status="Concluída")

        visual_progress = min(progress, 100)
        created_at = campaign.created_at.strftime('%d/%m/%Y %H:%M:%S') if campaign.created_at else "Data não disponível"
        deadline = campaign.deadline.strftime('%d/%m/%Y') if campaign.deadline else "Prazo não definido"

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
            "progress": progress,
            "visual_progress": visual_progress
        })

    # 4. Renderizar o template, passando também o "query" para manter no input
    return render_template('index.html', campaigns=campaigns_data, search_term=query)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/campaign', methods=['GET'])
@login_required
def campaign():
    user_id = current_user.id
    # Buscar somente as campanhas do usuário logado
    campaigns = Campaign.get_by_user(user_id)

    # --- PARÂMETRO DE BUSCA ---
    # Se na query string vier algo como ?q=algumTexto
    query = request.args.get('q', '')  # q é o nome do campo de busca
    if query:
        # Exemplo simples com LIKE
        campaigns = Campaign.search_by_title_or_description(user_id, query)
    else:
        campaigns = Campaign.get_by_user(user_id)

    # Montar a lista campaigns_data (igual ao index)
    campaigns_data = []
    for campaign_obj in campaigns:
        progress = (campaign_obj.reached_meta / campaign_obj.meta_value * 100) if campaign_obj.meta_value > 0 else 0

        if progress >= 100 and campaign_obj.status != "Concluída":
            campaign_obj.status = "Concluída"
            Campaign.update(campaign_obj.id, status="Concluída")

        created_at = campaign_obj.created_at.strftime('%d/%m/%Y %H:%M:%S') if campaign_obj.created_at else "Data não disponível"
        deadline = campaign_obj.deadline.strftime('%d/%m/%Y') if campaign_obj.deadline else "Prazo não definido"

        if campaign_obj.tipo == "Financeiro":
            meta = f"R$ {campaign_obj.meta_value:.2f}"
        elif campaign_obj.tipo == "Itens":
            items_data = Item.get_by_campaign(campaign_obj.id)
            meta = ", ".join([f"{item['quantity']} {item['name']}" for item in items_data])
        elif campaign_obj.tipo == "Itens e Financeiro":
            items_data = Item.get_by_campaign(campaign_obj.id)
            item_meta = ", ".join([f"{item['quantity']} {item['name']}" for item in items_data])
            meta = f"{item_meta} ou R$ {campaign_obj.meta_value:.2f}"
        else:
            meta = "Meta não definida"

        visual_progress = min(progress, 100)

        campaigns_data.append({
            "id": campaign_obj.id,
            "title": campaign_obj.title,
            "description": campaign_obj.description,
            "tipo": campaign_obj.tipo,
            "status": campaign_obj.status,
            "created_at": created_at,
            "deadline": deadline,
            "meta": meta,
            "progress": progress,
            "visual_progress": visual_progress
        })

    # Renderiza o template e passa "search_term=query" para exibir o valor no input
    return render_template('campaign.html', campaigns=campaigns_data, search_term=query)

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


@app.route('/edit-campaign/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    # 1. Buscar a campanha no banco
    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('campaign'))

    # (Opcional) Verifica se o usuário atual é dono da campanha
    if campaign.usr_id != current_user.id:
        flash("Você não tem permissão para editar esta campanha.", "danger")
        return redirect(url_for('campaign'))

    # 2. Se for GET, apenas preenche o formulário com os dados existentes
    if request.method == 'GET':
        # Se a campanha for do tipo "Itens" ou "Itens e Financeiro", buscamos seus itens
        items = []
        if campaign.tipo in ["Itens", "Itens e Financeiro"]:
            items = Item.get_by_campaign(campaign_id)  # Retorna lista de dicionários ou objetos

        return render_template('edit_campaign.html', campaign=campaign, items=items)

    # 3. Se for POST, processamos as alterações
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        deadline = request.form['deadline']
        goalType = request.form['goalType']

        # Atualiza parte principal da campanha
        # Precisamos de meta_value. Se for financeiro, vem de 'financialGoal'; se for itens, soma dos itens, etc.
        meta_value = campaign.meta_value  # Valor original, se quiser

        # Vamos redefinir a meta de acordo com o type
        if goalType == 'financial':
            meta_value = float(request.form.get('financialGoal', 0.0))
            tipo = 'Financeiro'

        elif goalType == 'items':
            tipo = 'Itens'
            # Soma das quantidades (ou zero) — depende da sua lógica
            itemQuantities = request.form.getlist('itemQuantity[]')
            meta_value = sum(int(q) for q in itemQuantities) if itemQuantities else 0

        elif goalType == 'items-financial':
            tipo = 'Itens e Financeiro'
            itemQuantities = request.form.getlist('itemQuantity[]')
            itemValues = request.form.getlist('itemValue[]')
            meta_value = 0
            # Por exemplo: soma (quantidade * valor unitário)
            for q, v in zip(itemQuantities, itemValues):
                meta_value += float(q) * float(v)

        # 4. Atualizar a tabela tb_campaigns
        Campaign.update(
            campaign_id,
            title=title,
            description=description,
            deadline=deadline,
            meta_value=meta_value,
            tipo=tipo
        )

        # 5. Atualizar itens (se for "Itens" ou "Itens e Financeiro")
        # Estratégia simples: deleta os antigos e recria
        if tipo in ['Itens', 'Itens e Financeiro']:
            # Apaga todos os itens antigos
            Item.delete_by_campaign(campaign_id)

            itemNames = request.form.getlist('itemName[]')
            itemQuantities = request.form.getlist('itemQuantity[]')

            if tipo == 'Itens':
                # Simples: sem valor unitário
                for name, qty in zip(itemNames, itemQuantities):
                    Item.create(name, int(qty), campaign_id)
            else:
                # Tipo = 'Itens e Financeiro': tem itemValue[]
                itemValues = request.form.getlist('itemValue[]')
                for name, qty, val in zip(itemNames, itemQuantities, itemValues):
                    Item.create(name, int(qty), campaign_id, float(val))

        flash("Campanha atualizada com sucesso!", "success")
        return redirect(url_for('campaign'))  # Ou para 'my_campaigns', etc.

@app.route('/donations', methods=['GET'])
@login_required
def donations():
    user_id = current_user.id
    donations_list = Donation.get_by_user(user_id)

    # Filtrar via query string (busca)
    query = request.args.get('q', '')
    if query:
        query_lower = query.lower()
        filtered = []
        for d in donations_list:
            # Combine campos que podem ser pesquisados (ex.: campanha, type, item_name)
            # Precisaremos talvez buscar o nome da campanha via Campaign.get(...) ou já trazer no SELECT
            # mas para simplicidade, assumimos que item_name, etc. resolvem
            combined = f" {d.item_name} {d.value}".lower()
            # Se contiver o termo, filtramos
            if query_lower in combined:
                filtered.append(d)
        donations_list = filtered

    # Converter cada Donation em dicionário para o template
    donations_data = []
    for d in donations_list:
        # (Opcional) buscar nome da campanha
        campaign = Campaign.get(d.campaign_id)
        campaign_name = campaign.title if campaign else "Campanha desconhecida"

        # Formatar valor ou quantidade
        if campaign.tipo == 'Financeiro':
            valor_quantidade = f"R$ {d.value:.2f}"
        else:
            # Se doação de itens
            valor_quantidade = f"{d.item_quantity} x {d.item_name}"

        # Formatar data
        donation_date_str = d.created_at.strftime('%d/%m/%Y') if d.created_at else "Data não disponível"

        donations_data.append({
            "id": d.id,
            "campaign_name": campaign_name,
            "valor_quantidade": valor_quantidade,
            "date": donation_date_str
        })

    return render_template('donations.html', donations=donations_data, search_term=query)



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

    if not donation_value:
        flash("O valor da doação não pode ser vazio.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    try:
        donation_value = float(donation_value)
    except ValueError:
        flash("Por favor, insira um valor válido para a doação.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    # 1. Obter a campanha
    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('index'))

    # 2. Registrar no tb_donations (o user_id é current_user.id)
    Donation.create(current_user.id, campaign_id, float(donation_value))

    # 3. Atualizar reached_meta da campanha
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

