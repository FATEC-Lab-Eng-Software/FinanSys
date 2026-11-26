# Assistente financeiro Hermes

## Visão geral

O FinanSys oferece um assistente financeiro integrado ao backend FastAPI. Hermes fornece o modelo/orquestrador OpenAI-compatible, enquanto o projeto implementa o roteamento e as ferramentas financeiras e de livros. O cliente chama `POST {HERMES_API_BASE_URL}/chat/completions` com `model: "hermes-agent"`, histórico de mensagens e autenticação Bearer via `HERMES_API_SERVER_KEY`. O Compose configura o serviço `hermes` com a imagem `nousresearch/hermes-agent:stable`, porta interna `8642`, armazenamento persistente e rede de API separada. O serviço `server` recebe a URL/chave por ambiente. A chave `OPENAI_API_KEY` configurada para o Supabase Studio é independente dessa conexão.

## Fluxo de conversa

1. A página client-side `/assistente` mantém o histórico em estado local, começa com uma saudação e envia as mensagens ao backend por `POST /assistant/chat`, com cookies de sessão. A página limita o histórico enviado a 20 mensagens, a mensagem digitada a 4.000 caracteres e redireciona ao login se a API responder `401`.
2. O router exige usuário autenticado e verifica a origem do navegador. O schema exige de 1 a 20 mensagens, cada uma com papel `user` ou `assistant`, conteúdo não vazio de até 4.000 caracteres, última mensagem do usuário e soma de conteúdo de até 12.000 caracteres.
3. `AssistantCoordinator` chama `OrchestratorAgent`, que inclui o prompt `apps/server/prompts/assistant-system.md` e o histórico na solicitação ao Hermes. A resposta precisa ser JSON conforme `AssistantPlan`; campos extras ou combinações inválidas são rejeitados.
4. O plano pode ser uma resposta direta, uma consulta financeira, geração de relatório, envio demonstrativo de email ou busca de livros. Consultas financeiras, relatórios e ações usam o agente financeiro e as ferramentas locais; recomendações usam o curador e Google Books.
5. A resposta da API segue `AssistantChatResponse`: texto e, opcionalmente, artefatos em base64 ou até 10 livros. O cliente mantém o histórico durante a sessão da página e o reapresenta a cada requisição.

Falhas de configuração, comunicação, timeout, resposta inválida/incompleta do Hermes e falhas de ferramentas são convertidas em erros HTTP com código e mensagem pelo router/serviços. O cliente usa a mensagem recebida para exibir o erro.

## Consulta financeira e relatório

O prompt `financial-consultation.md` orienta o consultor a responder em português, de forma curta, usando apenas o resumo financeiro fornecido e comparações disponíveis. O consultor obtém o resumo por `FinancialSummaryTool`, que agrega transações do usuário autenticado no período solicitado, com máximo de 366 dias. O resumo contém receitas, despesas, saldo (receitas menos despesas), quantidade de transações, despesas por categoria e totais de despesas por mês, em BRL; meses sem despesas entram com total zero.

Se o usuário não informar datas, o coordenador usa o mês corrente completo em `America/Sao_Paulo`. O prompt determina que períodos incompletos ou ambíguos sejam esclarecidos; o plano também rejeita período com apenas uma das datas. A consulta não retorna transações individuais ao modelo: a ferramenta agrega os totais e o consultor recebe o resumo junto ao histórico.

Para relatório, o coordenador usa o mesmo resumo para gerar um PDF local (`relatorio-financeiro.pdf`), devolvido como artefato base64. Para email, exige destinatário segundo o prompt e gera o PDF antes de chamar SMTP para `mailpit:1025`, com remetente `assistente@finansys.local`; a API devolve o artefato e a resposta informa envio demonstrativo ao Mailpit local. Esse fluxo não entrega email a um serviço externo. A interface permite baixar o PDF recebido.

## Recomendações de livros

O prompt de sistema direciona pedidos de livros, inclusive leitura para aprender um tema, ao `curador_livros`, com uma consulta curta em português sem dados pessoais/financeiros. O agente usa `GoogleBooksClient` e consulta exclusivamente `https://www.googleapis.com/books/v1/volumes`, com filtro `printType=books`, idioma `pt`, relevância e limite de até 10 resultados (o cliente solicita 5 por padrão). Requer `GOOGLE_BOOKS_API_KEY`; sem a chave, retorna indisponibilidade configurada.

Os resultados são normalizados para título, autores, descrição (com HTML removido), data de publicação e link do Google Books. Registros sem ID/título válido são descartados; o schema limita a descrição a 700 caracteres, autores a cinco e retorno a dez livros. A interface apresenta os dados catalográficos e links para o Google Books.

## Escopo operacional e configuração

- O cliente mantém as mensagens do histórico durante a sessão da página e envia esse contexto a cada solicitação.
- A consulta financeira agrega transações do usuário autenticado em períodos de até 366 dias.
- O fluxo de email usa SMTP local em `mailpit:1025`, com remetente `assistente@finansys.local`, para visualizar e validar relatórios enviados.
- A busca de livros usa o catálogo do Google Books e apresenta metadados bibliográficos e links de referência.
- O planejador valida o formato estruturado retornado pelo modelo antes de encaminhar as solicitações às ferramentas do produto.
- A configuração de execução usa `HERMES_API_BASE_URL`, `HERMES_API_SERVER_KEY` e `GOOGLE_BOOKS_API_KEY`.

## Evidências de código consultadas

Arquivos de implementação:

- `apps/server/prompts/assistant-system.md` e `apps/server/prompts/financial-consultation.md`: instruções do orquestrador e consultor.
- `apps/server/src/routers/assistant.py`, `schemas/assistant.py` e `main.py`: endpoint, validação dos contratos e registro do router.
- `apps/server/src/services/assistant_hermes_client.py`, `assistant_planner.py`, `assistant_service.py` e `assistant_orchestrator.py`: chamada do Hermes, validação do plano e coordenação.
- `apps/server/src/services/assistant_tools.py` e `financial_consultation_agent.py`: consulta agregada restrita ao usuário autenticado e geração do contexto financeiro.
- `apps/server/src/services/assistant_reports.py` e `assistant_action_tools.py`, além de `apps/server/templates/emails/financial-report.html` e `.txt`: geração de PDF e envio demonstrativo ao Mailpit.
- `apps/server/src/services/book_recommendation_agent.py`, `assistant_book_tools.py` e `google_books_client.py`: busca e normalização de livros do Google Books.
- `apps/server/src/core/config.py`, `docker-compose.yml` e `docker/hermes-start.sh`: parâmetros e execução dos serviços Hermes e Google Books.
- `apps/web/src/app/(system)/assistente/page.tsx`, `src/services/assistant.ts`, `src/types/assistant.ts` e `src/components/assistant/BookRecommendations.tsx`: tela e contrato consumido pelo frontend.
