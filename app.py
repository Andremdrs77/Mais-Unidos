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
    errors = {}
    active_form = None
    
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'login':
            active_form = 'login'
            
            email = request.form['l_email']
            senha = request.form['l_password']
            user = User.get_by_email(email)

            if not user:
                errors['l_email'] = 'E-mail não cadastrado!'
            elif not check_password_hash(user.password, senha):
                errors['l_password'] = 'Senha incorreta!'
            else:
                login_user(user)
                return redirect(url_for('index'))

        elif action == 'register':
            active_form = 'register'
            
            name = request.form['r_name']
            email = request.form['r_email']
            telephone = request.form['r_telefone']
            password = request.form['r_password']
            confirm_password = request.form['r_confirmpassword']

            if password != confirm_password:
                errors['r_confirmpassword'] = 'As senhas não coincidem!'
            else:
                existing_user = User.get_by_email(email)
                if existing_user:
                    errors['r_email'] = 'Este e-mail já está cadastrado!'
                else:
                    hashed_password = generate_password_hash(password)
                    User.create(
                        name=name, 
                        email=email, 
                        telephone=telephone, 
                        password=hashed_password,
                        itemDonationsTotal=0,
                        valueDonationsTotal=0
                    )
                    return redirect(url_for('index'))
        
        return render_template('login_register.html', errors=errors, active_form=active_form)
    
    return render_template('login_register.html', errors={}, active_form=None)

@app.route('/')
@login_required
def index():
    most_recent = Campaign.get_by_recents()
    most_successful = Campaign.get_by_sucess()
    top_donors = Donation.get_top_donors()
    top_item_donors = Donation.get_top_donors_items()

    query = request.args.get('q', '')
    if query:
        query_lower = query.lower()

        def matches_query(campaign):
            for attr in vars(campaign).values():
                if attr and query_lower in str(attr).lower():
                    return True
            return False

        most_recent = [camp for camp in most_recent if matches_query(camp)]
        most_successful = [camp for camp in most_successful if matches_query(camp)]

    def prepare_campaigns_data(campaigns):
        campaigns_data = []
        for campaign in campaigns:
            user = User.get(campaign.usr_id)
            user_name = user.name if user else "Usuário desconhecido"

            progress = (campaign.reached_meta / campaign.meta_value * 100) if campaign.meta_value > 0 else 0

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

    most_recent_data = prepare_campaigns_data(most_recent)
    most_successful_data = prepare_campaigns_data(most_successful)

    return render_template(
        'index.html',
        most_recent=most_recent_data,
        most_successful=most_successful_data,
        top_money_donors=top_donors,
        top_item_donors=top_item_donors,
        search_term=query
    )


@app.route('/delete-campaign/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('campaign'))

    if campaign.usr_id != current_user.id:
        flash("Você não tem permissão para excluir esta campanha.", "danger")
        return redirect(url_for('campaign'))

    Campaign.delete(campaign_id)

    flash("Campanha excluída com sucesso!", "success")
    return redirect(url_for('campaign'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/campaign', methods=['GET'])
@login_required
def campaign():
    user_id = current_user.id
    campaigns = Campaign.get_by_user(user_id)

    query = request.args.get('q', '')
    if query:
        query_lower = query.lower()

        def matches_query(campaign):
            for attr in vars(campaign).values():
                if attr and query_lower in str(attr).lower():
                    return True
            return False

        campaigns = [camp for camp in campaigns if matches_query(camp)]

    def prepare_campaigns_data(campaigns):
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
        return campaigns_data

    most_recent = Campaign.get_by_recents_from_user(user_id)
    most_successful = Campaign.get_by_success_from_user(user_id)

    if query:
        most_recent = [camp for camp in most_recent if matches_query(camp)]
        most_successful = [camp for camp in most_successful if matches_query(camp)]

    campaigns_data = prepare_campaigns_data(campaigns)
    most_recent_data = prepare_campaigns_data(most_recent)
    most_successful_data = prepare_campaigns_data(most_successful)

    return render_template(
        'campaign.html',
        campaigns=campaigns_data,
        most_recent=most_recent_data,
        most_successful=most_successful_data,
        search_term=query
    )

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
    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('campaign'))

    if campaign.usr_id != current_user.id:
        flash("Você não tem permissão para editar esta campanha.", "danger")
        return redirect(url_for('campaign'))

    if request.method == 'GET':
        items = []
        if campaign.tipo in ["Itens", "Itens e Financeiro"]:
            items = Item.get_by_campaign(campaign_id)

        return render_template('edit_campaign.html', campaign=campaign, items=items)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        deadline = request.form['deadline']
        goalType = request.form['goalType']

        meta_value = campaign.meta_value

        if goalType == 'financial':
            meta_value = float(request.form.get('financialGoal', 0.0))
            tipo = 'Financeiro'

        elif goalType == 'items':
            tipo = 'Itens'
            itemQuantities = request.form.getlist('itemQuantity[]')
            meta_value = sum(int(q) for q in itemQuantities) if itemQuantities else 0

        elif goalType == 'items-financial':
            tipo = 'Itens e Financeiro'
            itemQuantities = request.form.getlist('itemQuantity[]')
            itemValues = request.form.getlist('itemValue[]')
            meta_value = 0
            for q, v in zip(itemQuantities, itemValues):
                meta_value += float(q) * float(v)

        Campaign.update(
            campaign_id,
            title=title,
            description=description,
            deadline=deadline,
            meta_value=meta_value,
            tipo=tipo
        )

        if tipo in ['Itens', 'Itens e Financeiro']:
            Item.delete_by_campaign(campaign_id)

            itemNames = request.form.getlist('itemName[]')
            itemQuantities = request.form.getlist('itemQuantity[]')

            if tipo == 'Itens':
                for name, qty in zip(itemNames, itemQuantities):
                    Item.create(name, int(qty), campaign_id)
            else:
                itemValues = request.form.getlist('itemValue[]')
                for name, qty, val in zip(itemNames, itemQuantities, itemValues):
                    Item.create(name, int(qty), campaign_id, float(val))

        flash("Campanha atualizada com sucesso!", "success")
        return redirect(url_for('campaign'))

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

    donation_id = Donation.create(
        user_id=current_user.id,
        campaign_id=campaign_id,
        donation_value=donation_value
    )

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

    donation_id = Donation.create(
        user_id=current_user.id,
        campaign_id=campaign_id,
        donation_value=None
    )

    DonationItem.create(donation_id, item_id, item_quantity)

    item = Item.get(item_id)
    if item:
        new_item_reached = item['reached_quantity'] + item_quantity
        if new_item_reached > item['quantity']:
            new_item_reached = item['quantity']
        Item.update_quantity(item_id, new_item_reached)

    camp = Campaign.get(campaign_id)
    if camp:
        if camp.tipo == "Itens e Financeiro":
            item_val_unit = item['value'] or 0
            total_item_value = item_val_unit * item_quantity
            new_reached_meta = camp.reached_meta + total_item_value
            Campaign.update(campaign_id, reached_meta=new_reached_meta)
        else:
            new_reached_meta = camp.reached_meta + item_quantity
            Campaign.update(campaign_id, reached_meta=new_reached_meta)

    flash("Doação de itens registrada!", "success")
    return redirect(url_for('donations'))

@app.route('/donations')
@login_required
def donations():
    user_id = current_user.id
    donations_list = Donation.get_by_user(user_id)

    query = request.args.get('q', '')
    if query:
        query_lower = query.lower()
        filtered = []
        for d in donations_list:
            combined = f"{d.value or ''}"
            filtered.append(d)
        donations_list = filtered

    donations_data = []
    for d in donations_list:
        camp = Campaign.get(d.campaign_id)
        campaign_name = camp.title if camp else "Campanha desconhecida"

        donation_value_str = ""
        if d.value is not None:
            donation_value_str = f"R$ {d.value:.2f}"

        donation_items = DonationItem.get_by_donation(d.id)
        items_str = ""
        if donation_items:
            partials = []
            for di in donation_items:
                item_info = Item.get(di.item_id)
                partials.append(f"{di.quantity} x {item_info['name']}")
            items_str = ", ".join(partials)

        if donation_value_str and items_str:
            valor_quantidade = donation_value_str + " / " + items_str
        else:
            valor_quantidade = donation_value_str or items_str or ""

        date_str = d.created_at.strftime("%d/%m/%Y") if d.created_at else "N/A"

        donations_data.append({
            "id": d.id,
            "campaign_name": campaign_name,
            "donation_value": valor_quantidade,
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

    items = Item.get_by_campaign(campaign_id) if campaign.tipo in ["Itens", "Itens e Financeiro"] else []

    return render_template('make_donations.html', campaign=campaign, items=items)

@app.route('/process_donation', methods=['POST'])
@login_required
def process_donation():
    campaign_id = request.form.get('campaign_id')
    donation_value = request.form.get('donation_value')
    item_id = request.form.get('item_id')
    item_quantity = request.form.get('item_quantity')

    campaign = Campaign.get(campaign_id)
    if not campaign:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for('index'))

    donation_id = None

    if donation_value and donation_value.strip():
        try:
            val = float(donation_value)
        except ValueError:
            flash("Valor inválido!", "danger")
            return redirect(url_for('make_donations', campaign_id=campaign_id))

        donation_id = Donation.create(
            user_id=current_user.id,
            campaign_id=campaign_id,
            donation_value=val
        )

        new_reached = campaign.reached_meta + val
        Campaign.update(campaign_id, reached_meta=new_reached)
        flash("Doação financeira realizada com sucesso!", "success")

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
                donation_value=None
            )

        DonationItem.create(donation_id, item_id, item_quantity)

        item_data = Item.get(item_id)
        if item_data:
            new_item_reached = item_data['reached_quantity'] + item_quantity
            if new_item_reached > item_data['quantity']:
                new_item_reached = item_data['quantity']
            Item.update_quantity(item_id, new_item_reached)

        if campaign.tipo == "Itens e Financeiro":
            item_val_unit = item_data['value'] or 0
            total_item_value = item_val_unit * item_quantity
            donation_value_float = float(donation_value) if donation_value and donation_value.strip() else 0
            new_reached_meta = campaign.reached_meta + total_item_value + donation_value_float
            Campaign.update(campaign_id, reached_meta=new_reached_meta)
        else:
            new_reached_meta = campaign.reached_meta + item_quantity
            Campaign.update(campaign_id, reached_meta=new_reached_meta)

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

