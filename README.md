# 🔐 Sistema de Controle de Acesso RFID com Arquitetura Distribuída

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000.svg)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Sistema profissional completo de controle de acesso utilizando tecnologia RFID, desenvolvido com arquitetura distribuída e monitoramento em tempo real.

![Sistema RFID](https://img.shields.io/badge/Hardware-Raspberry_Pi-C51A4A.svg)
![Dashboard](https://img.shields.io/badge/Dashboard-Real_Time-success.svg)

---

## 📋 Sobre o Projeto

Este sistema foi desenvolvido para controlar e monitorar o acesso de colaboradores a salas restritas, oferecendo:

- ✅ **Controle de Acesso Inteligente**: Detecção automática de entrada/saída
- 📊 **Monitoramento em Tempo Real**: Dashboard web com atualização automática
- 🔒 **Sistema de Segurança**: Detecção de tentativas de invasão
- 💾 **Operação Offline**: Cache local no Raspberry Pi para funcionamento sem conexão
- 📈 **Análise de Dados**: Relatórios detalhados com Pandas
- 🎯 **Arquitetura Distribuída**: API REST, frontend separado e sistema físico independente

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                Dashboard Web (React + Tailwind)         │
│          Monitoramento em Tempo Real | Port 3000        │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST API
                        ↓
┌─────────────────────────────────────────────────────────┐
│              API Backend (Flask + SQLite)               │
│    • Autenticação JWT                                   │
│    • Gerenciamento de Colaboradores                     │
│    • Logs de Acesso | Port 5000                         │
└───────────┬────────────────────────────┬────────────────┘
            │                            │
            ↓                            ↓
┌───────────────────────┐    ┌──────────────────────────┐
│ Raspberry Pi + RFID   │    │  Análise de Dados        │
│ • Leitor MFRC522      │    │  • Pandas                │
│ • Cache Local         │    │  • Relatórios            │
│ • LEDs (GPIO)         │    │  • Estatísticas          │
│ • Modo Offline        │    │  • Tempo Permanência     │
└───────────────────────┘    └──────────────────────────┘
```

---

## 🚀 Funcionalidades

### Sistema Físico (Raspberry Pi)

- 🎫 **Leitura RFID**: Detecção automática de tags MFRC522
- 🚪 **Entrada/Saída Inteligente**: 
  - Primeira leitura → "Bem-vindo, {nome}"
  - Segunda leitura → "Bem-vindo de volta, {nome}"
  - Terceira leitura → Saída
- 💡 **Feedback Visual**:
  - LED Verde (5s) → Acesso permitido
  - LED Vermelho (5s) → Acesso negado
  - LED Vermelho piscando (10x) → Tentativa de invasão
- 💾 **Cache Local**: Operação offline com sincronização automática
- 📊 **Relatório de Sessão**: Gerado ao pressionar Ctrl+C

### Dashboard Web

- 🔐 **Autenticação**: Login seguro com tokens JWT
- 📈 **Estatísticas em Tempo Real**:
  - Total de acessos permitidos
  - Pessoas atualmente na sala
  - Acessos negados
  - Tentativas de invasão
- 👥 **Gerenciamento de Colaboradores**:
  - Criar, editar e excluir
  - Controle de permissões
  - Visualização de tags RFID
- 🔔 **Feed de Atividades**: Eventos em tempo real
- 📱 **Responsivo**: Interface moderna com Tailwind CSS

### API Backend

- 🔑 **Autenticação JWT**: Sistema seguro de tokens
- 📝 **CRUD Completo**: Gerenciamento de colaboradores
- 📊 **Logs Detalhados**: Registro de todos os eventos
- 🔄 **API RESTful**: Endpoints bem documentados
- 💾 **SQLite**: Banco de dados leve e eficiente

### Análise de Dados

- 📊 **Relatórios Personalizados**:
  - Relatório diário de acessos
  - Tempo de permanência por colaborador
  - Top usuários mais ativos
  - Distribuição por hora do dia
- 🚨 **Alertas de Segurança**: Histórico de tentativas suspeitas
- 📈 **Estatísticas Avançadas**: Análise com Pandas

---

## 📦 Tecnologias Utilizadas

### Backend
- **Flask** - Framework web Python
- **SQLite** - Banco de dados
- **Flask-SocketIO** - WebSocket para tempo real
- **Flask-CORS** - Suporte a CORS

### Frontend
- **React 18** - Biblioteca JavaScript
- **Tailwind CSS** - Framework CSS utilitário
- **Lucide React** - Ícones modernos

### Hardware
- **Raspberry Pi** - Computador de placa única
- **MFRC522** - Leitor RFID
- **RPi.GPIO** - Controle de pinos GPIO

### Análise
- **Pandas** - Manipulação e análise de dados
- **Matplotlib** - Visualização de dados
- **Seaborn** - Gráficos estatísticos

---

## 🛠️ Instalação e Configuração

### Pré-requisitos

- Python 3.7 ou superior
- Node.js 14 ou superior
- Raspberry Pi 3 ou superior (para sistema físico)
- Leitor RFID MFRC522

### 1. Clonar o Repositório

```bash
git clone https://github.com/rklein7/RFID-e-sistemas-distribuidos.git
cd RFID-e-sistemas-distribuidos
```

### 2. Configurar Backend

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor
python app.py
```

O backend estará rodando em `http://localhost:5000`

**Credenciais padrão:** `admin` / `admin123`

### 3. Configurar Dashboard

```bash
cd dashboard-rfid

# Instalar dependências
npm install

# Iniciar em modo desenvolvimento
npm start
```

O dashboard estará em `http://localhost:3000`

### 4. Configurar Raspberry Pi

```bash
# No Raspberry Pi
sudo apt-get update
sudo apt-get install python3-dev python3-pip

# Instalar bibliotecas
pip3 install RPi.GPIO mfrc522 requests

# Editar API_URL no código
nano rfid_reader.py
# Alterar: API_URL = 'http://SEU_IP_SERVIDOR:5000/api'

# Executar
sudo python3 rfid_reader.py
```

### 5. Executar Análises

```bash
# Modo interativo
python analytics.py

# Ou acessar via API
python analytics.py --use-api --token SEU_TOKEN
```

---

## 🔌 Diagrama de Conexões (Raspberry Pi)

```
MFRC522          Raspberry Pi
────────────────────────────
SDA    ────────→ GPIO 8  (CE0)
SCK    ────────→ GPIO 11 (SCLK)
MOSI   ────────→ GPIO 10 (MOSI)
MISO   ────────→ GPIO 9  (MISO)
GND    ────────→ GND
RST    ────────→ GPIO 25
3.3V   ────────→ 3.3V

LED Verde (+)   → GPIO 17 → Resistor 220Ω → GND
LED Vermelho(+) → GPIO 27 → Resistor 220Ω → GND
```

---

## 🎮 Como Usar

### Operação Básica

1. **Iniciar Backend**: `python app.py`
2. **Iniciar Dashboard**: `npm start` (em dashboard-rfid/)
3. **Iniciar Raspberry Pi**: `sudo python3 rfid_reader.py`

### Fluxo de Acesso

1. Colaborador aproxima o crachá RFID
2. Sistema verifica permissões
3. LED acende (verde = permitido, vermelho = negado)
4. Mensagem exibida no terminal
5. Evento registrado no banco de dados
6. Dashboard atualiza em tempo real

### Testando sem Hardware

```bash
# Executar simulador
python test_simulator.py

# Escolher modo:
# 1 - Modo interativo (digitar tags manualmente)
# 2 - Cenário: Dia normal de trabalho
# 3 - Cenário: Tentativas de invasão
# 4 - Cenário: Acessos negados
# 5 - Teste de stress
```

---

## 📡 API Reference

### Autenticação

#### `POST /api/auth/login`
Fazer login no sistema

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "expires_at": "2025-10-14T18:00:00"
}
```

### Colaboradores

#### `GET /api/collaborators`
Listar colaboradores (requer autenticação)

#### `POST /api/collaborators`
Criar colaborador (requer autenticação)

**Request:**
```json
{
  "name": "João Silva",
  "rfid_tag": "RFID001",
  "has_access": true
}
```

#### `PUT /api/collaborators/{id}`
Atualizar colaborador (requer autenticação)

#### `DELETE /api/collaborators/{id}`
Excluir colaborador (requer autenticação)

### Logs

#### `POST /api/logs/access`
Registrar evento de acesso

**Request:**
```json
{
  "rfid_tag": "RFID001",
  "collaborator_name": "João Silva",
  "event_type": "entry",
  "access_granted": true
}
```

Tipos de eventos: `entry`, `exit`, `denied`, `unknown`

#### `GET /api/logs`
Obter logs (requer autenticação)

**Query Parameters:**
- `start_date`: Data inicial (YYYY-MM-DD)
- `end_date`: Data final (YYYY-MM-DD)

---

## 🧪 Testes

### Cenários de Teste Disponíveis

```bash
python test_simulator.py
```

1. **Dia Normal**: Simula um dia completo de trabalho
2. **Tentativas de Invasão**: Tags desconhecidas
3. **Acessos Negados**: Colaboradores sem permissão
4. **Teste de Stress**: 50 eventos sequenciais
5. **Modo Interativo**: Teste manual de tags

---

## 📈 Relatórios e Análises

O sistema oferece análises detalhadas através do módulo Pandas:

### Relatório Completo
```bash
python analytics.py
# Opção 1
```

Exibe:
- Estatísticas gerais do sistema
- Top 10 usuários por tempo
- Histórico de alertas de segurança
- Período analisado

### Relatório Diário
```bash
python analytics.py
# Opção 2 > Digite a data (YYYY-MM-DD)
```

Exibe:
- Total de entradas e saídas
- Distribuição por hora
- Colaboradores mais ativos
- Tempo de permanência

### Tempo de Permanência
```bash
python analytics.py
# Opção 3 > Digite o nome do colaborador
```

---

## 🔒 Segurança

### Implementações de Segurança

- ✅ Autenticação JWT com expiração de tokens
- ✅ Senhas criptografadas com SHA-256
- ✅ CORS configurado para endpoints específicos
- ✅ Validação de entrada em todas as rotas
- ✅ Logs detalhados de tentativas de acesso
- ✅ Detecção automática de invasão
- ✅ Cache local para operação offline

### Recomendações para Produção

1. Alterar senha padrão do admin
2. Usar HTTPS com certificado SSL
3. Configurar firewall adequadamente
4. Implementar backup automático do banco
5. Usar variáveis de ambiente para credenciais
6. Adicionar rate limiting na API

---

## 👨‍💻 Autor

**Bruno da Motta Pasquetti**

**Gabriel Brocco de Oliveira**

**Pedro Henrique de Bortolli**

**Rafael Augusto Klein**

---

<div align="center">

**⭐ Se este projeto foi útil, deixe uma estrela! ⭐**

</div>