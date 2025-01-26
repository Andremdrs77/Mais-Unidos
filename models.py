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
        self.created_at = created_at

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


class Campaign:
    def __init__(self, id, title, description, deadline, meta_value, current_value, tipo, created_at, deleted_at, usr_id):
        self.id = id
        self.title = title
        self.description = description
        self.deadline = deadline
        self.meta_value = meta_value
        self.current_value = current_value
        self.tipo = tipo
        self.created_at = created_at
        self.deleted_at = deleted_at
        self.usr_id = usr_id

    @staticmethod
    def get(campaign_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_campanhas WHERE cam_id = %s", (campaign_id,))
        result = cursor.fetchone()
        conexao.close()
        if result:
            return Campaign(*result)
        return None

    @staticmethod
    def create(title, description, deadline, meta_value, tipo, usr_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            """
            INSERT INTO tb_campanhas (cam_title, cam_description, cam_deadline, cam_metaValue, cam_tipo, cam_usr_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, description, deadline, meta_value, tipo, usr_id)
        )
        conexao.commit()
        conexao.close()

    @staticmethod
    def update(campaign_id, title=None, description=None, deadline=None, meta_value=None, current_value=None, tipo=None):
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
        if meta_value:
            updates.append("cam_metaValue = %s")
            values.append(meta_value)
        if current_value is not None:
            updates.append("cam_currentValue = %s")
            values.append(current_value)
        if tipo:
            updates.append("cam_tipo = %s")
            values.append(tipo)

        if updates:
            query = f"UPDATE tb_campanhas SET {', '.join(updates)} WHERE cam_id = %s"
            values.append(campaign_id)
            cursor.execute(query, tuple(values))
            conexao.commit()
        conexao.close()

    @staticmethod
    def delete(campaign_id):
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tb_campanhas WHERE cam_id = %s", (campaign_id,))
        conexao.commit()
        conexao.close()

    @staticmethod
    def get_all():
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tb_campanhas")
        results = cursor.fetchall()
        conexao.close()
        return [Campaign(*row) for row in results]

    def is_active(self):
        return self.deleted_at is None