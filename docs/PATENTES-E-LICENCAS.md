# Patentes, autoria e licenças

Pesquisa preliminar de 26/10/2026, com foco no Brasil. Não é uma busca completa de liberdade de operação e não conclui que o produto esteja livre de reivindicações de terceiros.

## Há patentes para algo assim?

Existem documentos de patente relacionados a menus radiais e gestos de seleção. Um exemplo encontrado é [US8627233B2 — Radial menu with overshoot, fade away, and undo capabilities](https://patents.google.com/patent/US8627233B2/en). Encontrar esse documento não significa que ele cubra este aplicativo: seria necessário comparar cada reivindicação com a implementação, verificar a família, os territórios e a situação jurídica atual. Esta pesquisa não confirmou uma patente específica que impeça o Conversor no Brasil.

Patentes são territoriais; um documento americano não cria automaticamente proteção brasileira. Ver [perguntas frequentes da WIPO](https://www.wipo.int/en/web/patents/faq_patents).

No Brasil, o programa de computador **em si** não é considerado invenção pelo art. 10, V, da Lei da Propriedade Industrial. Isso não exclui toda invenção implementada por computador: um processo ou produto que resolva um problema técnico pode ser examinado conforme os requisitos aplicáveis. Ver a [Lei 9.279/1996](https://www.gov.br/mdic/pt-br/acesso-a-informacao/institucional/atos-normativos/leis/lei-no-9-279-de-14-de-maio-de-1996) e as [diretrizes do INPI para invenções implementadas em computador](https://www.gov.br/inpi/pt-br/servicos/patentes/legislacao/legislacao/PortariaINPIPR4112020_DIRPAInvenesImplementadasemComputador_05012021.pdf).

O código-fonte tem proteção autoral, distinta da patente. O registro de programa de computador no INPI pode servir como prova e não é obrigatório para existir proteção. Ver as [perguntas frequentes de programas de computador do INPI](https://www.gov.br/inpi/pt-br/acesso-a-informacao/perguntas-frequentes/programas-de-computador).

## Direito autoral e publicação do projeto

A [Lei 9.609/1998, art. 2º, § 3º](https://www2.camara.leg.br/legin/fed/lei/1998/lei-9609-19-fevereiro-1998-364738-normaatualizada-pl.html) estabelece que a proteção independe de registro. A proteção do código não cria exclusividade sobre toda funcionalidade de converter ou redimensionar arquivos. Já existem aplicativos com essas funções; a existência deles não equivale a uma proibição geral de desenvolver outro.

É possível apresentar o trabalho próprio no GitHub respeitando direitos de terceiros. Isso não significa declarar autoria sobre motores, bibliotecas, referências visuais ou qualquer material copiado. A participação humana e a assistência de IA devem ser descritas conforme o trabalho efetivo; não se deve presumir autoria exclusiva sobre todo trecho gerado automaticamente.

Publicar um repositório visível não o torna automaticamente open source. Sem uma licença, não há uma autorização geral de uso, alteração ou redistribuição, embora os termos do GitHub permitam visualizar e fazer fork de repositórios públicos. Ver a [documentação do GitHub sobre licenças](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

O proprietário escolheu AGPL-3.0 para o código próprio, conforme [LICENSING.md](../LICENSING.md). A integração com PyMuPDF merece atenção: sua [documentação oficial](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) informa licenciamento AGPL ou comercial. Colocar MIT apenas no código próprio não afastaria obrigações que possam surgir da combinação. O [FFmpeg também distingue LGPL e GPL conforme a compilação](https://ffmpeg.org/legal.html). O tratamento correto depende do conteúdo distribuído e de como os componentes são integrados.

Para este portfólio, a publicação foi preparada com código e documentação, sem anexar o instalador completo. Essa escolha não equivale a aprovar a redistribuição de todos os componentes. A descrição e a seleção de conteúdo estão em `PUBLICACAO-GITHUB.md`.

## Referência visual não é licença universal

O [Filee publica seu código sob MIT](https://github.com/KnifeLemon/Filee/blob/main/LICENSE). Essa licença rege o material licenciado pelo projeto e não concede uma autorização genérica para todos os motores ou resolve, por si só, questões de patentes e marcas. Neste projeto, Filee foi uma referência de interação; não houve importação de seu código.

## O que importa antes do GitHub

Publicar o código autoral e redistribuir o instalador completo são decisões diferentes. FFmpeg, calibre, Ghostscript, PyMuPDF, LibreOffice e os demais componentes têm condições próprias. O ODA File Converter é proprietário e requer revisão de seus termos de redistribuição. A lista está em `THIRD-PARTY-NOTICES.md`.

A AGPL do código próprio não transforma todo o pacote em material sob uma licença única. A autoria e o uso de assistência de IA devem ser descritos de acordo com o desenvolvimento efetivo.

Se houver intenção de comercializar ou distribuir amplamente, a etapa adequada é uma análise das reivindicações e licenças para os países de interesse. A simples semelhança de um menu, ou sua diferença visual, não encerra essa análise.
