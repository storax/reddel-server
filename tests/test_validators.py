"""Tests for the validators module"""
import pytest
import redbaron

import reddel_server

DEF_SRC = """def foo(bar):
    spam = bar + 1
    return spam
"""

DEF_SRC2 = DEF_SRC + """
def foo2(bar):
	pass
"""

@pytest.mark.parametrize('identifiers,single,src,valid', [
    [['def', 'defnode'], True, DEF_SRC, True],
    [['def', 'defnode'], True, DEF_SRC2, False],
    [['name'], True, DEF_SRC, False],
    [['def'], False, DEF_SRC2, True]
])
def test_barontype_call(identifiers, single, src, valid):
    val = reddel_server.BaronTypeValidator(identifiers, single=single)
    red = redbaron.RedBaron(src)
    if valid:
        val(red)
    else:
        with pytest.raises(reddel_server.ValidationException):
            val(red)

def test_barontype_transform_single():
    val = reddel_server.BaronTypeValidator((), single=True)
    red = redbaron.RedBaron(DEF_SRC)
    transformed = val.transform(red)
    assert transformed is red[0]

def test_barontype_transform_singleOff():
    val = reddel_server.BaronTypeValidator((), single=False)
    red = redbaron.RedBaron(DEF_SRC)
    transformed = val.transform(red)
    assert transformed is red
