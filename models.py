import mysql.connector
from flask_login import UserMixin

def obter_conexao():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="db_mais_unidos"
    )   

class User(UserMixin):
    def __init__(self, id, name, email, telephone, password, created_at, itemDonationsTotal, valueDonationsTotal):
        self.id = id
        self.name = name
        self.email = email
        self.telephone = telephone
        self.password = password
        self.created_at = created_at.strftime('%d/%m/%Y') if created_at else "Data não disponível"

        # Exibir nas informações do perfil
        self.itemDonationsTotal = itemDonationsTotal
        self.valueDonationsTotal = valueDonationsTotal
        self.get_major_donation()
        self.get_valueDonationsTotal()
        self.get_totalContributions()
        self.get_engagedCampaigns()
        self.get_activeCampaigns()
        self.averagePerCampaign = self.valueDonationsTotal / self.engagedCampaigns if self.engagedCampaigns > 0 and self.valueDonationsTotal > 0 else 0



    @staticmethod
    def get(user_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_users WHERE usr_id = %s", (user_id,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return User(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
        return None

    @staticmethod
    def get_by_email(email):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_users WHERE usr_email = %s", (email,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return User(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
        return None
    
    def get_major_donation(self):        
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = "SELECT MAX(dnt_value) FROM tb_donations WHERE dnt_usr_id = %s"
        cursor.execute(sql, (self.id,))
        result = cursor.fetchone()
        conexao.close()
        self.majorDonation = result[0] if result and result[0] is not None else 0

    def get_valueDonationsTotal(self):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = "SELECT SUM(dnt_value) FROM tb_donations WHERE dnt_usr_id = %s"
        cursor.execute(sql, (self.id,))
        result = cursor.fetchone()
        conexao.close()
        self.valueDonationsTotal = result[0] if result and result[0] is not None else 0

    def get_totalContributions(self):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = "SELECT COUNT(*) FROM tb_donations WHERE dnt_usr_id = %s"
        cursor.execute(sql, (self.id,))
        result = cursor.fetchone()
        conexao.close()
        self.totalContributions = result[0] if result and result[0] is not None else 0

    def get_activeCampaigns(self):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        # Corrigir a consulta SQL
        sql = "SELECT COUNT(DISTINCT cam_id) FROM tb_campaigns WHERE cam_usr_id = %s and cam_status = 'ativa'"
        cursor.execute(sql, (self.id,))
        result = cursor.fetchone()
        conexao.close()
        self.activeCampaigns = result[0] if result and result[0] is not None else 0

    def get_engagedCampaigns(self):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        # Corrigir a consulta SQL
        sql = "SELECT COUNT(DISTINCT dnt_cam_id) FROM tb_donations WHERE dnt_usr_id = %s"
        cursor.execute(sql, (self.id,))
        result = cursor.fetchone()
        conexao.close()
        self.engagedCampaigns = result[0] if result and result[0] is not None else 0

    @staticmethod
    def create(name, email, telephone, password, itemDonationsTotal, valueDonationsTotal):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO tb_users (usr_name, usr_email, usr_telephone, usr_password, usr_itemDonationsTotal, usr_valueDonationsTotal) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, email, telephone, password, itemDonationsTotal, valueDonationsTotal)
        )
        conexao.commit()
        conexao.close()

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    

class Item:
    @staticmethod
    def get_by_campaign(campaign_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT itm_id, itm_name, itm_quantity, itm_reachedQuantity, itm_value FROM tb_items WHERE itm_cam_id = %s", (campaign_id,))
        results = cursor.fetchall()
        conexao.close()

        items = []
        for row in results:
            items.append({
                "id": row[0],
                "name": row[1],
                "quantity": row[2],
                "reached_quantity": row[3],
                "value": row[4]
            })
        return items


    @staticmethod
    def get(item_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT itm_id, itm_name, itm_quantity, itm_reachedQuantity, itm_value, itm_cam_id FROM tb_items WHERE itm_id = %s", (item_id,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "quantity": result[2],
                "reached_quantity": result[3],
                "value": result[4],
                "campaign_id": result[5]
            }
        return None
    
    @staticmethod
    def create(name, quantity, campaign_id, value=None):
        """Cria um novo item no banco de dados."""
        conexao = obter_conexao()
        cursor = conexao.cursor()
        # Ajuste os nomes de colunas conforme seu schema REAL:
        cursor.execute(
            """
            INSERT INTO tb_items (itm_name, itm_quantity, itm_cam_id, itm_value)
            VALUES (%s, %s, %s, %s)
            """,
            (name, quantity, campaign_id, value)
        )
        conexao.commit()
        new_id = cursor.lastrowid
        conexao.close()
        return new_id

    @staticmethod
    def update_quantity(item_id, new_quantity):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("UPDATE tb_items SET itm_reachedQuantity = %s WHERE itm_id = %s", (new_quantity, item_id))
        conexao.commit()
        conexao.close()

    @staticmethod
    def delete_by_campaign(campaign_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tb_items WHERE itm_cam_id = %s", (campaign_id,))
        conexao.commit()
        conexao.close()
class Campaign:
    def __init__(self, id, title, description, deadline, meta_value, reached_meta, tipo, status, created_at, deleted_at, usr_id):
        self.id = id
        self.title = title
        self.description = description
        self.deadline = deadline
        self.meta_value = meta_value
        self.reached_meta = reached_meta
        self.tipo = tipo
        self.status = status
        self.created_at = created_at
        self.deleted_at = deleted_at
        self.usr_id = usr_id

    @staticmethod
    def delete(campaign_id):
        conn = obter_conexao()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tb_items WHERE campaign_id = %s", (campaign_id,))

        cursor.execute("DELETE FROM tb_donations WHERE dnt_campaign_id = %s", (campaign_id,))

        cursor.execute("DELETE FROM tb_campaigns WHERE id = %s", (campaign_id,))

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get(campaign_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_campaigns WHERE cam_id = %s", (campaign_id,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return Campaign(*result)
        return None
    
    @staticmethod
    def search_by_title_or_description(user_id, query):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = "SELECT * FROM tb_campaigns WHERE cam_usr_id = %s AND (cam_title LIKE %s OR cam_description LIKE %s)"
        like_query = f"%{query}%"
        cursor.execute(sql, (user_id, like_query, like_query))
        results = cursor.fetchall()
        conexao.close()

        campaigns = []
        for row in results:
            # row deve ter 11 campos
            campaigns.append(Campaign(*row))

        return campaigns

    @staticmethod
    def create(title, description, deadline, meta_value, tipo, usr_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            """
            INSERT INTO tb_campaigns (cam_title, cam_description, cam_deadline, cam_meta, cam_tipo, cam_usr_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, description, deadline, meta_value, tipo, usr_id)
        )
        conexao.commit()
        campaign_id = cursor.lastrowid 
        conexao.close()
        return campaign_id

    @staticmethod
    def update(campaign_id, title=None, description=None, deadline=None, meta_value=None, reached_meta=None, tipo=None, status=None):
        conexao = obter_conexao()
        cursor = conexao.cursor()

        updates = []
        values = []
        if title:
            updates.append("cam_title = %s")
            values.append(title)
        if description:
            updates.append("cam_description = %s")
            values.append(description)
        if deadline:
            updates.append("cam_deadline = %s")
            values.append(deadline)
        if meta_value is not None:
            updates.append("cam_meta = %s")
            values.append(meta_value)
        if reached_meta is not None:
            updates.append("cam_reachedMeta = %s")
            values.append(reached_meta)
        if tipo:
            updates.append("cam_tipo = %s")
            values.append(tipo)
        if status:
            updates.append("cam_status = %s")
            values.append(status)

        if updates:
            query = f"UPDATE tb_campaigns SET {', '.join(updates)} WHERE cam_id = %s"
            values.append(campaign_id)
            cursor.execute(query, tuple(values))
            conexao.commit()
        conexao.close()

    @staticmethod
    def delete(campaign_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tb_campaigns WHERE cam_id = %s", (campaign_id,))
        conexao.commit()
        conexao.close()
    
    @staticmethod
    def get_by_user(user_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_campaigns WHERE cam_usr_id = %s", (user_id,))
        results = cursor.fetchall()
        conexao.close()

        return [
            Campaign(
                cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
            )
            for cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id in results
        ]

    @staticmethod
    def get_all():
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_campaigns")
        results = cursor.fetchall()
        conexao.close()

        return [
            Campaign(
                cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
            )
            for cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id in results
        ]
    
    @staticmethod
    def get_by_recents():
        conexao = obter_conexao()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT * FROM tb_campaigns ORDER BY cam_createdAt DESC")
        results = cursor.fetchall()
        conexao.close()

        return [
            Campaign(
                cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
            )
            for cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id in results
        ]
    
    @staticmethod
    def get_by_sucess():
        conexao = obter_conexao()
        cursor = conexao.cursor()
        
        cursor.execute("""
        SELECT cam_id, cam_title, cam_description, cam_deadline, cam_meta,
        cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
        FROM tb_campaigns
        WHERE cam_meta > 0
        ORDER BY (cam_reachedMeta / cam_meta * 100) DESC
        """)

        results = cursor.fetchall()
        conexao.close()

        return [
            Campaign(
                cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
            )
            for cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id in results
        ]
    
    @staticmethod
    def get_by_recents_from_user(user_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()

        cursor.execute("""
        SELECT cam_id, cam_title, cam_description, cam_deadline, cam_meta,
            cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
        FROM tb_campaigns
        WHERE cam_usr_id = %s
        ORDER BY cam_createdAt DESC
        """, (user_id,))

        results = cursor.fetchall()
        conexao.close()

        return [
            Campaign(
                cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
            )
            for cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id in results
        ]


    
    @staticmethod
    def get_by_success_from_user(user_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()

        cursor.execute("""
        SELECT cam_id, cam_title, cam_description, cam_deadline, cam_meta,
            cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
        FROM tb_campaigns
        WHERE cam_meta > 0 AND cam_usr_id = %s
        ORDER BY (cam_reachedMeta / cam_meta * 100) DESC
        """, (user_id,)) 

        results = cursor.fetchall()
        conexao.close()

        return [
            Campaign(
                cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id
            )
            for cam_id, cam_title, cam_description, cam_deadline, cam_meta,
                cam_reachedMeta, cam_tipo, cam_status, cam_createdAt, cam_deletedAt, cam_usr_id in results
        ]


        



    def is_active(self):
        return self.status == "ativa"

class Donation:
    def __init__(self, dnt_id, dnt_usr_id, dnt_cam_id, dnt_value, dnt_createdAt):
        self.id = dnt_id
        self.user_id = dnt_usr_id
        self.campaign_id = dnt_cam_id
        self.value = dnt_value        # Se != None => é doação financeira
        self.created_at = dnt_createdAt

    @staticmethod
    def create(user_id, campaign_id, donation_value=None):
        """Cria registro em 'tb_donations' para doações financeiras ou sem valor (caso itens)."""
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = """
            INSERT INTO tb_donations (dnt_usr_id, dnt_cam_id, dnt_value)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (user_id, campaign_id, donation_value))
        conexao.commit()
        new_id = cursor.lastrowid  # Precisaremos do ID gerado se formos adicionar items
        conexao.close()
        return new_id

    @staticmethod
    def get_by_user(user_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = """
            SELECT dnt_id, dnt_usr_id, dnt_cam_id, dnt_value, dnt_createdAt
            FROM tb_donations
            WHERE dnt_usr_id = %s
            ORDER BY dnt_createdAt DESC
        """
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        conexao.close()

        donations = []
        for row in rows:
            # row = (dnt_id, dnt_usr_id, dnt_cam_id, dnt_value, dnt_createdAt)
            donation = Donation(*row)
            donations.append(donation)
        return donations
    
    @staticmethod
    def get_top_donors(limit=10):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = """
            SELECT usr_id, usr_name, SUM(dnt_value) AS total_donated
            FROM tb_donations
            JOIN tb_users ON usr_id = dnt_usr_id
            GROUP BY usr_id
            HAVING total_donated > 0
            ORDER BY total_donated DESC
            LIMIT %s
        """
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        conexao.close()

        top_donors = []
        for row in rows:
            user_id, user_name, total_donated = row
            top_donors.append({
                'user_id': user_id,
                'user_name': user_name,
                'total_donated': total_donated
            })
        return top_donors

    @staticmethod
    def get_top_donors_items(limit=10):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = """
            SELECT usr_id, usr_name, SUM(dni_quantity) AS total_items_donated
            FROM tb_donation_items
            JOIN tb_donations ON dnt_id = dni_dnt_id
            JOIN tb_users ON usr_id = dnt_usr_id
            GROUP BY usr_id
            HAVING total_items_donated > 0
            ORDER BY total_items_donated DESC
            LIMIT %s
        """
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        conexao.close()

        top_donors = []
        for row in rows:
            user_id, user_name, total_items_donated = row
            top_donors.append({
                'user_id': user_id,
                'user_name': user_name,
                'total_items_donated': total_items_donated
            })
        return top_donors


class DonationItem:
    def __init__(self, dni_id, dni_dnt_id, dni_item_id, dni_quantity):
        self.id = dni_id
        self.donation_id = dni_dnt_id
        self.item_id = dni_item_id
        self.quantity = dni_quantity

    @staticmethod
    def create(donation_id, item_id, quantity):
        """Inserir relação doação-itens."""
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = """
            INSERT INTO tb_donation_items (dni_dnt_id, dni_item_id, dni_quantity)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (donation_id, item_id, quantity))
        conexao.commit()
        conexao.close()

    @staticmethod
    def get_by_donation(donation_id):
        """Retorna todos os itens doados para uma doação."""
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = """
            SELECT dni_id, dni_dnt_id, dni_item_id, dni_quantity
            FROM tb_donation_items
            WHERE dni_dnt_id = %s
        """
        cursor.execute(sql, (donation_id,))
        rows = cursor.fetchall()
        conexao.close()

        donation_items = []
        for row in rows:
            # row = (dni_id, dni_dnt_id, dni_item_id, dni_quantity)
            donation_items.append(DonationItem(*row))
        return donation_items