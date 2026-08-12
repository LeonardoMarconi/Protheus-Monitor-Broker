# Broker Monitor

Painel web para **monitoramento de Brokers TOTVS**, permitindo consultar informações de servidores, conexões, usuários, threads, consumo de memória, CPU e demais informações disponibilizadas pelos endpoints HTTP do Broker.

O projeto é composto por um **proxy HTTP local em Python** e uma **interface web HTML/JavaScript**, permitindo que o navegador consulte Brokers TOTVS localizados na rede privada.

---

## 📋 Visão geral

O **Broker Monitor** foi desenvolvido para facilitar a visualização das informações disponibilizadas pelo Broker TOTVS através de uma interface web simples e centralizada.

A aplicação possui dois componentes principais:

* `broker_proxy.py` — servidor HTTP local responsável por intermediar as requisições entre o navegador e os Brokers TOTVS.
* `broker_userinfo.html` — painel web responsável pela apresentação, filtros, estatísticas e gerenciamento dos Brokers.

O proxy utiliza a porta **8765** por padrão e disponibiliza as rotas:

```text
GET /userinfo?target=IP:PORTA
GET /brokerinfo?target=IP:PORTA
```

O endereço do Broker informado pelo usuário é validado antes do encaminhamento da requisição. O código permite somente hosts `localhost` ou endereços pertencentes às redes privadas RFC1918.

---

## 🏗️ Arquitetura

```text
┌──────────────────────────────┐
│          Navegador           │
│                              │
│   broker_userinfo.html       │
└──────────────┬───────────────┘
               │
               │ HTTP
               ▼
┌──────────────────────────────┐
│       broker_proxy.py        │
│                              │
│       localhost:xxxx         │
└──────────────┬───────────────┘
               │
               │ HTTPS
               ▼
┌──────────────────────────────┐
│        Broker TOTVS          │
│                              │
│  /totvs_broker_query         │
│  /totvs_broker_query/        │
│       userinfo               │
└──────────────────────────────┘
```

O navegador não acessa diretamente o Broker. As requisições são realizadas através do proxy Python, que também adiciona os headers CORS necessários para permitir o consumo pela interface web.

---

## ✨ Funcionalidades

### Monitoramento do Broker

O painel apresenta informações como:

* Servidores do cluster
* Status dos servidores
* Número de conexões
* Usuários conectados
* Threads
* Memória utilizada
* CPU
* Uptime
* PID

As informações dos servidores são obtidas através do endpoint `brokerinfo`.

### 👥 Usuários conectados

O painel apresenta:

* Usuário
* Host
* Função
* Ambiente
* Tipo de thread
* Data/hora da conexão
* Uptime
* Tempo ocioso
* Instruções por segundo
* Detalhes/observações

Também é possível identificar conexões de **SmartClient** e **Jobs/Threads**.

### 🔎 Filtros

É possível filtrar os dados por:

* Usuário
* Host
* Função
* Ambiente
* Tipo de thread

O painel também permite ordenar as colunas da tabela de usuários.

### 🔄 Atualização automática

O monitor possui atualização manual e automática.

Intervalos disponíveis:

```text
5 segundos
10 segundos
30 segundos
60 segundos
```

O usuário pode ativar ou desativar o Auto Refresh diretamente no painel.

### 🖥️ Múltiplos Brokers

É possível cadastrar vários Brokers e alternar entre eles através das abas do painel.

Cada Broker possui:

* Nome de exibição
* IP/Host
* Porta

As configurações são armazenadas no `localStorage` do navegador.

Também é possível:

* Adicionar Broker
* Editar Broker
* Remover Broker
* Alternar entre Brokers cadastrados

### 🌙 Tema claro/escuro

O painel possui suporte a:

* Dark Mode
* Light Mode

A preferência do usuário também é armazenada no `localStorage`.

---

# 🚀 Instalação

## Pré-requisitos

* Python 3.x
* Acesso de rede ao Broker TOTVS
* Broker TOTVS disponibilizando os endpoints HTTP utilizados pela aplicação
* Navegador moderno

O projeto utiliza somente módulos nativos do Python no proxy, incluindo:

```text
http.server
urllib
ssl
json
re
os
mimetypes
```

Portanto, não é necessário instalar dependências através de `pip`.

---

## 📁 Estrutura do projeto

```text
broker-monitor/
│
├── broker_proxy.py
├── broker_userinfo.html
└── README.md
```

Os dois arquivos principais devem permanecer no mesmo diretório.

O `broker_proxy.py` utiliza o diretório onde o próprio script está localizado para encontrar o arquivo HTML:

```text
broker_userinfo.html
```

---

# ▶️ Executando

O servidor será iniciado na porta definida na chave abaixo no arquivo broker_proxy.py [edite antes de subir o server]:

```text
PROXY_PORT
```

Abra um terminal no diretório do projeto:

```bash
python broker_proxy.py
```

O próprio script informa no console os endereços disponíveis:

```text
Servidor rodando em http://0.0.0.0:[porta do Proxy]/

Painel:
http://localhost:[porta do Proxy]/

API userinfo:
GET /userinfo?target=IP:PORTA

API brokerinfo:
GET /brokerinfo?target=IP:PORTA
```

---

# 🌐 Acessando o painel

Após iniciar o Python, acesse:

```text
http://localhost:[porta do Proxy]/
```

O proxy identifica a requisição à raiz e entrega automaticamente o arquivo:

```text
broker_userinfo.html
```

---

# ⚙️ Configurando um Broker

No painel:

1. Clique em **Gerenciar brokers**.
2. Clique em **Adicionar novo**.
3. Informe o nome do Broker.
4. Informe o endereço no formato:

```text
IP:PORTA
```

Exemplo:

```text
192.xxx.xxx.xxx:xxxx
```

5. Clique em **Salvar**.

A interface utiliza o endereço cadastrado para consultar os endpoints do proxy.

---

# 🔌 API do Proxy

## `/userinfo`

Consulta informações dos usuários conectados ao Broker.

### Requisição

```http
GET /userinfo?target=192.xxx.xxx.xxx:xxxx
```

O proxy transforma a chamada em:

```text
https://192.xxx.xxx.xxx:xxxx/totvs_broker_query/userinfo
```

---

## `/brokerinfo`

Consulta informações gerais do Broker e seus servidores.

### Requisição

```http
GET /brokerinfo?target=192.xxx.xxx.xxx:xxxx
```

O proxy encaminha para:

```text
https://192.xxx.xxx.xxx:xxx/totvs_broker_query
```

---

# 🔐 Segurança

O proxy possui uma validação básica para impedir que qualquer endereço arbitrário seja utilizado como destino.

São aceitos:

```text
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
localhost
```

Essa validação é realizada através de expressão regular antes da criação da URL do Broker.

### ⚠️ Atenção

O código atualmente desabilita a validação do certificado TLS para as conexões HTTPS realizadas pelo proxy:

```python
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
```

Isso facilita a comunicação com Brokers que utilizam certificados internos ou não confiáveis pelo sistema, porém **reduz a segurança da conexão TLS**.

Para ambientes produtivos, recomenda-se avaliar a utilização de certificados confiáveis e validação TLS adequada.

---

# 🌍 CORS

O proxy adiciona os seguintes headers:

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

Além disso, requisições `OPTIONS` recebem resposta HTTP `204`.

---

# 🧠 Funcionamento do painel

Ao iniciar, a interface:

1. Carrega os Brokers armazenados no `localStorage`.
2. Caso não exista nenhum Broker, cria uma configuração inicial.
3. Seleciona o primeiro Broker.
4. Consulta `/userinfo`.
5. Consulta `/brokerinfo`.
6. Renderiza as informações no painel.

As duas consultas são executadas simultaneamente utilizando `Promise.all()`.

---

# 📊 Indicadores

O painel calcula e apresenta indicadores resumidos, incluindo:

### Cluster

* Servidores
* Conexões
* Usuários
* Memória total
* CPU média

### Usuários

* Conexões totais
* SmartClients
* Jobs/Threads
* Ambientes

---

# 🛠️ Tratamento de erros

Caso o Broker não esteja acessível ou ocorra uma falha na consulta, o proxy retorna HTTP `502` com informações do erro.

```json
{
  "error": "mensagem do erro",
  "target": "https://..."
}
```

A interface também apresenta uma mensagem orientando a verificar se:

* O `broker_proxy.py` está em execução.
* O Broker está acessível pela rede.
* O endereço configurado está correto.

---

# 📦 Dependências

### Backend

Nenhuma dependência externa.

Utiliza exclusivamente bibliotecas padrão do Python.

### Frontend

O HTML utiliza recursos externos para:

* **Tabler Icons**
* **Google Fonts / Roboto**

Esses recursos são referenciados diretamente no HTML.

---

# 🧪 Exemplo de utilização

Supondo que o Broker esteja disponível em:

```text
192.xxx.xxx.xxx:xxxx
```
Execute:

```bash
python broker_proxy.py
```

Depois abra:

```text
http://localhost:[porta do Proxy]/
```

Cadastre:

```text
Nome: Broker Principal
Endereço: 192.xxx.xxx.xxx:xxxx
```

O painel passará a consultar automaticamente:

```text
http://localhost:[porta do Proxy]/userinfo?target=192.xxx.xxx.xxx:xxxx
```

e:

```text
http://localhost:[porta do Proxy]/brokerinfo?target=192.xxx.xxx.xxx:xxxx
```

---

# 📌 Observações

Este projeto foi desenvolvido para facilitar o monitoramento operacional de ambientes TOTVS Protheus utilizando as informações disponibilizadas pelo Broker.

A aplicação funciona como uma camada intermediária:

```text
Browser
   ↓
Broker Monitor Proxy
   ↓
TOTVS Broker
   ↓
Informações do ambiente
```

O projeto não altera configurações do Broker nem executa comandos administrativos sobre os servidores. Seu objetivo é realizar consultas e apresentar as informações de forma visual.

---


# 👨‍💻 Autor

**Leonardo Marconi**

Projeto desenvolvido para monitoramento e observabilidade de ambientes **TOTVS Protheus / Broker**.
