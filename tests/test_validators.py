"""Tests for the validators module"""
import pytest
import redbaron

import reddel_server


def test_OptionalRegionValidator_call():
    """Test that it's valid to not specify a region"""
    testsrc = redbaron.RedBaron("1+1")
    validator = reddel_server.OptionalRegionValidator()
    validator(testsrc)


def test_OptionalRegionValidator_transform_region():
    """Test that the region is extracted when specified"""
    testsrc = redbaron.RedBaron("a=1+1\nb=5")
    start = reddel_server.Position(1, 1)
    end = reddel_server.Position(1, 4)
    validator = reddel_server.OptionalRegionValidator()
    result = validator.transform(testsrc, start, end)
    expected = (testsrc[0], reddel_server.Position(1, 1), reddel_server.Position(1, 5))
    assert expected == result, "Expected that the region was extracted and the bounding box was updated."


def test_OptionalRegionValidator_transform_no_region():
    """Test that there is no tranformation without any region"""
    testsrc = redbaron.RedBaron("a=1+1\nb=5")
    validator = reddel_server.OptionalRegionValidator()
    result = validator.transform(testsrc)
    expected = (testsrc, None, None)
    assert expected == result


def test_MandatoryRegionValidator_no_region():
    """Test that the validator raises without a region"""
    testsrc = redbaron.RedBaron("1+1")
    validator = reddel_server.MandatoryRegionValidator()
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc, start=(1, 1), end=None)


def test_MandatoryRegionValidator_region():
    """Test that there has to be a region"""
    testsrc = redbaron.RedBaron("1+1")
    validator = reddel_server.MandatoryRegionValidator()
    validator(testsrc, start=reddel_server.Position(1, 1), end=reddel_server.Position(1, 3))


def test_SingleNodeValidator_no_region_invalid():
    """Test that the validator raises when there is more than one node and no region"""
    testsrc = redbaron.RedBaron("1+1\n2+2")
    validator = reddel_server.SingleNodeValidator()
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc)


def test_SingleNodeValidator_no_region_valid():
    """Test that the validator does not raise when there is one node and no region"""
    testsrc = redbaron.RedBaron("1+1")
    validator = reddel_server.SingleNodeValidator()
    validator(testsrc)


def test_SingleNodeValidator_no_region_single_node_valid():
    """Test that the validator does not raise when there is one node and no region"""
    testsrc = redbaron.RedBaron("for i in range(10):\n\ta=1\n\tb=2")[0]
    validator = reddel_server.SingleNodeValidator()
    validator(testsrc)


def test_SingleNodeValidator_region_invalid():
    """Test that the validator raises when there is more than one node in the region"""
    testsrc = redbaron.RedBaron("1+1\n2+2")
    validator = reddel_server.SingleNodeValidator()
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc, start=reddel_server.Position(1, 1), end=reddel_server.Position(2, 3))


def test_SingleNodeValidator_region_valid():
    """Test that the validator does not raise when there is one node in the region"""
    testsrc = redbaron.RedBaron("1+1\n2+2")
    validator = reddel_server.SingleNodeValidator()
    validator(testsrc, start=reddel_server.Position(2, 1), end=reddel_server.Position(2, 3))


def test_SingleNodeValidator_transform_no_region_no_list():
    """Test that there is no transformation if there is no list"""
    testsrc = redbaron.RedBaron("1+1")[0]
    validator = reddel_server.SingleNodeValidator()
    assert (testsrc, None, None) == validator.transform(testsrc, start=None, end=None)


def test_SingleNodeValidator_transform_region_no_list():
    """Test that there is no transformation if there is a region"""
    testsrc = redbaron.RedBaron("1+1")
    validator = reddel_server.SingleNodeValidator()
    expected = (testsrc, (1, 1), (1, 3))
    assert expected == validator.transform(testsrc, start=reddel_server.Position(1, 1),
                                           end=reddel_server.Position(1, 3))


def test_SingleNodeValidator_transform_no_region_list():
    """Test the transformation when there is no region"""
    testsrc = redbaron.RedBaron("1+1")
    validator = reddel_server.SingleNodeValidator()
    expected = "1+1"
    assert expected == validator.transform(testsrc)[0].dumps()


def test_TypeValidator_valid_no_region_no_list():
    """Test a valid source that is not a list without a region"""
    testsrc = redbaron.RedBaron("def foo(): pass")[0]
    validator = reddel_server.TypeValidator(['def'])
    validator(testsrc)


def test_TypeValidator_valid_no_region_list():
    """Test a valid source that is a list without a region"""
    testsrc = redbaron.RedBaron("def foo(): pass\ndef bar(): pass")
    validator = reddel_server.TypeValidator(['def'])
    validator(testsrc)


def test_TypeValidator_valid_region_list():
    """Test a valid source that is a list with a region"""
    testsrc = redbaron.RedBaron("a=1\ndef foo(): pass\ndef bar(): pass")
    validator = reddel_server.TypeValidator(['def'])
    validator(testsrc, start=reddel_server.Position(2, 1), end=reddel_server.Position(3, 1))


def test_TypeValidator_valid_region_no_list():
    """Test a valid source where the region specifies a single node"""
    testsrc = redbaron.RedBaron("a=1\ndef foo(): pass\nb=2")
    validator = reddel_server.TypeValidator(['def'])
    validator(testsrc, start=reddel_server.Position(2, 1), end=reddel_server.Position(2, 1))


def test_TypeValidator_invalid_no_region_no_list():
    """Test that the validator raises for invalid sources without a region and list"""
    testsrc = redbaron.RedBaron("1+1")[0]
    validator = reddel_server.TypeValidator(['def'])
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc)


def test_TypeValidator_invalid_no_region_list():
    """Test that the validator raises for invalid sources without a region but a list"""
    testsrc = redbaron.RedBaron("def foo(): pass\na=1")
    validator = reddel_server.TypeValidator(['def'])
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc)


def test_TypeValidator_invalid_region_list():
    """Test that the validator raises for invalid sources with a region and list"""
    testsrc = redbaron.RedBaron("def foo():\n\ta=1\n\tdef bar(): pass")
    validator = reddel_server.TypeValidator(['def'])
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc, start=reddel_server.Position(2, 3), end=reddel_server.Position(3, 3))


def test_TypeValidator_invalid_region_no_list():
    """Test that the validator raises for invalid sources with a region and no list"""
    testsrc = redbaron.RedBaron("def foo():\n\ta=1")
    validator = reddel_server.TypeValidator(['def'])
    with pytest.raises(reddel_server.ValidationException):
        validator(testsrc, start=reddel_server.Position(2, 3), end=reddel_server.Position(2, 4))
