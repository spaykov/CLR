from clr.core.safety import is_safety_critical


def test_detects_evacuation():
    assert is_safety_critical("Everybody needs to leave the building right now")
    assert is_safety_critical("Please evacuate the premises immediately.")


def test_detects_other_emergency_phrases():
    assert is_safety_critical("There is a gas leak on the 3rd floor")
    assert is_safety_critical("This is a life-threatening situation, call 911")
    assert is_safety_critical("Office is on lockdown until further notice")


def test_ignores_routine_messages():
    assert not is_safety_critical("Please review the attached quarterly report")
    assert not is_safety_critical("Reminder: team lunch at noon")
    assert not is_safety_critical("50% OFF TODAY ONLY!!!")