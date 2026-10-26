# Como contribuir

O Conversor é um projeto pessoal em desenvolvimento para Windows x64. Antes de uma mudança extensa, abra uma issue descrevendo o problema e a proposta.

Para relatar falhas, informe a versão, a operação, a extensão do arquivo, o comportamento esperado e a mensagem apresentada. Remova nomes de usuário, caminhos pessoais e links privados dos diagnósticos. Não envie documentos ou mídias sem autorização para compartilhá-los.

## Desenvolvimento

Siga a preparação e os comandos do [README](README.md). Os motores são obtidos separadamente; não devem ser adicionados ao Git. Os testes precisam dos componentes indicados e geram suas próprias amostras.

Use nomes descritivos e mantenha as regras em `.editorconfig`. Mensagens da interface devem permanecer em português. Preserve originais, cancelamento e isolamento de falhas por item. Ao adicionar um formato, atualize catálogo, worker, testes pertinentes e documentação dos limites.

Descreva no pull request o problema, o comportamento após a mudança e as verificações executadas. Diferencie testes offline de consultas a plataformas reais. Não altere políticas de segurança do Windows para fazer um teste passar.

As contribuições devem poder ser distribuídas sob a licença AGPL-3.0 deste repositório. Identifique material externo e preserve suas atribuições e condições.
