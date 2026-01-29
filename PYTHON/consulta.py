import requests
import json
import os
from dotenv import load_dotenv

usuario = os.getenv("NOVAVIDA_USUARIO")
senha = os.getenv("NOVAVIDA_SENHA")
cliente = os.getenv("NOVAVIDA_CLIENTE")
url = os.getenv("NOVAVIDA_URL")

telefone = os.getenv("TELEFONE")

# Configurações iniciais
BASE_URL = url

# OBS: CREDENCIAIS NOVA VIDA
CREDENCIAIS = {
    "usuario": usuario,
    "senha": senha, 
    "cliente": cliente
}

# --- ALTERAÇÃO AQUI: SOLICITA O CPF AO USUÁRIO ---
print("\n" + "="*30)
cpfdigitado = input("Digite o CPF ou CNPJ para consulta: ")

def obter_token():
    url = f"{BASE_URL}/GerarTokenJson"
    payload = {"credencial": CREDENCIAIS}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        try:
            dados_json = response.json()
            if 'd' in dados_json:
                return dados_json['d']
            return dados_json
        except:
            token_raw = response.text
            return token_raw.strip().replace('"', '')

    except Exception as e:
        print(f"Erro ao gerar token: {e}")
        return None

def consultar_documento(token, documento):
    url = f"{BASE_URL}/NVCHECKJson"
    payload = {
        "nvcheck": {
            "Documento": documento
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'Token': token
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        dados = response.json()
        
        # Às vezes o retorno vem dentro de 'd', e às vezes esse 'd' é uma string JSON
        retorno = dados.get('d', dados)
        
        # Se o retorno for uma string (json stringificado), converte para dict
        if isinstance(retorno, str):
            return json.loads(retorno)
            
        return retorno

    except Exception as e:
        print(f"Erro na consulta: {e}")
        return None

# --- Execução ---
print("Iniciando autenticação...")
token_acesso = obter_token()

if token_acesso:
    print(f"Token gerado com sucesso...") 
    
    cpf_cnpj = cpfdigitado
    
    print(f"Consultando CPF: {cpf_cnpj}...")
    resultado = consultar_documento(token_acesso, cpf_cnpj)
    
    if resultado:
        
        # Navega com segurança usando .get() para não quebrar se faltar algum dado
        consulta = resultado.get('CONSULTA', {})
        cadastrais = consulta.get('CADASTRAIS', {})
        situacao_cadastral = consulta.get('SITUACAOCADASTRAL', {})
        
        # Monta o dicionário limpo
        dados_filtrados = {
            "Nome": cadastrais.get('NOME'),
            "CPF": cadastrais.get('CPF'),
            "Nascimento": cadastrais.get('NASC'),
            "Idade": cadastrais.get('IDADE'),
            "Mãe": cadastrais.get('NOME_MAE', 'Não informado'), # Exemplo caso tenha mãe
            "Score": cadastrais.get('SCORE'),
            "Risco": cadastrais.get('MENSAGEMSCORE'),
            "Situação": situacao_cadastral.get('DESCRICAO'),
            "Sexo": cadastrais.get('SEXO'),
        }

        # Exemplo extra: Pegar o primeiro endereço se existir
        enderecos = consulta.get('ENDERECOS', [])
        if enderecos:
            # Pega o primeiro da lista
            end = enderecos[0]
            # Monta string de endereço
            logradouro = end.get('LOGRADOURO') or ""
            numero = end.get('NUMERO') or ""
            bairro = end.get('BAIRRO') or ""
            cidade = end.get('CIDADE') or ""
            uf = end.get('UF') or ""
            dados_filtrados["Endereço Principal"] = f"{logradouro}, {numero} - {bairro}, {cidade}/{uf}"

        print("\n" + "=" * 30)
        print("RESULTADO RESUMIDO:")
        print(json.dumps(dados_filtrados, indent=4, ensure_ascii=False))
        # --------------------------------------
        
    else:
        print("Não houve retorno de dados.")
else:
    print("Falha ao obter o token.")