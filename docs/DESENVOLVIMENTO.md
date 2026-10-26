# Desenvolvimento e apresentação do projeto

Projeto pessoal de Gabriel para estudar aplicações desktop, integração com Windows, processos e tratamento de arquivos. A implementação e os testes receberam assistência de IA (Codex). A referência de interação foi o Filee; o projeto não usa seu código como base.

O projeto permite demonstrar decisões sobre preservação de originais, organização de uma fila, resposta da interface, tratamento de falhas de motores externos e validação de resultados reais. Para apresentá-lo, convém conseguir explicar essas decisões e seus limites.

## Como estudar e explicar o código

1. Acompanhe um arquivo da ação da janela até `ConversionQueue.Enqueue` e o JSON enviado ao worker.
2. Veja como o catálogo limita destinos e como o menu circular recebe arquivos pelo mecanismo de drag-and-drop do Windows.
3. Compare o cancelamento cooperativo pelo arquivo marcador com o encerramento da árvore de processos.
4. Execute o teste de conflito de nomes e explique por que a saída é reservada antes de ser publicada.
5. Na aba de downloads, siga o caminho consulta → seleção de qualidade → fila → publicação de cada item.
6. Leia as limitações dos testes: validar amostras não equivale a garantir todos os documentos ou codecs.

## Convenções

- C# com nomes descritivos, arquivos separados por responsabilidade e padrões definidos em `.editorconfig`.
- Python com funções para as operações e protocolo explícito; a formatação é mantida por Ruff.
- Comentários explicam decisões ou particularidades dos motores, sem narrar cada linha.
- Testes offline verificam contratos e falhas previsíveis; testes com plataformas reais são executados separadamente.
- Motores e resultados de testes ficam fora do repositório de código.

## Publicação

O código foi preparado para publicação sob AGPL-3.0, por escolha do proprietário. O instalador pessoal reúne componentes livres e proprietários; essa composição não foi aprovada para redistribuição pública. Não incluir vídeos baixados, fontes do Windows, cache, histórico, configurações pessoais ou credenciais.

A publicação inicial reúne o estado do desenvolvimento local em um commit real. Melhorias posteriores devem registrar mudanças efetivas; não foram inventados commits ou experiência profissional para o portfólio.
