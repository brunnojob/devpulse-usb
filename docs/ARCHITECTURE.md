# Decisões de implementação

O agente coleta métricas no computador e envia o mesmo pacote para as saídas habilitadas: arquivo, terminal ou USB. O display não tenta descobrir dados do sistema operacional sozinho.

| Arquivo | Responsabilidade |
| --- | --- |
| `agent.py` | Entrada compatível com execução direta pelo checkout |
| `devpulse/cli.py` | Argumentos, ciclo de coleta, arquivos e encerramento |
| `devpulse/telemetry.py` | Amostragem, taxas e continuidade dos alertas |
| `devpulse/protocol.py` | Contrato de métricas e serialização limitada |
| `devpulse/transport.py` | Porta, timeout, backoff e recuperação de escrita parcial |
| `firmware/DevPulse/LineFramer.h` | Enquadramento independente de Arduino, testável em C++ nativo |
| `firmware/DevPulse/DevPulse.ino` | Validação do payload, validade da leitura e renderização |
| `assets/session.mjs` | Parsing, resumo e coordenadas de séries; testável sem DOM |
| `assets/site.js` | Interação da bancada e atualização do DOM |

## Por que Python + JSON

psutil disponibiliza as métricas nos três sistemas de desktop sem manter um coletor por SO. JSON por linha permite observar uma sessão com ferramentas comuns e reaproveitar o mesmo formato no display e no navegador. O custo é mais bytes e parsing do que um protocolo binário; o limite fixo e o intervalo padrão de um segundo tornam esse custo explícito.

As dependências Python ficam no agente. O Pages usa módulos nativos do navegador, sem framework ou backend. Node e Prettier são usados apenas em testes e formatação.

## Continuidade e falhas

A coleta é agendada com relógio monotônico, sem acumular atrasos indefinidamente. Se uma iteração ultrapassa o próximo prazo, o coletor agenda uma nova amostra em vez de executar um lote para “compensar” leituras perdidas. As escritas seriais têm timeout; as tentativas de reconexão não acrescentam sleeps ao ciclo. A captura é síncrona e faz flush por amostra; disco muito lento ainda pode atrasar a coleta.

Após uma lacuna longa não há evidência de CPU continuamente alta. O alerta reinicia sua contagem. Se o contador de rede regressar, a taxa daquele período é zero. As duas decisões evitam converter descontinuidade em informação enganosa.

A captura abre com modo exclusivo (`xb`). A saída nunca substitui uma sessão anterior. O encerramento normal ou por Ctrl+C fecha os arquivos e a porta via `ExitStack`. Falhas de coleta encerram com código diferente de zero e mensagem legível.

## Escopo

O objetivo é observar uso de recursos. Percentual alto não identifica sozinho gargalo, vazamento ou causa de travamento. Comparar duas capturas exige considerar tarefa, máquina, intervalo e aplicações concorrentes. A página destaca lacunas e diferencia exemplo sintético de arquivo carregado.

Um monitor USB não é uma categoria inédita; há projetos maduros como [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python). Aqui o recorte é uma base pequena para ESP32, protocolo inspecionável e captura local que também funciona sem o painel.
