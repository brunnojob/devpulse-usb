# Protocolo v1

USB serial a 115200 baud. Um objeto JSON ASCII por linha, terminado em LF (`0x0a`). Até **255 bytes por objeto**, sem contar o LF. O agente começa cada conexão com um LF para encerrar eventual linha parcial anterior.

```json
{"v":1,"cpu":31.2,"ram":58.0,"disk":44.0,"rx":22.4,"tx":3.1,"alert":"OK","t":1.002}
```

| Campo | Significado | Limite |
| --- | --- | --- |
| `v` | Versão, inteiro | `1` |
| `cpu` | CPU total, % | 0–100 |
| `ram` | Memória usada conforme psutil, % | 0–100 |
| `disk` | Ocupação do volume escolhido, % | 0–100 |
| `rx`, `tx` | Taxa agregada de rede, KiB/s | 0–10¹² |
| `alert` | Estado calculado pelo agente | `OK`, `CPU`, `RAM`, `CPU+RAM` |
| `t` | Segundos desde o início do coletor, relógio monotônico | 0–10¹² |

`t` é usado na gravação e na bancada; o firmware não o utiliza e também aceita pacotes v1 anteriores sem esse campo. A bancada exige `t`, numérico e estritamente crescente. Isso impede misturar reinícios do agente no mesmo arquivo sem perceber. Os demais campos acima são obrigatórios em ambos os lados. Campos adicionais são ignorados pelo firmware e pelo leitor web.

## Enquadramento

`LineFramer.h` recebe bytes incrementalmente. Ignora CR, permitindo CRLF; aceita LF como separador. Uma linha longa é descartada até o próximo LF. O buffer é fixo e termina em NUL; a validação JSON recebe também seu comprimento. Não há alocação para acumular a linha. O ArduinoJson usa seu próprio documento de parsing limitado pelo comprimento recebido e pela profundidade configurada.

O firmware verifica versão, percentuais finitos, taxas não negativas e estado de alerta conhecido. Linhas rejeitadas não atualizam o relógio de validade da tela. O processamento serial tem orçamento de bytes por iteração para permitir verificar o estado desatualizado mesmo com entrada contínua.

## Serial e reconexão

A porta é explícita. `--list` enumera sem abrir dispositivos. O timeout de escrita é 200 ms por chamada; não existe espera ocupada. As tentativas de abrir a porta seguem esperas de 1, 2, 4 e no máximo 8 segundos, sem inserir sleeps de reconexão no coletor. Se uma escrita for parcial, a conexão é fechada e a próxima começa com LF.

Não há handshake, ACK, número de sequência ou garantia de entrega. “Escrita retomada” significa que o sistema aceitou os bytes; não prova que a tela os exibiu. Placas que reiniciam ao abrir a porta podem perder os primeiros pacotes. O agente envia a amostra atual nas tentativas seguintes; não mantém fila de amostras antigas para o display.

## Alertas e amostragem

- Limiar inclusivo de 90%; duração de dez segundos por relógio monotônico.
- Uma amostra abaixo do limiar limpa o alerta imediatamente.
- Intervalos maiores que três segundos ou relógio regressivo reiniciam a contagem.
- Não é possível comprovar o uso entre amostras: “sustentado” se refere à sequência observada.
- A taxa de rede usa a diferença de contadores dividida pelo tempo efetivamente decorrido. Reset de contador não produz taxa negativa. Ausência de contadores produz zero nesta versão, sem distinguir indisponibilidade de ausência de tráfego.

## Análise web

Até dois arquivos, com no máximo 4 MiB e 20.000 amostras cada. Todo o parsing ocorre no navegador. A aplicação não usa fetch, analytics ou endpoint de upload. Ao recarregar a página, as sessões carregadas são perdidas.

As curvas são alinhadas pela primeira amostra de cada sessão e usam segundos reais no mesmo eixo. A duração exclui o período anterior à primeira amostra. A média de CPU usa a integral trapezoidal entre amostras dividida pela duração; uma sessão com apenas uma leitura usa esse valor como média. Intervalos acima de três segundos são sinalizados. Há interpolação entre pontos, inclusive lacunas: não use uma captura interrompida para afirmar uso contínuo.

A diferença `B − A` usa pontos percentuais para percentuais e segundos para duração. Contagem de amostras em alerta depende do intervalo de coleta; não equivale à duração do alerta.
