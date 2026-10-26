# Validação da versão 0.2

Verificações realizadas em 26/10/2026. A rodada anterior de conversões está descrita em `VALIDACAO.md` e `RELATORIO-TESTES-20261026.md`; ela não foi repetida integralmente nesta alteração.

## Testes automatizados

- **53 testes offline da função de downloads**: serviços aceitos, URLs fora do escopo, seleção de formatos e qualidade, consulta de metadados, playlists com falhas, item inicial indisponível, cancelamento, preservação de resultados, conflito de nomes, mensagens sem links assinados e exclusão de lives/estreias futuras.
- **77 testes de regressão de conversão e publicação** passaram após a reorganização do código. Os 11 testes de Office dessa suíte foram excluídos dessa repetição; continuam documentados na rodada anterior.
- Compilação/publicação de WPF e CLI em .NET 10 passaram. A verificação de formatação C# passou.

Os testes offline usam um adaptador controlado e não provam disponibilidade dos serviços externos.

## Downloads reais

| Serviço / caso | Resultado conferido |
|---|---|
| YouTube, vídeo público de 19 s | MP4 com limite de 144p; vídeo de 192 × 144 e áudio AAC; decodificação completa sem erros |
| Instagram, reel público de teste | MP4 H.264, 720 × 1280, aproximadamente 5 s; decodificação completa sem erros; o exemplo não tem áudio |
| TikTok, link público fornecido pelo usuário | MP4 H.264 com áudio AAC, 576 × 1024, aproximadamente 458 s; decodificação completa sem erros |
| Playlist pública curta do YouTube | Consulta identificou a playlist; download de seu único item com limite de 720p foi concluído |
| YouTube → MP3 pela janela instalada | Consulta, seleção de áudio/192 kbps, fila e histórico concluíram; MP3 de aproximadamente 19 s foi reaberto e decodificado sem erros |

O primeiro exemplo antigo do YouTube estava indisponível. Os primeiros testes de TikTok falharam; depois de incluir a dependência oficial opcional curl-cffi, o link fornecido pelo usuário foi baixado. Isso não garante que todos os links funcionem: bloqueios regionais, conteúdo privado, alterações da plataforma e verificações de acesso continuam possíveis.

## Interface e preservação

A aba foi inspecionada visualmente na instalação 0.2.0. A seleção de somente áudio atualizou formatos e taxas; a análise exibiu título, duração e plataforma. O Histórico mostrou o progresso e o resultado do download.

Uma segunda tarefa foi cancelada pela interface quando já havia publicado um item. O estado informou o cancelamento e preservou o item salvo; o MP3 anterior conservou seu SHA-256. O teste offline cobre também cancelamento antes de publicar o próximo item de uma playlist. Essa verificação pela interface não representa interrupção comprovada no meio de uma transferência longa.

Os testes reais e seus arquivos ficam em `tests/results`, excluídos do ZIP de código-fonte. Históricos, configurações e executáveis anteriores foram preservados antes da atualização local. Não houve publicação no GitHub.

## Limites

Não foram testadas playlists reais com múltiplos itens nesta rodada; esse fluxo foi coberto pelo adaptador offline. Não foram usados login, cookies de navegador, DRM ou serviços de download de terceiros. Esta versão não retoma tarefas após encerrar o aplicativo. Reinício do PC e múltiplas telas/escalas continuam fora desta rodada.
