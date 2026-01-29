# 🤖 Automação Integrada: Nova Vida ↔️ V8 Consignado

Este projeto é uma ferramenta de automação RPA (Robotic Process Automation) desenvolvida em **Python**. O sistema integra a consulta de dados de clientes na API **Nova Vida** e automatiza o processo de cadastro, geração de termos e validação de status no sistema **V8 Consignado**.

## 🚀 Funcionalidades

* **Consulta via API**: Busca dados cadastrais completos (Nome, CPF, Nascimento, Mãe, Sexo) diretamente na base da Nova Vida.
* **Automação de Navegador**: Utiliza o **Playwright** para controlar o Google Chrome.
* **Preenchimento Inteligente**: Preenche formulários no V8 automaticamente com os dados recuperados.
* **Gestão de Termos**: Gera links de autorização, abre novas abas e realiza o aceite do termo automaticamente.
* **Monitoramento em Tempo Real**: Loop de verificação que detecta atualizações de status ("Aprovado", "Rejeitado", "Falha").
* **Captura de Erros**: Sistema robusto para capturar mensagens de erro em tooltips (balões) do Chakra UI, mesmo quando escondidos em Portais ou iframes.

---

## 🛠️ Tecnologias Utilizadas

* [Python 3.x](https://www.python.org/)
* [Playwright](https://playwright.dev/python/) (Automação Web)
* [Requests](https://pypi.org/project/requests/) (Consumo de API)
* [Python-Dotenv](https://pypi.org/project/python-dotenv/) (Gerenciamento de variáveis de ambiente)

---

## 📝 Pré-requisitos

Antes de começar, certifique-se de ter instalado em sua máquina:

* [Git](https://git-scm.com/install/windows)
* [Python](https://www.python.org/downloads/)

---

## ⚙️ Instalação Passo a Passo

Siga os comandos abaixo no seu terminal (CMD, PowerShell ou VS Code) para configurar o ambiente.

### 1. Clone o repositório

Baixe o código para o seu computador:

```bash
git clone https://github.com/lovssthzn/consultav8consignado.git
cd consultav8consignado
```

### 2. Crie o Ambiente Virtual (Opcional, mas recomendado)

Isso evita conflitos com outras bibliotecas do seu PC.

## Windows
```bash
python -m venv venv
.\venv\Scripts\activate
```
## Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

Instale as bibliotecas listadas no requirements.txt

```bash
pip install -r requirements.txt 
```

### 4. Instale os Navegadores do Playwright

O script precisa dos binários do navegador para rodar:

```bash
playwright install
```

## 🔐 Configuração das Senhas (.env)
Por segurança, as senhas não ficam no código. Você precisa criar um arquivo .env.

- Vá até o arquivo .env.example na raiz do projeto (onde está o v8.py)

- Preencha com seus dados reais

- Troque o nome do arquivo para ".env", retirando o ".example" do final

Nota: Nunca suba o arquivo .env para o GitHub! Crie um ".gitignore" e adicione ".env"

## ▶️ Como Rodar

Para rodar a Automação Completa (API + V8), este é o script principal que faz todo o processo:

```bash
python v8.py
```
- O sistema pedirá o CPF do cliente e iniciará o navegador automaticamente.

Para testar apenas a consulta na API, se quiser apenas ver os dados do cliente:

```bash
python consulta.py
```

## 🐛 Solução de Problemas Comuns

### Erro: "playwright not found"
- Certifique-se de que rodou pip install -r requirements.txt.

### Erro: "Executable doesn't exist"
- Você esqueceu de rodar o comando playwright install.

### Login falhando ou API negada
- Verifique se o arquivo .env foi criado corretamente e se não há espaços extras nas senhas.

### Tela congela ou erro de Timeout
- Verifique sua conexão com a internet. O script tem esperas automáticas, mas conexões muito lentas podem exceder o limite.