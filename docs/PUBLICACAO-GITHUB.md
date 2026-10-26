# Apresentação do Conversor no GitHub

Textos para apresentar o projeto e orientar sua manutenção no portfólio. O código foi preparado sob AGPL-3.0; o instalador pessoal e os motores ficam fora da publicação. O estado do envio remoto deve ser conferido no próprio GitHub.

## Nome e descrição

Nome sugerido do repositório: `conversor-windows`.

Descrição curta:

> Aplicativo para Windows em C# e WPF para converter arquivos, redimensionar imagens e vídeos e organizar tarefas em uma fila com histórico.

Tópicos: `csharp`, `dotnet`, `wpf`, `windows`, `desktop-application`, `file-converter`, `ffmpeg`, `imagemagick`, `image-resizer`, `video-processing`, `yt-dlp`.

## Texto de abertura

> O Conversor é um projeto pessoal em desenvolvimento para reunir tarefas comuns de arquivos em um aplicativo para Windows. Ele permite converter formatos localmente, redimensionar imagens e vídeos e acompanhar o processamento em uma fila com histórico e cancelamento.
>
> A interface foi construída com C#/.NET 10 e WPF. O projeto integra motores como FFmpeg, ImageMagick e LibreOffice para realizar as conversões. Também possui um menu circular acionado por Ctrl + arrastar e uma aba para downloads de links públicos de YouTube, Instagram e TikTok.
>
> O desenvolvimento recebeu assistência de IA na implementação, revisão e testes. A interação do menu circular teve como referência o Filee. Os motores e bibliotecas utilizados mantêm suas próprias licenças.

## O que mostrar no README

1. Problema que o aplicativo resolve e estado atual: projeto pessoal em desenvolvimento.
2. Funcionalidades verificadas, com as limitações do catálogo e dos downloads.
3. Uma captura limpa da interface, sem arquivos pessoais, histórico ou dados de terceiros.
4. Tecnologias utilizadas e a responsabilidade de cada uma. A interface coordena o trabalho; motores existentes realizam as conversões.
5. Diagrama da arquitetura e uma explicação curta da fila, processos separados, cancelamento e publicação sem sobrescrever originais.
6. Instruções reproduzíveis de compilação e teste, incluindo a preparação dos componentes.
7. Validações datadas e limitações reais. Diferenciar testes automatizados, testes pela interface e verificações ainda pendentes.
8. Créditos, licença AGPL-3.0 do código e avisos dos componentes de terceiros.

O README atual já reúne grande parte dessas informações. O diagrama e os detalhes ficam em `ARQUITETURA.md`; os relatórios de validação registram as amostras verificadas.

## O que entra na publicação

Código C#, XAML e Python; projetos de compilação; scripts de preparação; testes que geram suas próprias amostras; ícone do aplicativo; documentação e avisos de terceiros. O ZIP de código-fonte é um ponto de partida para inspecionar o conteúdo antes de publicar.

Ficam fora: `engines`, `downloads`, `dist`, `bin`, `obj`, caches, resultados e amostras geradas, cópias locais de segurança, histórico, configurações, fontes do Windows, vídeos baixados, documentos pessoais e credenciais. Não anexar o instalador pessoal como Release antes de revisar as licenças de redistribuição. A ausência de binários de terceiros não elimina automaticamente obrigações decorrentes da integração com bibliotecas.

## Como explicar em uma entrevista

Use uma tarefa concreta para apresentar o fluxo: seleção do arquivo → validação do destino → fila → processo de conversão → publicação do resultado. Mostre por que os originais são preservados, como um erro não interrompe o lote e o que acontece ao cancelar.

Descreva o que você consegue explicar e modificar hoje. Evite afirmar que escreveu tudo sozinho, que criou os motores de conversão ou que domina todas as tecnologias apenas por constarem no projeto. Um projeto assistido continua sendo útil no portfólio quando o aprendizado, as decisões e os limites estão claros.

## Para construir um perfil consistente

Fixe poucos projetos que funcionem e tenham boa documentação. Mantenha descrições diretas, instruções verificáveis, imagens próprias e um histórico real de melhorias. Registre problemas e correções concretos em vez de criar atividade ou números artificiais. Atualize o portfólio conforme conseguir explicar melhor o código e realizar novas mudanças.

Não são necessárias badges de cobertura, CI ou desempenho que o projeto ainda não mede. Capturas de tela e um vídeo curto podem ser produzidos mais tarde com material próprio; as amostras usadas no desenvolvimento foram removidas a pedido do proprietário.
