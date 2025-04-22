import yaml
import re

SDA_PIN = "GPIO21"
SCL_PIN = "GPIO22"
ENCODER_DT_PIN = "GPIO35"
ENCODER_CLK_PIN = "GPIO14"
SW_PIN = "GPIO34"
PUMPS = [
    {
        "pin": "GPIO19",
        "flowrate": 10,
    },
    {
        "pin": "GPIO18",
        "flowrate": 10,
    },
    {
        "pin": "GPIO17",
        "flowrate": 10,
    },
    {
        "pin": "GPIO16",
        "flowrate": 10,
    },
    {
        "pin": "GPIO13",
        "flowrate": 10,
    },
    {
        "pin": "GPIO27",
        "flowrate": 10,
    },
    {
        "pin": "GPIO32",
        "flowrate": 10,
    },
    {
        "pin": "GPIO33",
        "flowrate": 10,
    },
    {
        "pin": "GPIO25",
        "flowrate": 10,
    },
    {
        "pin": "GPIO26",
        "flowrate": 10,
    },
]
COCKTAILS = {
    "Mojito": {
        "ingredients": {
            "white rum": 40,
            "lime juice": 20,
            "sugar syrup": 40,
            "soda water": 100,
        }
    },
    "Margarita": {
        "ingredients": {
            "tequila": 40,
            "lime juice": 20,
            "triple sec": 20,
        }
    },
    "Pina Colada": {
        "ingredients": {
            "white rum": 40,
            "coconut cream": 30,
            "pineapple juice": 100,
        }
    },
    "Old Fashioned": {
        "ingredients": {
            "bourbon": 50,
            "sugar syrup": 10,
            "bitters": 2,
        }
    },
    "Cosmopolitan": {
        "ingredients": {
            "vodka": 40,
            "triple sec": 20,
            "lime juice": 20,
            "cranberry juice": 30,
        }
    },
}

nbrOfPumps = len(PUMPS)
ingredients = sorted({ingredient for c in COCKTAILS.values() for ingredient in c["ingredients"]})
COCKTAILS = dict(sorted(COCKTAILS.items()))

config = {
    "esphome": {
        "name": "cocktail-machine",
        "friendly_name": "Cocktail Machine",
    },
    "esp32": {
        "board": "esp32dev",
        "framework": {
            "type": "arduino",
        },
    },
    "logger": {},
    "json": {},
    "globals": [
        {
            "id": "error_message",
            "type": "std::string",
            "restore_value": False,
            "initial_value": "",
        }
    ],
    "output": [
        {
            "platform": "gpio",
            "id": "pump_" + str(i) + "_output",
            "pin": PUMPS[i]["pin"],
        } for i in range(nbrOfPumps)
    ],
    "i2c": {
        "sda": SDA_PIN,
        "scl": SCL_PIN,
        "id": "bus_a",
        "scan": True,
        "frequency": "800kHz",
    },
    "pn532_i2c": {
        "id": "card_reader",
        "update_interval": "1s",
        "on_tag": {
            "then": [
                {
                    "lambda": 
                        "if (!tag.has_ndef_message()) return;"
                        "auto message = tag.get_ndef_message();"
                        "auto records = message->get_records();"
                        "for (auto &record : records) {"
                            "std::string payload = record->get_payload();"
                            "size_t pos = payload.find(\"coctail:\");"
                            "if (pos != std::string::npos) {"
                                "ESP_LOGD(\"card_reader\", \"Found cocktail: %s\", payload.c_str());"
                                "json::parse_json(payload.substr(pos + 8), [](JsonObject root) -> bool {"
                                    "std::string name = root[\"name\"].as<std::string>();"
                                    "JsonArray ingredients = root[\"ingredients\"].as<JsonArray>();"
                                    "if (ingredients.size() == 0) {"
                                        "id(error)->execute(\"Invalid tag!\");"
                                        "return false;"
                                    "}"
                                    "id(clear_ingredients)->execute();" +
                                    "".join([
                                        "if (ingredients[" + str(i) + "] && ingredients[" + str(i) + "][\"name\"] && ingredients[" + str(i) + "][\"amount\"]) {"
                                            "std::string name = ingredients[" + str(i) + "][\"name\"].as<std::string>();"
                                            "int amount = ingredients[" + str(i) + "][\"amount\"].as<int>();"
                                            "if (!name.empty() && amount > 0) {"
                                                "id(ingredient_" + str(i) + "_name).state = name;"
                                                "id(ingredient_" + str(i) + "_name).state = amount;"
                                            "}"
                                        "}" 
                                        for i in range(nbrOfPumps)
                                    ]) +
                                    "id(make_cocktail)->execute();" +
                                "});"
                                "return;"
                            "}"
                        "}",
                },
            ],
        },
    },
    "display": [
        {
            "platform": "lcd_pcf8574",
            "id": "main_display",
            "dimensions": "20x4",
            "address": 0x27,
            "user_characters": [
                {
                    "position": 0,
                    "data": [
                        0b00100,
                        0b01000,
                        0b11110,
                        0b01001,
                        0b00101,
                        0b00001,
                        0b11110,
                        0b00000,
                    ],
                },
            ],
            "lambda": 
                "id(main_menu).draw();"
                "if (id(main_menu).is_active()) return;"

                "if (!id(error_message).empty()) { "
                    "it.print(0, 0, \"---==[ Error! ]==---\"); "
                    "it.print(0, 1, id(error_message).c_str()); "
                    "return;"
                "}"
                
                "it.print(0, 0, \"--------------------\");"
                "it.print(0, 3, \"--------------------\");"
                
                "if (id(make_cocktail).is_running()) { "
                    "it.print(0, 1, \"     Dispensing \");"
                    "it.print(0, 2, \" Do not remove cup!\");"
                "}"
                
                "if (id(write_card).is_running()) {"
                    "it.print(0, 1, \"      Writing\");"
                    "it.print(0, 2, \"  Do not remove it!\");"
                "}",
        },
    ],
    "sensor": [
        {
            "platform": "rotary_encoder",
            "id": "rotary_input",
            "pin_a": ENCODER_DT_PIN,
            "pin_b": ENCODER_CLK_PIN,
            "filters": [
                {
                    "debounce": "30ms",
                },
            ],
            "on_anticlockwise": [
                {
                    "display_menu.up": "main_menu",
                },
            ],
            "on_clockwise": [
                {
                    "display_menu.down": "main_menu",
                },
            ],
        }
    ],
    "binary_sensor": [
        {
            "platform": "gpio",
            "id": "switch_input",
            "pin": SW_PIN,
            "filters": [
                {
                    "delayed_on": "30ms",
                },
                {
                    "delayed_off": "30ms",
                },
            ],
            "on_press": [
                {
                    "display_menu.enter": "main_menu",
                },
            ],
        }
    ],
    "script": [
        {
            "id": "make_cocktail",
            "mode": "single",
            "then": [
                {
                    "display_menu.hide": {
                        "id": "main_menu",
                    },
                },
                {
                    "lambda": 
                        "std::string missingIngredients;" +
                        "".join([
                            "if (!id(ingredient_" + str(i) + "_name).state.empty()) {"
                                "if (!(" + " || ".join(["id(ingredient_" + str(i) + "_name).state == id(pump_" + str(n) + "_ingredient).state" for n in range(nbrOfPumps)]) + ")) {"
                                    "missingIngredients.append(\", \" + id(ingredient_" + str(i) + "_name).state);"
                                "}"
                            "}" for i in range(nbrOfPumps)
                        ]) +
                        "if (!missingIngredients.empty()) { "
                            "id(error)->execute(\"Missing: \" + missingIngredients.substr(2));"
                            "id(make_cocktail).stop();"
                        "}",
                },
                {
                    "lambda": 
                        "".join([
                            "if (!id(ingredient_" + str(i) + "_name).state.empty()) {"
                                "id(pump_ingredient)->execute(id(ingredient_" + str(i) + "_name).state, id(ingredient_" + str(i) + "_amount).state);"
                            "}" 
                            for i in range(nbrOfPumps)
                        ])
                },
            ] + [
                {
                    "wait_until": {
                        "condition": {
                            "lambda": "return id(run_pump_" + str(i) + ").is_running() == false;",
                        },
                    },
                } for i in range(nbrOfPumps)
            ] + [
                {
                    "script.execute": {
                        "id": "reset",
                    },
                },
            ],
        },
        {
            "id": "write_card",
            "mode": "single",
            "then": [
                {
                    "display_menu.hide": {
                        "id": "main_menu",
                    },
                },
                {
                    "lambda": 
                        "std::string data;" +
                        "".join([
                            "if (!id(ingredient_" + str(i) + "_name).state.empty() && id(ingredient_" + str(i) + "_amount).state > 0) {"
                                "data.append(\",{\\\"name\\\":\\\"\" + id(ingredient_" + str(i) + "_name).state + \"\\\",\\\"amount\\\":\" + to_string((int) id(ingredient_" + str(i) + "_amount).state) + \"}\");"
                            "}"
                            for i in range(nbrOfPumps)
                        ]) +
                        
                        "if (data.empty()) { "
                            "id(error)->execute(\"No ingredients to write!\");"
                            "id(write_card).stop();"
                        "}"
                        "if (data.length() > 255) { "
                            "id(error)->execute(\"Data too long!\"); "
                            "id(write_card).stop();"
                        "}"

                        "data = \"cocktail:{\\\"name\\\":\\\"Stored\\\",\\\"ingredients\\\":[\" + data.substr(1) + \"]}\";"
                        "ESP_LOGD(\"write_card\", \"Writing to card: %s\", data.c_str());"
                        
                        "auto message = new nfc::NdefMessage();"
                        "message->add_text_record(data);"       
                        "id(card_reader).write_mode(message);",
                },
                {
                    "wait_until": {
                        "condition": {
                            "lambda": "return id(card_reader).is_writing() == false;",
                        },
                    },
                },
                {
                    "script.execute": {
                        "id": "reset",
                    },
                },
            ],
        },
        {
            "id": "pump_ingredient",
            "mode": "parallel",
            "parameters": {
                "ingredient": "std::string",
                "amount": "int",
            },
            "then": [
                {
                    "lambda": 
                        "if (ingredient.empty() || amount <= 0) return;"
                        "int nbrOfIngredientPumps = 0;" +
                        "". join([
                            "if (id(pump_" + str(i) + "_ingredient).state == ingredient) {"
                                "nbrOfIngredientPumps++;"
                            "}"
                            for i in range(nbrOfPumps)
                        ]) +
                        "if (nbrOfIngredientPumps == 0) return;" +
                        "".join([
                            "if (id(pump_" + str(i) + "_ingredient).state == ingredient) {"
                                "id(run_pump_" + str(i) + ")->execute(amount / nbrOfIngredientPumps);"
                            "}"
                            for i in range(nbrOfPumps)
                        ]),
                },
            ],
        }
    ] + [
        {
            "id": "run_pump_" + str(i),
            "mode": "single",
            "parameters": {
                "amount": "float",
            },
            "then": [
                {
                    "if": {
                        "condition": {
                            "lambda": "return amount > 0;",
                        },
                        "then": [
                            {
                                "lambda": "ESP_LOGD(\"PUMP_" + str(i) + "\", \"Pumping %.2f ml\", amount);",
                            },
                            {
                                "output.turn_on": {
                                    "id": "pump_" + str(i) + "_output",
                                },
                            },
                            {
                                "delay": "!lambda \"return amount / id(pump_" + str(i) + "_flowrate).state * 1000;\"",
                            },
                            {
                                "output.turn_off": {
                                    "id": "pump_" + str(i) + "_output",
                                },
                            },
                        ],
                    },
                },
            ],
        } for i in range(nbrOfPumps)
    ] + [
        {
            "id": "clear_ingredients",
            "mode": "single",
            "then": [
                {
                    "text.set": {
                        "id": "ingredient_" + str(i) + "_name",
                        "value": "",
                    },
                } for i in range(nbrOfPumps)
            ] + [
                {
                    "number.set": {
                        "id": "ingredient_" + str(i) + "_amount",
                        "value": 0,
                    },
                } for i in range(nbrOfPumps)
            ],
        },
        {
            "id": "error",
            "mode": "single",
            "parameters": {
                "message": "std::string",
            },
            "then": [
                {
                    "globals.set": {
                        "id": "error_message",
                        "value": "!lambda \"return message;\"",
                    },
                },
                {
                    "display_menu.hide": {
                        "id": "main_menu",
                    },
                },
                {
                    "delay": "3s",
                },
                {
                    "script.execute": {
                        "id": "reset",
                    },
                },
            ],
        },
        {
            "id": "reset",
            "mode": "single",
            "then": [
                {
                    "lambda": "id(error_message).clear();",
                },
                {
                    "script.execute": {
                        "id": "clear_ingredients",
                    },
                },
                {
                    "display_menu.show_main": {
                        "id": "main_menu",
                    },
                },
                {
                    "display_menu.show": {
                        "id": "main_menu",
                    },
                },
                {
                    "script.wait": {
                        "id": "clear_ingredients",
                    },
                },
            ],
        },
    ],
    "select": [
        {
            "platform": "template",
            "id": "pump_" + str(i) + "_ingredient",
            "optimistic": True,
            "options": [""] + ingredients,
            "initial_option": "",
            "restore_value": True,
        } for i in range(nbrOfPumps)
    ],
    "text": [
        {
            "platform": "template",
            "id": "ingredient_" + str(i) + "_name",
            "mode": "text",
            "optimistic": True,
            "initial_value": "",
            "restore_value": False,
            "internal": True,
        } for i in range(nbrOfPumps)
    ],
    "number": [
        {
            "platform": "template",
            "id": "pump_" + str(i) + "_flowrate",
            "optimistic": True,
            "min_value": 1,
            "max_value": 100,
            "step": 1,
            "initial_value": PUMPS[i]["flowrate"],
            "restore_value": True,
            "unit_of_measurement": "ml/s",
            "device_class": "volume_flow_rate",
        } for i in range(nbrOfPumps)
    ] + [
        {
            "platform": "template",
            "id": "ingredient_" + str(i) + "_amount",
            "optimistic": True,
            "min_value": 0,
            "max_value": 100,
            "step": 1,
            "initial_value": 0,
            "restore_value": False,
            "unit_of_measurement": "ml",
            "device_class": "volume",
            "internal": True,
        } for i in range(nbrOfPumps)
    ],
    "lcd_menu": {
        "id": "main_menu",
        "display_id": "main_display",
        "active": True,
        "mode": "rotary",
        "mark_back": 0x08,
        "mark_selected": 0x3e,
        "mark_editing": 0x2a,
        "mark_submenu": 0x7e,
        "items": [
            {
                "type": "menu",
                "text": "Cocktails",
                "items": [
                    {
                        "type": "back",
                        "text": "Back",
                    },
                ] + [
                    {
                        "type": "menu",
                        "text": name,
                        "items": [
                            {
                                "type": "back",
                                "text": "Back",
                            },
                            {
                                "type": "command",
                                "text": "Make",
                                "on_value": {
                                    "then": [
                                        {
                                            "script.execute": {
                                                "id": "make_cocktail",
                                            },
                                        },
                                    ],
                                },
                            },
                            {
                                "type": "command",
                                "text": "Write to Card",
                                "on_value": {
                                    "then": [
                                        {
                                            "script.execute": {
                                                "id": "write_card",
                                            },
                                        },
                                    ],
                                },
                            },
                            {
                                "type": "label",
                                "text": "-=[ Personalize ]=",
                            },
                        ] + [
                            {
                                "type": "number",
                                "text": ingredient,
                                "format": "%.0f",
                                "number": "ingredient_" + str(i) + "_amount",
                            } for i, ingredient in enumerate(data['ingredients'].keys())
                        ],
                        "on_enter": {
                            "then": [
                                {
                                    "script.execute": {
                                        "id": "clear_ingredients",
                                    },
                                },
                                {
                                    "script.wait": {
                                        "id": "clear_ingredients",
                                    },
                                },
                            ] + [
                                {
                                    "text.set": {
                                        "id": "ingredient_" + str(i) + "_name",
                                        "value": ingredient,
                                    },
                                } for i, ingredient in enumerate(data['ingredients'].keys())
                             ] + [
                                 {
                                    "number.set": {
                                        "id": "ingredient_" + str(i) + "_amount",
                                        "value": amount,
                                    }
                                } for i, amount in enumerate(data['ingredients'].values())
                            ]
                        },
                    } for name, data in COCKTAILS.items()
                ],
            },
            {
                "type": "menu",
                "text": "Singles",
                "items": [
                    {
                        "type": "back",
                        "text": "Back",
                    },
                ] + [
                    {
                        "type": "menu",
                        "text": "!lambda \"return id(pump_" + str(i) + "_ingredient).state;\"",
                        "items": [
                            {
                                "type": "back",
                                "text": "Back",
                            },
                            {
                                "type": "command",
                                "text": "Dispense",
                                "on_value": {
                                    "then": [
                                        {
                                            "script.execute": {
                                                "id": "make_cocktail",
                                            },
                                        },
                                    ],
                                },
                            },
                            {
                                "type": "number",
                                "text": "Amount [ml]",
                                "format": "%.0f",
                                "number": "ingredient_0_amount",
                            },
                            {
                                "type": "command",
                                "text": "Write to Card",
                                "on_value": {
                                    "then": [
                                        {
                                            "script.execute": {
                                                "id": "write_card",
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                        "on_enter": {
                            "then": [
                                {
                                    "script.execute": {
                                        "id": "clear_ingredients",
                                    },
                                },
                                {
                                    "script.wait": {
                                        "id": "clear_ingredients",
                                    },
                                },
                                {
                                    "text.set": {
                                        "id": "ingredient_0_name",
                                        "value": "!lambda \"return id(pump_" + str(i) + "_ingredient).state;\"",
                                    },
                                },
                                {
                                    "number.set": {
                                        "id": "ingredient_0_amount",
                                        "value": 20,
                                    }
                                }
                            ]
                        },
                    } for i in range(nbrOfPumps)
                ],
            },
            {
                "type": "menu",
                "text": "Settings",
                "items": [
                    {
                        "type": "back",
                        "text": "Back",
                    },
                    {
                        "type": "menu",
                        "text": "Pump config",
                        "items": [
                            {
                                "type": "back",
                                "text": "Back",
                            }
                        ] + [{
                                "type": "menu",
                                "text": "Pump #" + str(i + 1),
                                "items": [
                                    {
                                        "type": "back",
                                        "text": "Back",
                                    },
                                    {
                                        "type": "select",
                                        "text": "Ingredient",
                                        "immediate_edit": False,
                                        "select": "pump_" + str(i) + "_ingredient",
                                    },
                                    {
                                        "type": "number",
                                        "text": "Flow [ml/s]",
                                        "format": "%.0f",
                                        "number": "pump_" + str(i) + "_flowrate",
                                    },
                                    {
                                        "type": "command",
                                        "text": "Prime",
                                        "on_value": {
                                            "then": [
                                                {
                                                    "script.execute": {
                                                        "id": "run_pump_" + str(i),
                                                        "amount": 50,
                                                    },
                                                },
                                            ],
                                        },
                                    }
                                ],
                            } for i in range(nbrOfPumps)
                        ],
                    },
                    {
                        "type": "label",
                        "text": "Factory Reset (TODO)",
                    },
                ],
            }
        ],
    },
}

contents = yaml.safe_dump(config, default_flow_style=False, sort_keys=False, width=float("inf"))

contents = re.sub(r"\'\!lambda\s(.*)\'", r'!lambda \1', contents)

print(contents)
