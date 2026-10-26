# Conversor

Aplicativo desktop para Windows x64, em português, feito com C#/.NET 10 e WPF. Reúne conversão local de arquivos, redimensionamento de imagens e vídeos e downloads de mídia em uma fila com histórico e cancelamento.

Projeto pessoal em desenvolvimento, versão 0.3.1. Criado para estudar aplicações desktop, integração com Windows e processamento de arquivos. Este repositório distribui o código-fonte; os motores e o instalador pessoal não estão incluídos.

## O que faz

- **Conversões:** imagens, PDF, documentos Office, áudio/vídeo, e-books, compactados, fontes e CAD, conforme os pares do catálogo.
- **Menu circular:** Ctrl + arrastar no Explorador; solte sobre um formato. Tab alterna as páginas e Esc cancela.
- **Downloads:** links públicos de YouTube, Instagram e TikTok, com consulta de qualidades, vídeo ou áudio e playlists/coleções.
- **Redimensionamento:** imagens e vídeos com tamanhos prontos ou personalizados, recorte por posição, faixas e prévia do enquadramento.
- **Organização:** lotes, histórico, escolha de pasta, bandeja, início automático e pastas monitoradas.

A aplicação preserva os originais e numera saídas quando já existe um arquivo com o mesmo nome. Conversões não enviam arquivos a serviços externos. A aba de downloads usa a internet para acessar a plataforma escolhida.

## Baixar mídia

Na aba **Baixar vídeos**, cole um link e clique em **Consultar link**. Escolha vídeo ou áudio, o formato, a qualidade e a pasta; depois adicione à fila. Acompanhe ou cancele pelo Histórico.

Vídeo pode ser salvo em MP4 ou MKV. Áudio pode ser extraído em MP3, M4A, WAV ou FLAC. Para playlists, marque a opção antes da consulta. As resoluções mostradas vêm do primeiro item; cada item usa a melhor qualidade até o limite escolhido. Itens indisponíveis são registrados, e itens já salvos são preservados ao cancelar.

Somente os três serviços anunciados são aceitos. A disponibilidade depende da plataforma, do link e da região; mudanças nos sites podem exigir atualização do yt-dlp. Esta versão usa links públicos, sem importar contas ou cookies do navegador, e não oferece downloads de DRM, transmissões ao vivo ou estreias futuras.

## Limites das conversões

| Categoria | Entradas reconhecidas | Destinos e operações |
|---|---|---|
| Imagens | JPG/JPEG, PNG, WEBP, BMP, TIF/TIFF, GIF, HEIC | PNG, JPG, WEBP, BMP, TIFF, GIF, PDF |
| PDF | PDF | PNG, JPG, juntar, separar, extrair páginas, comprimir |
| Textos | DOC, DOCX, ODT, RTF, TXT | PDF, DOCX, ODT, TXT |
| Planilhas | XLS, XLSX, ODS, CSV, TSV | PDF, XLSX, ODS, CSV, TSV |
| Apresentações | PPT, PPTX, ODP | PDF, PPTX, ODP |
| Vídeo | MP4, MOV, MKV, WEBM, AVI, WMV | MP4, MOV, MKV, WEBM; áudio MP3, WAV, FLAC, AAC, OGG |
| Áudio | MP3, WAV, FLAC, AAC, M4A, OGG, OPUS | MP3, WAV, FLAC, AAC, OGG, M4A |
| E-books | EPUB, MOBI, AZW3 | EPUB, MOBI, AZW3, PDF, TXT |
| Compactados | ZIP, 7Z, RAR, TAR, GZ | Extrair; criar ZIP e 7Z |
| Fontes | TTF, OTF, WOFF, WOFF2 | WOFF, WOFF2, restaurar TTF/OTF |
| CAD | DWG, DXF | DWG ↔ DXF; DXF para PDF, SVG, PNG |

A tabela resume o catálogo, não representa todas as combinações entre as colunas. A aplicação filtra destinos conforme extensão e componentes presentes e não oferece conversão para a mesma extensão. Juntar PDFs e extrair páginas são operações da janela; o menu circular oferece apenas ações compatíveis com o gesto. Arquivos comuns também podem ser empacotados em ZIP/7Z.

O catálogo é explícito: não existe promessa de qualquer entrada para qualquer saída. GIF e imagens com várias páginas usam o primeiro quadro/página. Compressão de PDF pode aumentar arquivos já otimizados. PDF para Word editável e OCR estão fora desta versão.

Restaurar WOFF/WOFF2 recupera TTF ou OTF conforme os contornos da fonte original. Para renderizar DWG, converta primeiro para DXF. A fidelidade de documentos complexos depende do motor utilizado.

## Redimensionar imagens e vídeos

Na aba **Redimensionar**, adicione ou solte arquivos. Escolha TikTok/Shorts (9:16), YouTube (16:9), quadrado (1:1), retrato (4:5) ou clássico (4:3). Largura e altura podem ser editadas diretamente. Para uma proporção diferente, digite, por exemplo, `3:2` e clique em **Aplicar**: a altura é calculada a partir da largura e arredondada para um número par.

**Preencher e recortar bordas** preenche as medidas sem deformar a imagem. Escolha uma das nove posições para manter a parte desejada. **Manter tudo com faixas pretas** mantém o quadro inteiro, centralizado. Selecione um arquivo e use **Atualizar prévia** para conferir o resultado antes de adicionar o lote à fila. A prévia de vídeo mostra o primeiro quadro, sem reprodução.

Imagens podem sair em PNG, JPG ou WEBP; vídeos em MP4, MKV ou WEBM. Em lotes mistos, cada tipo usa seu próprio formato. A pasta vazia salva ao lado dos originais; nomes recebem as dimensões e um número em conflitos. O Histórico oferece progresso, cancelamento e abertura dos resultados.

Vídeos mantêm a duração e as faixas de áudio, com reencodificação; não são copiadas legendas ou faixas de dados. Esta ferramenta não corta a duração. GIF/TIFF com múltiplos quadros usam somente o primeiro. PNG preserva transparência no modo de recorte; faixas usam fundo preto. Medidas aceitas: 16 a 7680 pixels por lado, até 33.177.600 pixels; vídeos exigem medidas pares. Aumentar as dimensões não recupera detalhes ausentes.

## Compilar e testar

Requisitos de desenvolvimento: Windows x64, [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0), PowerShell 7, [uv](https://docs.astral.sh/uv/) e [RTK](https://github.com/rtk-ai/rtk), utilizado nos scripts de preparação e empacotamento. Os motores são preparados em pastas privadas; essas ferramentas de desenvolvimento não são exigidas na instalação final.

Para compilar somente a interface, sem baixar os motores:

```powershell
dotnet build Conversor.csproj -c Release
dotnet build cli/Conversor.Cli.csproj -c Release
```

A interface compilada procura os componentes ao lado do executável. Para executar a aplicação a partir de uma publicação com os motores preparados:

```powershell
pwsh -File scripts/Prepare-Engines.ps1
dotnet publish Conversor.csproj -c Release -r win-x64 --self-contained true -o dist/app
Copy-Item engines dist/app/engines -Recurse -Force
pwsh -File scripts/Publish-Cli.ps1
Copy-Item conversor.cmd dist/app/
.\dist\app\Conversor.exe
```

A preparação precisa de internet, vários gigabytes livres e pode demorar. O ODA é um componente proprietário: consulte seus termos antes de prepará-lo ou redistribuí-lo. Não execute o script de preparação em uma instalação com tarefas em andamento. O manifesto registra componentes locais; entradas cujo arquivo não existe são preparadas novamente em um clone novo.

Para executar os testes com os componentes preparados:

```powershell
.\engines\python\python.exe -m pytest tests/test_media_download.py tests/test_worker_regressions.py tests/test_resize_media.py -q
```

A preparação baixa os componentes dos projetos oficiais e grava versões/origens/hashes em `engines.json`. Os scripts locais usam RTK para comandos suportados; ele pode ser substituído pelo comando original em outro ambiente de desenvolvimento. Para criar o instalador pessoal, execute `scripts/Build-Installer.ps1`.

Os testes de download acima são offline e usam um adaptador controlado. A verificação com sites reais é separada:

```powershell
.\engines\python\python.exe tests/probe_download_platforms.py
```

A matriz completa de conversões precisa de todos os motores. Usa o projeto por padrão; `CONVERSOR_TEST_APP` permite apontar para outra instalação. Os relatórios anteriores registram amostras verificadas, não uma garantia para qualquer arquivo.

## Automação e linha de comando

As pastas monitoradas aguardam o arquivo terminar de ser copiado. Apenas novos arquivos no nível diretamente monitorado são tratados. A saída precisa ficar fora das entradas monitoradas para evitar ciclos; não há varredura retroativa.

```powershell
.\conversor.cmd convert "C:\Fotos\imagem.png" --to webp
.\conversor.cmd convert "C:\Fotos\*.png" --to jpg -o "C:\Convertidos" --quality 90
```

A CLI usa a mesma fila da interface, espera o resultado e retorna JSON: código 0 em sucesso e 1 em falha. Cancele pelo Histórico; Ctrl+C no terminal não cancela a tarefa da interface. A nova função de downloads está disponível pela janela.

O bloqueio local de `conversor-cli.dll` na revisão 0.3.1 foi resolvido restaurando o lançador anterior intacto. EXE e CMD passaram em conversões reais, incluindo partida em segundo plano. O empacotamento preserva esse componente enquanto seu código não mudar. Novos binários ainda precisam de validação e, para distribuição previsível, assinatura confiável. Detalhes no relatório de recuperação abaixo.

## Dados e documentação

Preferências, histórico e diagnóstico ficam em `%LOCALAPPDATA%\Conversor`. O histórico contém caminhos e links. Fechar a janela mantém a bandeja; **Sair** encerra o aplicativo. Limpar o histórico não remove arquivos. Não há telemetria nem atualização automática dos motores.

- [Arquitetura e decisões](docs/ARQUITETURA.md)
- [Desenvolvimento e uso como portfólio](docs/DESENVOLVIMENTO.md)
- [Textos e conteúdo propostos para o GitHub](docs/PUBLICACAO-GITHUB.md)
- [Pesquisa preliminar de patentes e licenças](docs/PATENTES-E-LICENCAS.md)
- [Validação das conversões](VALIDACAO.md)
- [Validação da versão 0.2 e dos downloads](docs/VALIDACAO-0.2.md)
- [Validação da versão 0.3: playlist e redimensionador](docs/VALIDACAO-0.3.md)
- [Revisão 0.3.1: código, bandeja e limpeza](docs/VALIDACAO-0.3.1.md)
- [Recuperação e testes da CLI](docs/VALIDACAO-CLI-20261026.md)
- [Componentes de terceiros](THIRD-PARTY-NOTICES.md)
- [Histórico de versões](CHANGELOG.md)
- [Como contribuir](CONTRIBUTING.md)
- [Licenciamento](LICENSING.md)

## Validação e próximos passos

Os relatórios datados registram uma matriz histórica de 323 pares e verificações adicionais. A revisão 0.3.1 passou em 91 testes de redimensionamento, downloads offline e regressões. Esses números se referem às rodadas documentadas, não a cobertura medida nem a testes de todos os arquivos possíveis. Foram conferidos pela interface o gesto global, uma playlist de quatro vídeos com limite de 240p e redimensionamentos com dimensões verificadas.

Ainda precisam de validação: diferentes monitores e escalas, reinício físico com início automático e instalação completa seguida de desconexão da rede. A CLI sem assinatura pode ser bloqueada pela política do Windows; a recuperação local documentada não garante execução de novas compilações em outros computadores. Não há instalador público nesta publicação.

Próximas melhorias: assinatura confiável dos binários, revisão da redistribuição de componentes, testes em mais configurações de tela e simplificação da preparação dos motores.

## Autoria e licença

Projeto pessoal de Gabriel Siqueira, com assistência de IA na implementação, revisão e testes. O [Filee](https://github.com/KnifeLemon/Filee) foi referência de interação; seu código não foi usado como base. Os motores existentes realizam as conversões, e seus autores estão creditados em [Componentes de terceiros](THIRD-PARTY-NOTICES.md).

O código deste projeto é disponibilizado sob [GNU AGPL v3.0](LICENSE), conforme o escopo descrito em [LICENSING.md](LICENSING.md). Essa escolha não altera as licenças dos componentes externos nem autoriza redistribuir o ODA ou o instalador pessoal. Use downloads apenas para conteúdo que você tenha direito de baixar e respeite os termos das plataformas.

As amostras e os arquivos de demonstração do desenvolvimento não acompanham o código. Os testes automatizados geram novas entradas quando executados. Relatórios anteriores descrevem verificações realizadas; os arquivos de mídia usados nessas execuções foram removidos na limpeza local.
