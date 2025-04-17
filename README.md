# ESPHome Cocktail Machine

A simple [ESPHome](https://esphome.io) based cocktail machine.

## Parts I am using
- ESP32
- 20x4 LCD with PCF8574
- Rotary encoder
- PN532 [AliExpress](https://www.aliexpress.com/item/1005008711010897.html)
- Peristaltic pumps [AliExpress](https://www.aliexpress.com/item/1005006054669302.html)

## Usage
Only modify the python script!

1. Specify the GPIO pins, and their purposes. 
2. Specify the cocktails you want to make available.
3. Run the `run.sh` script, it will generate the `esphome-config.yaml` file, which contains the configuration.
4. Upload the generated configuration to your device.

## Limitations
- ESPHome's [menu system](https://esphome.io/components/display_menu/) currently does not support dynamic generation of menu items, and also does not support marking an item inactive, therefore, in some places, empty (and also unrelevant) items can be seen.

## TODOs
- Add a card reader (and writer): *Write customized coctails to an NFC card (using NDEF messages) so cocktails can be quickly made using the card.* - **In progress, waiting for the PN532 to arrive**
- Add some basic web portal: *Add a simple web portal that administrations can use to access inner-states of the device (variables, configuration, etc...). The device should broadcast it's ap, and should not connect to any network. OTA upgrades may be possible using this web interface.*
- Implement PWM based pumping: *While pumping ingredients, it's best to start and stop all the pumps at once. This will make sure the blending is perfect. PWM can be used to slow pumps down that requires less runtime.*