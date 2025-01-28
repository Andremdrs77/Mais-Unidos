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
    def __init__(self, id, name, email, telephone, password, created_at):
        self.id = id
        self.name = name
        self.email = email
        self.telephone = telephone
        self.password = password
        self.created_at = created_at.strftime('%d/%m/%Y') if created_at else "Data não disponível"

    @staticmethod
    def get(user_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_users WHERE usr_id = %s", (user_id,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return User(result[0], result[1], result[2], result[3], result[4], result[5])
        return None

    @staticmethod
    def get_by_email(email):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_users WHERE usr_email = %s", (email,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return User(result[0], result[1], result[2], result[3], result[4], result[5])
        return None

    @staticmethod
    def create(name, email, telephone, password):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO tb_users (usr_name, usr_email, usr_telephone, usr_password) VALUES (%s, %s, %s, %s)",
            (name, email, telephone, password)
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
        campaign_id = cursor.lastrowid  # Obter o ID da campanha recém-criada
        conexao.close()
        return campaign_id

    @staticmethod
    def update(campaign_id, title=None, description=None, deadline=None, meta_value=None, reached_meta=None, tipo=None, status=None):
        conexao = obter_conexao()
        cursor = conexao.cursor()

        # Criar os valores de atualização dinamicamente
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



    def is_active(self):
        return self.status == "ativa"

class Donation:
    def __init__(self, dnt_id, dnt_usr_id, dnt_cam_id, dnt_value, dnt_createdAt):
        self.id = dnt_id
        self.user_id = dnt_usr_id
        self.campaign_id = dnt_cam_id
        self.value = dnt_value
        self.created_at = dnt_createdAt

    @staticmethod
    def create(user_id, campaign_id, value):
        """Insere uma nova doação (financeira) na tabela tb_donations."""
        conexao = obter_conexao()
        cursor = conexao.cursor()
        # Ajuste nomes de colunas conforme seu schema
        sql = """
            INSERT INTO tb_donations (dnt_usr_id, dnt_cam_id, dnt_value)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (user_id, campaign_id, value))
        conexao.commit()
        conexao.close()

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
        results = cursor.fetchall()
        conexao.close()

        donations = []
        for row in results:
            donation = Donation(*row)
            donations.append(donation)
        return donations

