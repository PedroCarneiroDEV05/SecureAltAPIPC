<div align="center">

# Sistema de Autenticação Segura

Sistema full-stack de autenticação construído com foco em segurança real — não apenas um login funcional, mas uma arquitetura de sessão com decisões conscientes sobre exposição de credenciais, tempo de vida de token e recuperação de sessão.

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens&logoColor=white)
![Google OAuth](https://img.shields.io/badge/Google_OAuth-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white)

</div>

---

## Sobre o Projeto

O problema que motivou esse projeto é clássico em aplicações reais: como manter o frontend responsivo e com boa experiência de sessão sem armazenar credenciais de longa duração onde o JavaScript possa alcançá-las?

A resposta implementada aqui é um modelo híbrido de tokens. O access token é um JWT de curta duração que fica no cliente e é usado nas requisições autenticadas. O refresh token é opaco, armazenado no servidor como hash e entregue ao navegador exclusivamente via cookie HTTPOnly — inacessível ao JavaScript por design. Quando o access token expira, o frontend solicita a renovação ao backend e o navegador anexa o cookie automaticamente, sem que nenhum código do lado do cliente precise tocar nessa credencial.

Além da autenticação local, o sistema integra Google OAuth com vinculação automática de contas por e-mail, rotação de refresh tokens a cada renovação de sessão e detecção de reuso de tokens revogados como sinal de comprometimento.

---

## Arquitetura

```
.
├── app/
│   ├── core/          # Configurações e utilitários de segurança
│   ├── db/            # Conexão com banco de dados
│   ├── deps/          # Dependências de autenticação (injeção)
│   ├── models/        # Modelos SQLAlchemy
│   ├── routes/        # Rotas HTTP da API
│   ├── schemas/       # Schemas Pydantic
│   └── services/      # Regras de negócio
├── frontend/
│   ├── components/    # Componentes React
│   ├── context/       # Contexto global de autenticação
│   ├── pages/         # Páginas Next.js
│   ├── services/      # Cliente HTTP com interceptors
│   └── styles/        # Estilos globais
├── tests/
├── requirements.txt
└── README.md
```

O backend separa roteamento de lógica de negócio: as rotas lidam com HTTP, os serviços cuidam de criação de usuário, verificação de credenciais e geração de tokens. No frontend, o estado de sessão vive no `AuthContext` e os interceptors do Axios gerenciam a injeção e renovação do access token de forma transparente para o restante da aplicação.

---

## Fluxo de Autenticação

| Etapa | Ação |
|---|---|
| 1 | Usuário cria conta em `/auth/register` com e-mail e senha |
| 2 | Login em `/auth/login` — credenciais verificadas no backend |
| 3 | Backend emite o access token JWT no corpo da resposta |
| 4 | Backend grava o refresh token em cookie HTTPOnly |
| 5 | Frontend armazena o access token em `sessionStorage` |
| 6 | Requisições autenticadas usam `Authorization: Bearer <token>` |
| 7 | `/auth/me` retorna os dados do usuário com o token válido |
| 8 | Quando o token expira, `/auth/refresh` usa o cookie para emitir um novo par |
| 9 | Logout limpa a sessão local e remove o cookie no servidor |

---

## Design de Segurança

**Rotação de tokens.** A cada renovação de sessão, o refresh token atual é revogado e um novo é emitido. Se um token já revogado for apresentado novamente, o sistema interpreta isso como um possível comprometimento e invalida todas as sessões ativas do usuário de forma preventiva.

**Cookies HTTPOnly.** O refresh token nunca é exposto ao JavaScript — o navegador o gerencia e o envia automaticamente nas requisições de renovação. Isso elimina a classe de ataques que dependem de leitura de credenciais via XSS.

**Validação de state no OAuth.** O parâmetro `state` gerado no servidor é armazenado em cookie temporário e conferido no callback do Google, prevenindo ataques CSRF durante o fluxo de autorização.

**Vinculação de contas.** Se um usuário tenta entrar via Google com um e-mail que já existe como conta local, as contas são vinculadas automaticamente — sem criar duplicatas e sem perder o histórico da conta original.

---

## Fluxo do Google OAuth

```
Usuário clica em "Entrar com Google"
        │
        ▼
GET /auth/google/login
        │
        ▼
Backend gera state, salva em cookie temporário
e redireciona para o Google
        │
        ▼
Usuário autoriza no Google
        │
        ▼
Google redireciona para /auth/google/callback
        │
        ▼
Backend valida o state, busca dados do usuário no Google
        │
        ├── Conta existente? → Vincula e autentica
        └── Conta nova?      → Cria e autentica
        │
        ▼
Redireciona para http://localhost:3000/auth-callback
com access token e refresh token (cookie HTTPOnly)
```

---

## Como Executar

### Pré-requisitos

- Python 3.10+
- Node.js 18+

### Backend

```bash
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

| Recurso | URL |
|---|---|
| API | `http://localhost:8000` |
| Health check | `http://localhost:8000/health` |
| Documentação interativa | `http://localhost:8000/docs` |

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplicação disponível em `http://localhost:3000`.

---

## Variáveis de Ambiente

### Backend — `.env`

```env
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
ADMIN_EMAIL=seu@email.com
GOOGLE_CLIENT_ID=seu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

### Frontend — `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Descrição das variáveis

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão do banco de dados |
| `SECRET_KEY` | Chave usada para assinar os tokens JWT |
| `ALGORITHM` | Algoritmo de assinatura dos tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tempo de validade do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Tempo de validade do refresh token |
| `ENVIRONMENT` | Define comportamentos de desenvolvimento ou produção |
| `ADMIN_EMAIL` | E-mail promovido automaticamente a administrador |
| `GOOGLE_CLIENT_ID` | Identificador OAuth do Google |
| `GOOGLE_CLIENT_SECRET` | Segredo OAuth do Google |
| `GOOGLE_REDIRECT_URI` | Callback registrado no Google OAuth |
| `FRONTEND_URL` | URL usada pelo backend para redirecionar ao frontend |
| `NEXT_PUBLIC_API_URL` | URL da API consumida pelo frontend |

---

## Administração

Em desenvolvimento, a aplicação garante a existência de uma conta administrativa no startup:

```
E-mail: admin@example.com
Senha:  admin123
```

Se a conta não existir, ela é criada. Se já existir, é mantida como administradora. Em produção, essa conta fixa não é criada — use a variável `ADMIN_EMAIL` para promover uma conta existente.

---

## Desenvolvimento vs. Produção

| Configuração | Desenvolvimento | Produção |
|---|---|---|
| HTTPS | Não obrigatório | Obrigatório |
| Flag `Secure` nos cookies | Desativada | Ativada |
| Conta admin fixa | Criada no startup | Não criada |
| `SECRET_KEY` | Qualquer valor | Chave forte e privada |
| Credenciais Google OAuth | Projeto de teste | Projeto de produção verificado |

---

## Roadmap

- Redefinição de senha por e-mail
- Verificação de conta por e-mail
- Bloqueio de conta após tentativas falhas consecutivas
- Suporte a outros provedores OAuth
