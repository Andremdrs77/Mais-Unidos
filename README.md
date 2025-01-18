# + Unidos

## Sistema de Gerenciamento de Doações e Campanhas Beneficentes

### Objetivo
Desenvolver uma aplicação web utilizando Flask (Python) e MySQL para gerenciar doações e campanhas beneficentes realizadas por ONGs ou grupos sociais. O sistema permitirá cadastro, controle e geração de relatórios detalhados para acompanhar doadores, itens doados e o impacto das campanhas.

---

## Funcionalidades Principais

### 1. Cadastro e Edição de Dados
- **Doadores:** Registro de informações como nome, e-mail, telefone e histórico de doações.
- **Campanhas:** Cadastro de campanhas beneficentes, incluindo título, descrição, metas (financeiras ou de itens), prazo e status.
- **Itens e Doações:** Registro de itens doados ou valores monetários associados a uma campanha, com detalhes como tipo de item, quantidade e data de doação.

### 2. Gestão de Campanhas
- Atualização do status da campanha (ativa, concluída, cancelada).
- Visualização do progresso da meta da campanha.

### 3. Relatórios e Consultas Avançadas
- **Doações por período:** Total arrecadado em um intervalo de datas.
- **Top doadores:** Lista de maiores doadores em valor ou quantidade de itens.
- **Impacto da campanha:** Relatório que compara as metas definidas com os resultados obtidos.
- **Campanhas mais bem-sucedidas:** Identificação das campanhas com maior arrecadação em diferentes períodos (7, 30, 60, 90 dias).
- **Itens mais doados:** Listagem de itens mais comuns nas doações, categorizados.

---

## Tecnologias Utilizadas

- **Backend:** Flask (Python)
- **Banco de Dados:** MySQL
- **Frontend:** HTML, CSS, JavaScript (opcional: frameworks como Bootstrap ou React)
- **Outros:** SQLAlchemy (ORM), Flask-Migrate (controle de migrações de banco de dados)

---

## Configuração do Ambiente de Desenvolvimento

### Pré-requisitos
1. Python 3.8 ou superior
2. MySQL 5.7 ou superior
3. Git (para versionamento de código)

### Passos para Configuração

1. **Clone o Repositório:**
   ```bash
   git clone https://github.com/seuusuario/mais-unidos.git
   cd mais-unidos
   ```

2. **Crie um Ambiente Virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate # Para Linux/Mac
   venv\Scripts\activate   # Para Windows
   ```

3. **Instale as Dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o Banco de Dados:**
   - Crie um banco de dados no MySQL:
     ```sql
     CREATE DATABASE mais_unidos;
     ```
   - Configure as credenciais no arquivo `.env`:
     ```env
     DB_HOST=localhost
     DB_USER=seu_usuario
     DB_PASSWORD=sua_senha
     DB_NAME=mais_unidos
     ```

5. **Execute as Migrações:**
   ```bash
   flask db upgrade
   ```

6. **Inicie o Servidor:**
   ```bash
   flask run
   ```
   Acesse o sistema em [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## Estrutura do Projeto

```
mais-unidos/
│
├── app/
│   ├── __init__.py       # Inicialização do aplicativo
│   ├── models.py         # Modelos do banco de dados
│   ├── routes.py         # Rotas da aplicação
│   ├── templates/        # Arquivos HTML
│   └── static/           # Arquivos CSS, JS e imagens
│
├── migrations/           # Arquivos de migração do banco de dados
├── .env                  # Configurações do ambiente (não versionado)
├── requirements.txt      # Dependências do projeto
├── config.py             # Configurações do Flask
└── run.py                # Arquivo principal para rodar o servidor
```

---

## Contribuição

Contribuições são bem-vindas! Siga os passos abaixo:
1. Faça um fork deste repositório.
2. Crie um branch para suas alterações:
   ```bash
   git checkout -b minha-melhoria
   ```
3. Realize as alterações desejadas e faça commit:
   ```bash
   git commit -m "Descrição das alterações"
   ```
4. Envie suas alterações:
   ```bash
   git push origin minha-melhoria
   ```
5. Abra um Pull Request.

---

## Licença
Este projeto está licenciado sob a [MIT License](LICENSE).

---

## Contato
Para dúvidas ou sugestões, entre em contato pelo e-mail: **seuemail@dominio.com**
