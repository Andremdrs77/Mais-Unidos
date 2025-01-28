from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Item, Campaign, Donation, DonationItem, obter_conexao


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
    most_recent = Campaign.get_by_recents()

    most_successful = Campaign.get_by_sucess()

    top_donors = Donation.get_top_donors()

    query = request.args.get('q', '')  # 'q' é o nome do parâmetro
    if query:
        # Filtrar localmente (comparando título e descrição) para ambas as listas
        query_lower = query.lower()
        most_recent = [
            camp for camp in most_recent
            if query_lower in camp.title.lower() or query_lower in camp.description.lower()
        ]
        most_successful = [
            camp for camp in most_successful
            if query_lower in camp.title.lower() or query_lower in camp.description.lower()
        ]

    # 4. Função para montar a lista campaigns_data
    def prepare_campaigns_data(campaigns):
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
        return campaigns_data

    # 5. Preparar dados para as duas categorias
    most_recent_data = prepare_campaigns_data(most_recent)
    most_successful_data = prepare_campaigns_data(most_successful)

    # 6. Renderizar o template, passando ambas as listas e o termo de busca
    return render_template(
        'index.html',
        most_recent=most_recent_data,
        most_successful=most_successful_data,
        top_donors=top_donors,
        search_term=query
    )


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

@app.route('/doar_financeiro', methods=['POST'])
@login_required
def doar_financeiro():
    campaign_id = request.form.get('campaign_id')
    donation_value = request.form.get('donation_value')
    try:
        donation_value = float(donation_value)
    except:
        flash("Valor inválido.", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    # Cria registro em tb_donations
    donation_id = Donation.create(
        user_id=current_user.id,
        campaign_id=campaign_id,
        donation_value=donation_value
    )

    # Atualiza meta na campanha
    camp = Campaign.get(campaign_id)
    if camp:
        new_reached = camp.reached_meta + donation_value
        Campaign.update(campaign_id, reached_meta=new_reached)

    flash("Doação financeira registrada!", "success")
    return redirect(url_for('donations'))

@app.route('/doar_itens', methods=['POST'])
@login_required
def doar_itens():
    campaign_id = request.form.get('campaign_id')
    item_id = request.form.get('item_id')
    item_quantity = request.form.get('item_quantity')

    try:
        item_quantity = int(item_quantity)
    except:
        flash("Quantidade inválida", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    # 1. Criar doação (sem valor)
    donation_id = Donation.create(
        user_id=current_user.id,
        campaign_id=campaign_id,
        donation_value=None  # Indica que é itens
    )

    # 2. Criar pivot (doação-itens)
    DonationItem.create(donation_id, item_id, item_quantity)

    # 3. Atualizar contagem do item e a meta da campanha
    item = Item.get(item_id)
    if item:
        new_item_reached = item['reached_quantity'] + item_quantity
        if new_item_reached > item['quantity']:
            new_item_reached = item['quantity']
        Item.update_quantity(item_id, new_item_reached)

    camp = Campaign.get(campaign_id)
    if camp:
        # Se a campanha for "Itens e Financeiro", calcule o valor total 
        # do item doado (item['value'] * item_quantity) e some à meta
        if camp.tipo == "Itens e Financeiro":
            # Se o item tiver 'value' != None:
            item_val_unit = item['value'] or 0
            total_item_value = item_val_unit * item_quantity
            new_reached_meta = camp.reached_meta + total_item_value
            Campaign.update(campaign_id, reached_meta=new_reached_meta)
        else:
            # Campanha só de itens => soma item_quantity mesmo (se quiser)
            new_reached_meta = camp.reached_meta + item_quantity
            Campaign.update(campaign_id, reached_meta=new_reached_meta)

    flash("Doação de itens registrada!", "success")
    return redirect(url_for('donations'))

@app.route('/donations')
@login_required
def donations():
    user_id = current_user.id
    donations_list = Donation.get_by_user(user_id)

    # Filtro de busca (opcional)
    query = request.args.get('q', '')
    if query:
        # Se quiser filtrar localmente ...
        # Exemplo simples (pode adaptar)
        query_lower = query.lower()
        filtered = []
        for d in donations_list:
            # Montar string para comparar
            combined = f"{d.value or ''}"
            # se tiver DonationItem, busque e concatene também
            filtered.append(d)
        donations_list = filtered

    donations_data = []
    for d in donations_list:
        # Buscar nome da campanha
        camp = Campaign.get(d.campaign_id)
        campaign_name = camp.title if camp else "Campanha desconhecida"

        # Montar a string final "valor_quantidade"
        # 1) Verifica se doação tem valor (d.value)
        donation_value_str = ""
        if d.value is not None:
            donation_value_str = f"R$ {d.value:.2f}"

        # 2) Verifica se doação tem itens via DonationItem (pivô)
        donation_items = DonationItem.get_by_donation(d.id)  # lista de itemPivot
        items_str = ""
        if donation_items:
            partials = []
            for di in donation_items:
                # di.item_id e di.quantity
                item_info = Item.get(di.item_id)  # Ex.: {"name": "Arroz", ...}
                partials.append(f"{di.quantity} x {item_info['name']}")
            items_str = ", ".join(partials)

        # 3) Unificar em uma string final
        #    Se tiver valor e itens => "R$ 50,00 / 3 x Arroz"
        #    Se só valor => "R$ 50,00"
        #    Se só itens => "3 x Arroz"
        if donation_value_str and items_str:
            valor_quantidade = donation_value_str + " / " + items_str
        else:
            valor_quantidade = donation_value_str or items_str or ""

        # Formatar data
        date_str = d.created_at.strftime("%d/%m/%Y") if d.created_at else "N/A"

        donations_data.append({
            "id": d.id,
            "campaign_name": campaign_name,
            "donation_value": valor_quantidade,  # campo unificado
            "date": date_str
        })

    return render_template(
        'donations.html',
        donations=donations_data,
        search_term=query
    )

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
    donation_value = request.form.get('donation_value')  # se for dinheiro
    item_id = request.form.get('item_id')               # se for itens
    item_quantity = request.form.get('item_quantity')   # se for itens

    # 1. Verificar se a campanha existe
    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('index'))

    # GUARDA O ID DA DOAÇÃO PRINCIPAL (caso façamos 1 ou 2 doações)
    donation_id = None

    # 2. Lógica de doação financeira, se donation_value foi enviado
    if donation_value:
        try:
            val = float(donation_value)
        except ValueError:
            flash("Valor inválido!", "danger")
            return redirect(url_for('make_donations', campaign_id=campaign_id))

        # Cria registro principal em 'tb_donations' com dnt_value=val
        donation_id = Donation.create(
            user_id=current_user.id,
            campaign_id=campaign_id,
            donation_value=val
        )

        # Atualizar reached_meta
        new_reached = campaign.reached_meta + val
        Campaign.update(campaign_id, reached_meta=new_reached)
        flash("Doação financeira realizada com sucesso!", "success")

    # 3. Lógica de doação de itens, se item_id e item_quantity foram enviados
    if item_id and item_quantity:
        try:
            item_quantity = int(item_quantity)
        except ValueError:
            flash("Quantidade de item inválida!", "danger")
            return redirect(url_for('make_donations', campaign_id=campaign_id))

        if donation_id is None:
            donation_id = Donation.create(
                user_id=current_user.id,
                campaign_id=campaign_id,
                donation_value=None  # doação de itens
            )

        DonationItem.create(donation_id, item_id, item_quantity)

        # Atualizar contagem do item
        item_data = Item.get(item_id)
        if item_data:
            new_item_reached = item_data['reached_quantity'] + item_quantity
            if new_item_reached > item_data['quantity']:
                new_item_reached = item_data['quantity']
            Item.update_quantity(item_id, new_item_reached)

        # Se a campanha for "Itens e Financeiro", soma o valor do item no reached_meta
        if campaign.tipo == "Itens e Financeiro":
            item_val_unit = item_data['value'] or 0
            total_item_value = item_val_unit * item_quantity
            new_reached_meta = campaign.reached_meta + total_item_value + donation_value
            Campaign.update(campaign_id, reached_meta=new_reached_meta)
        else:
            # Se for só Itens, soma a quantidade no reached_meta (ou não, depende da sua lógica)
            new_reached_meta = campaign.reached_meta + item_quantity
            Campaign.update(campaign_id, reached_meta=new_reached_meta)

    # 4. Se usuário não enviou nem donation_value nem item_id, não doou nada
    if not donation_value and not item_id:
        flash("Nenhuma informação de doação fornecida!", "danger")
        return redirect(url_for('make_donations', campaign_id=campaign_id))

    return redirect(url_for('donations'))

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

