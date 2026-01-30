import requests
import json
from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv

# ==============================================================================
# CONFIGURAÇÕES GERAIS
# ==============================================================================
load_dotenv()

usuario = os.getenv("NOVAVIDA_USUARIO")
senha = os.getenv("NOVAVIDA_SENHA")
cliente = os.getenv("NOVAVIDA_CLIENTE")
url = os.getenv("NOVAVIDA_URL")

usuario_v8 = os.getenv("V8_LOGIN")
senha_v8 = os.getenv("V8_SENHA")
url_v8 = os.getenv("V8_URL")

telefone = os.getenv("TELEFONE")

# Configurações da API Nova Vida
API_BASE_URL = url
API_CREDS = {
    "usuario": usuario,
    "senha": senha, 
    "cliente": cliente
    }

# Configurações do Sistema V8 
V8_URL = url_v8 
V8_LOGIN = usuario_v8
V8_SENHA = senha_v8

# ==============================================================================
# PARTE 1: API NOVA VIDA (Busca os dados)
# ==============================================================================
def obter_token_api():
    try:
        response = requests.post(
            f"{API_BASE_URL}/GerarTokenJson", 
            json={"credencial": API_CREDS}, 
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            dados = response.json()
            return dados.get('d', dados) if isinstance(dados, dict) else response.text.strip('"')
    except Exception as e:
        print(f"[API] Erro ao obter token: {e}")
    return None

def buscar_dados_cliente(cpf):
    token = obter_token_api()
    if not token:
        return None

    print(f"[API] Consultando dados do CPF {cpf}...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/NVCHECKJson",
            json={"nvcheck": {"Documento": cpf}},
            headers={'Content-Type': 'application/json', 'Token': token}
        )
        
        dados = response.json()
        raw_data = dados.get('d', dados)
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
            
        # Filtra apenas o necessário para o V8
        cadastrais = raw_data.get('CONSULTA', {}).get('CADASTRAIS', {})
        
        if not cadastrais.get('NOME'):
            return None

        return {
            "Nome": cadastrais.get('NOME'),
            "CPF": cadastrais.get('CPF'),
            "Nasc": cadastrais.get('NASC'),
            "Sexo": cadastrais.get('SEXO'),
            "NomeMae": cadastrais.get('NOME_MAE', '')
        }
    except Exception as e:
        print(f"[API] Erro na consulta: {e}")
        return None

# ==============================================================================
# PARTE 2: AUTOMACAO V8 (Playwright)
# ==============================================================================
def executar_automacao_v8(dados_cliente):
    print(f"\n[V8] Iniciando automação para: {dados_cliente['Nome']}")
    
    with sync_playwright() as p:
        # headless=False para você ver o navegador abrindo (bom para dev)
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()

        try:
            # 1. Acessar V8
            print("[V8] Acessando página de login...")
            page.goto(V8_URL)

            # PASSO 1: Clicar em "Entrar na minha conta"
            # Usamos get_by_role para ser bem específico: "Quero o botão que tem o nome X"
            print("[V8] Clicando no botão de entrar...")
            page.get_by_role("button", name="Entrar na minha conta").click()

            page.wait_for_selector('input[name="email"]')

            # PASSO 2: Preencher Login e Senha
            print("[V8] Preenchendo credenciais...")

            page.fill("input[name='email']", V8_LOGIN)
            page.fill("input[name='password']", V8_SENHA)
            page.click("button[type='submit']")

            time.sleep(6)  # Aguarda 6 segundos para garantir o login

            # PASSO 3: Ir para pagina CLT
            print("[V8] Navegando para Crédito Consignado...")
            page.goto("https://app.v8sistema.com/credito-consignado")

            # PASSO 4: 'Gerar termo de autorização'
            print("[V8] Clicando em Gerar termo...")
            
            page.get_by_role("button", name="Gerar termo de autorização").click()

            print("[V8] Aguardando modal de cadastro...")
            page.wait_for_selector('input[name="signerName"]')

            print("[V8] Preenchendo dados cadastrais...")

            page.fill('input[name="signerName"]', dados_cliente['Nome'])
            page.fill('input[name="borrowerDocumentNumber"]', dados_cliente['CPF'])
            page.fill('input[name="signerEmail"]', 'naotenho123@live.com')
            page.fill('input[name="signerPhone"]', telefone)
            page.fill('input[name="birthDate"]', dados_cliente['Nasc'])
            sexo_api = dados_cliente.get('Sexo')
            sexo_formatado = sexo_api.title()
            page.get_by_text("Gênero", exact=True).click()
            page.get_by_text(sexo_formatado, exact=True).click()
            time.sleep(2)
            page.click("button[type='submit']")
            
            time.sleep(2)  # Aguarda 2 segundos

            print("[V8] Iniciando autorização...")

            # Pegando o link gerado
            page.get_by_placeholder("Buscar").fill(dados_cliente['CPF']) # Preenche o CPF no campo de busca
            page.get_by_role("button", name="Pesquisar").click()
            
            time.sleep(2)

            botao_link = page.locator("p.chakra-text.css-w1yups").first 
            botao_link.click() # Pega o link gerado e clica nele
            link_capturado = page.evaluate("navigator.clipboard.readText()")
            print(f"[V8] Link capturado: {link_capturado}")

            time.sleep(2)
         
            # Autorizando LINK
            nova_aba = context.new_page()
            nova_aba.goto(link_capturado)      

            nova_aba.wait_for_selector('input[name="cpf"]')
            nova_aba.fill('input[name="cpf"]', dados_cliente['CPF'])
            nova_aba.click("button[type='submit']")
            time.sleep(2)

            nova_aba.locator(".chakra-checkbox__control").first.click()
            time.sleep(0.5)
            nova_aba.get_by_role("button", name="Confirmar").click()

            nova_aba.get_by_text("Termo aceito com sucesso!").wait_for(state="visible")
            print("PROCESSO FINALIZADO: TERMO ACEITO COM SUCESSO!")

            print("[V8] Fechando a aba do termo...")
            nova_aba.close()

            # PASSO 5: LOOP DE VERIFICAÇÃO DE ERROS
            max_tentativas = 25
            status_final = None

            for i in range(max_tentativas):
                print(f"[V8] Verificação {i+1}/{max_tentativas}...")
                
                # --- PASSO 1: ATUALIZAR A PÁGINA ---
                botao_atualizar = page.locator("button[aria-label='edit']").first
                
                if botao_atualizar.is_visible():
                    # print("Clicando no botão de atualizar...") # Descomente se quiser ver o log
                    botao_atualizar.click()
                else:
                    print("[AVISO] Botão 'edit' não encontrado. Recarregando (F5)...")
                    page.reload()
                    page.wait_for_load_state("networkidle")

                # Espera o React renderizar
                time.sleep(4)

                # --- PASSO 2: DETECTAR STATUS DE ERRO VISÍVEL ---
                # .locator("visible=true") ignora os elementos ocultos do modo mobile
                badge_rejeitado = page.get_by_text("Rejeitado").locator("visible=true")
                badge_falha = page.get_by_text("Falha ao gerar consentimento").locator("visible=true")

                # Se encontrou algum (count > 0)
                if badge_rejeitado.count() > 0 or badge_falha.count() > 0:
                    print("[V8] 🚨 Erro detectado! Iniciando captura inteligente...")
                    
                    # Define quem é o alvo (quem apareceu na tela)
                    alvo = badge_rejeitado.first if badge_rejeitado.count() > 0 else badge_falha.first
                    
                    # --- ACHAR O ÍCONE (ESTRATÉGIA DO PAI) ---
                    # 1. alvo.locator("xpath=..") -> Sobe para a DIV PAI que segura o texto e o ícone
                    # 2. .locator("svg") -> Pega o ícone dentro desse pai
                    icone_info = alvo.locator("xpath=..").locator("svg").first
                    
                    # (Opcional) Pinta de vermelho para você ver que achou certo
                    try:
                        icone_info.evaluate("el => el.style.border = '2px solid red'")
                    except:
                        pass 

                    icone_info.scroll_into_view_if_needed()
                    
                    # --- HOVER (PASSAR O MOUSE) ---
                    print("Passando o mouse no ícone...")
                    icone_info.hover(force=True)
                    time.sleep(1) # Essencial para o Portal aparecer

                    # --- CAPTURAR MENSAGEM (ESTRATÉGIA DO PORTAL) ---
                    mensagem_erro = "Erro não identificado"
                    
                    try:
                        # O Chakra UI joga o tooltip no final do HTML (Portal)
                        # Pegamos o último portal que apareceu (.last) e pegamos a div direta dele
                        portal_tooltip = page.locator(".chakra-portal > div").last
                        
                        # Espera ficar visível e conter texto
                        portal_tooltip.wait_for(state="visible", timeout=3000)
                        
                        if portal_tooltip.count() > 0:
                            mensagem_erro = portal_tooltip.text_content().strip()
                        else:
                            raise Exception("Portal vazio")
                            
                    except:
                        print("⚠️ Falha ao capturar pelo Portal. Tentando fallback...")
                        # Fallback: Tenta pegar qualquer texto que tenha aparecido flutuando
                        try:
                            texto_flutuante = page.locator("div[id^='tooltip-']").last
                            if texto_flutuante.is_visible():
                                mensagem_erro = texto_flutuante.text_content().strip()
                        except:
                            pass

                    print(f"❌ MENSAGEM FINAL: {mensagem_erro}")
                    
                    # Salva o status e sai do loop
                    status_final = "ERRO"
                    break 

                else:
                    print(f"Status pendente. Aguardando... ({i+1})")
                    time.sleep(5)

            # --- FIM DO LOOP ---
            
            # Validação final para o VS Code não reclamar da variável
            if status_final == "ERRO":
                print(f"🚨 Processo finalizado com FALHA: {mensagem_erro}")
                # Se quiser parar o robô aqui: raise Exception(mensagem_erro)
            else:
                print("✅ Processo finalizado com SUCESSO (Aprovado ou tempo esgotado).")

        except Exception as e:
            print(f"[V8] Erro durante a automação: {e}")
            page.screenshot(path="eerro_v8.png")
        
        finally:
            browser.close()

# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("--- SISTEMA INTEGRADO NOVA VIDA -> V8 ---")
    cpf_input = input("Digite o CPF do cliente: ").strip().replace(".", "").replace("-", "")

    if cpf_input:
        # Passo 1: Busca dados na API
        cliente = buscar_dados_cliente(cpf_input)

        if cliente:
            print(f"\n[SUCESSO] Cliente encontrado: {cliente['Nome']}")
            
            # Passo 2: Joga os dados no Playwright
            executar_automacao_v8(cliente)
        else:
            print("[ERRO] Cliente não encontrado na Nova Vida. Abortando V8.")
    else:
        print("CPF inválido.")
