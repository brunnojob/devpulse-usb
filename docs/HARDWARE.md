# Configuração do hardware

A foto fornecida identifica um ESP32-C6 pelo texto da tela. Ela não determina o fabricante da placa, controlador, ligações, dimensões ou offsets do painel. Não grave o firmware usando pinos presumidos a partir da aparência.

## Perfil incluído

O sketch usa Adafruit ST7789 sobre SPI. É necessário **confirmar esse controlador**. Se a sua tela usa outro chip, substitua o driver e a inicialização conforme a documentação do fabricante.

`BOARD_CONFIGURED=0` bloqueia a compilação por padrão. Isso evita produzir um firmware aparentemente pronto para uma placa ainda não identificada.

1. Obtenha o esquema ou o exemplo `.ino` que já funciona na sua placa.
2. Instale Arduino-ESP32 da Espressif e selecione a placa correspondente na Arduino IDE.
3. Instale ArduinoJson 7, Adafruit GFX Library e Adafruit ST7735 and ST7789 Library.
4. Abra `firmware/DevPulse/DevPulse.ino`.
5. Preencha o perfil abaixo conforme o esquema.
6. Ajuste eventuais offsets do painel e sua inicialização de acordo com o fabricante.
7. Só depois altere `BOARD_CONFIGURED` para `1`.
8. Compile e grave. Feche o Monitor Serial antes de abrir o agente.

| Parâmetro | Verificar |
| --- | --- |
| `LCD_MOSI`, `LCD_SCLK` | Pinos de dados e relógio SPI |
| `LCD_CS`, `LCD_DC`, `LCD_RST` | Seleção, comando/dados e reset |
| `LCD_BL`, `LCD_BL_ACTIVE` | Backlight e polaridade; `-1` se não controlado |
| `LCD_WIDTH`, `LCD_HEIGHT` | Dimensões nativas na inicialização do driver |
| `LCD_ROTATION` | Orientação horizontal; área útil mínima 240 × 160 |

Os valores **172 × 320 / rotação 1 são placeholders**, não uma identificação da tela da foto. Alguns painéis exigem offsets específicos além dessas dimensões.

## Compilação de verificação

O CI usa core ESP32 3.3.2, ArduinoJson 7.4.2 e Adafruit ST7735/ST7789 1.11.0. `tools/check_firmware.py` cria uma cópia temporária com um perfil para o compilador. Os pinos desse teste não identificam uma placa suportada; não use esse perfil para gravação. O `board_config.h` original permanece bloqueado até a configuração física.

## Conexão USB

Para USB nativo do ESP32-C6, habilite **USB CDC On Boot**. Para uma ponte USB/UART, siga a configuração do fabricante e confira se drivers adicionais são necessários. Use cabo que transporte dados. Algumas placas reiniciam ao abrir a porta.

```sh
python agent.py --list
python agent.py --port COM5
```

No Linux, por exemplo, use `/dev/ttyACM0`; no macOS, use o caminho efetivamente listado. Acesso à porta pode depender de permissões do sistema. Não é necessário ligar o Wi-Fi da placa para este projeto.

## Verificação na bancada física

- Verifique se cores, orientação, backlight e limites da tela estão corretos.
- Confira leituras contra o monitor do sistema usando janelas de amostragem semelhantes.
- Gere uma carga controlada e observe o alerta após dez segundos no limiar.
- Encerre o agente: o display deve indicar dados desatualizados após cinco segundos.
- Retire e reconecte o cabo: o agente deve tentar recuperar a porta escolhida.
- Confira o consumo do agente e a legibilidade das taxas de rede com valores altos.

O desenho limpa a área de métricas em vez de apagar toda a tela a cada pacote. Isso reduz o trabalho de desenho, mas não comprova ausência de cintilação: é preciso observar o painel físico.

## Referências primárias

- [USB serial no ESP32-C6](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/get-started/establish-serial-connection.html)
- [USB CDC em Arduino-ESP32](https://github.com/espressif/arduino-esp32/blob/master/docs/en/tutorials/cdc_dfu_flash.rst)
- [Adafruit ST7735/ST7789](https://github.com/adafruit/Adafruit-ST7735-Library)
- [ArduinoJson 7](https://arduinojson.org/v7/api/json/deserializejson/)
