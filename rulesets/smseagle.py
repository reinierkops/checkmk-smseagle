#!/usr/bin/env python3

from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    Float,
    InputHint,
    LevelDirection,
    migrate_to_float_simple_levels,
    Percentage,
    SimpleLevels,
    String,
)
from cmk.rulesets.v1.rule_specs import CheckParameters, HostAndItemCondition, Topic


def _gsm_parameter_form() -> Dictionary:
    return Dictionary(
        elements={
            "signal_levels": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Lower levels for GSM signal strength"),
                    form_spec_template=Percentage(),
                    level_direction=LevelDirection.LOWER,
                    migrate=migrate_to_float_simple_levels,
                    prefill_fixed_levels=InputHint((20.0, 10.0)),
                ),
            ),
        },
    )


rule_spec_smseagle_gsm = CheckParameters(
    name="smseagle_gsm",
    title=Title("SMSEagle GSM modem"),
    topic=Topic.SERVER_HARDWARE,
    parameter_form=_gsm_parameter_form,
    condition=HostAndItemCondition(
        item_title=Title("Modem index"),
        item_form=String(),
    ),
)


def _environment_parameter_form() -> Dictionary:
    return Dictionary(
        elements={
            "temperature_levels": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Upper levels for temperature"),
                    form_spec_template=Float(unit_symbol="°C"),
                    level_direction=LevelDirection.UPPER,
                    migrate=migrate_to_float_simple_levels,
                    prefill_fixed_levels=InputHint((40.0, 50.0)),
                ),
            ),
            "humidity_levels": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Upper levels for humidity"),
                    form_spec_template=Percentage(),
                    level_direction=LevelDirection.UPPER,
                    migrate=migrate_to_float_simple_levels,
                    prefill_fixed_levels=InputHint((70.0, 85.0)),
                ),
            ),
        },
    )


rule_spec_smseagle_environment = CheckParameters(
    name="smseagle_environment",
    title=Title("SMSEagle environment sensors"),
    topic=Topic.SERVER_HARDWARE,
    parameter_form=_environment_parameter_form,
    condition=HostAndItemCondition(
        item_title=Title("Sensor name"),
        item_form=String(
            help_text=Help(
                "Use the exact service item such as Temp, Temp1, Temp2, or Humidity."
            ),
        ),
    ),
)
