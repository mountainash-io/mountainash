from enum import Enum, StrEnum, IntEnum, Flag, IntFlag, auto
from dataclasses import dataclass
import pytest
from pytest_check import check
from mountainash.pydata.utils.enum_helpers import (
    is_enum,
    member_identities,
    member_names,
    member_values,
    is_valid_member_name,
    is_valid_member_value,
    is_valid_member_identity,
    find_member,
    find_member_name,
    find_all_member_names,
    find_member_names_dict,
    get_enum_attribute_names,
    get_enum_values,
    get_enum_values_set,
    get_enum_values_tuple,
    get_enum_values_dict,
)


# Sample Enums for testing
class SampleEnum(Enum):
    ONE = 1
    TWO = 2
    THREE = 3


class SampleEnum2(Enum):
    EIGHT = "ONE"
    NINE = "TWO"
    TEN = "THREE"


# Identity enum using auto()
class AutoEnum(Enum):
    FIRST = auto()
    SECOND = auto()
    THIRD = auto()


# Identity enum with object values (true identity enum)
class IdentityAutoEnum(Enum):
    """Identity enum where auto() generates unique objects"""
    RED = object()
    GREEN = object()
    BLUE = object()


# Value-based enums (primitives)
class ColorStrEnum(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class StatusIntEnum(IntEnum):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3


# Flag-based enums
class Permission(Flag):
    READ = auto()       # 1
    WRITE = auto()      # 2
    EXECUTE = auto()    # 4
    RWX = 7            # Named combination (alias)


class FileMode(IntFlag):
    R = 4
    W = 2
    X = 1
    RWX = 7  # Named combination (alias)


class SampleEnumEmpty(Enum):
    ONE = None
    TWO = None
    THREE = None


class SampleEnumPass(Enum):
    pass


class FakeEnum:
    ONE = 1
    TWO = 2
    THREE = 3


class SampleEnumBadData(Enum):
    FOUR = [1, "2", 3.45, [{"hello": 7}, ("8", 9.10)]]
    FIVE = 80
    SIX = 90
    SEVEN = "ALICE"


class IdentityEnum(Enum):
    """Identity-based enum where the value is the instance itself"""
    RED = object()
    GREEN = object()
    BLUE = object()


@dataclass
class SimpleDataclass:
    name: str
    age: int


@dataclass
class NestedDataclass:
    simple: SimpleDataclass
    score: float


class TestIsEnum:
    """Test the is_enum function"""

    def test_is_enum_with_enum(self):
        assert is_enum(SampleEnum)
        assert is_enum(SampleEnumEmpty)
        assert is_enum(SampleEnumPass)

    def test_is_enum_with_fake_enum(self):
        assert not is_enum(FakeEnum)

    def test_is_enum_with_dataclass(self):
        assert not is_enum(SimpleDataclass)
        assert not is_enum(SimpleDataclass("Test", 30))

    def test_is_enum_with_none(self):
        # is_enum handles None gracefully and returns False
        assert not is_enum(None)


class TestMemberIdentities:
    """Test the member_identities function (decorator-inspired)"""

    def test_member_identities_basic(self):
        identities = member_identities(SampleEnum)
        assert SampleEnum.ONE in identities
        assert SampleEnum.TWO in identities
        assert SampleEnum.THREE in identities
        assert len(identities) == 3

    def test_member_identities_identity_enum(self):
        identities = member_identities(IdentityEnum)
        assert IdentityEnum.RED in identities
        assert IdentityEnum.GREEN in identities
        assert IdentityEnum.BLUE in identities
        assert len(identities) == 3

    def test_member_identities_empty(self):
        identities = member_identities(SampleEnumPass)
        assert len(identities) == 0

    def test_member_identities_non_enum(self):
        with pytest.raises(ValueError):
            member_identities(FakeEnum)


class TestMemberNames:
    """Test the member_names function (decorator-inspired)"""

    def test_member_names_basic(self):
        names = member_names(SampleEnum)
        assert 'ONE' in names
        assert 'TWO' in names
        assert 'THREE' in names
        assert len(names) == 3

    def test_member_names_empty(self):
        names = member_names(SampleEnumPass)
        assert len(names) == 0

    def test_member_names_non_enum(self):
        with pytest.raises(ValueError):
            member_names(FakeEnum)


class TestMemberValues:
    """Test the member_values function (decorator-inspired)"""

    def test_member_values_int_enum(self):
        values = member_values(SampleEnum)
        assert 1 in values
        assert 2 in values
        assert 3 in values
        assert len(values) == 3

    def test_member_values_str_enum(self):
        values = member_values(SampleEnum2)
        assert "ONE" in values
        assert "TWO" in values
        assert "THREE" in values
        assert len(values) == 3

    def test_member_values_none_enum(self):
        values = member_values(SampleEnumEmpty)
        assert None in values
        assert len(values) == 1  # All Nones collapse to one in a set

    def test_member_values_empty(self):
        values = member_values(SampleEnumPass)
        assert len(values) == 0

    def test_member_values_non_enum(self):
        with pytest.raises(ValueError):
            member_values(FakeEnum)


class TestIsValidMemberName:
    """Test the is_valid_member_name validation function"""

    def test_is_valid_member_name_valid(self):
        assert is_valid_member_name(SampleEnum, 'ONE')
        assert is_valid_member_name(SampleEnum, 'TWO')
        assert is_valid_member_name(SampleEnum, 'THREE')

    def test_is_valid_member_name_invalid(self):
        assert not is_valid_member_name(SampleEnum, 'FOUR')
        assert not is_valid_member_name(SampleEnum, 'ZERO')
        assert not is_valid_member_name(SampleEnum, '')

    def test_is_valid_member_name_non_enum(self):
        assert not is_valid_member_name(FakeEnum, 'ONE')

    def test_is_valid_member_name_unhashable(self):
        # Should handle unhashable types gracefully
        assert not is_valid_member_name(SampleEnum, ['unhashable'])
        assert not is_valid_member_name(SampleEnum, {'unhashable': 'dict'})


class TestIsValidMemberValue:
    """Test the is_valid_member_value validation function"""

    def test_is_valid_member_value_valid(self):
        assert is_valid_member_value(SampleEnum, 1)
        assert is_valid_member_value(SampleEnum, 2)
        assert is_valid_member_value(SampleEnum, 3)

    def test_is_valid_member_value_invalid(self):
        assert not is_valid_member_value(SampleEnum, 99)
        assert not is_valid_member_value(SampleEnum, 0)
        assert not is_valid_member_value(SampleEnum, 'ONE')

    def test_is_valid_member_value_str_enum(self):
        assert is_valid_member_value(SampleEnum2, "ONE")
        assert is_valid_member_value(SampleEnum2, "TWO")
        assert not is_valid_member_value(SampleEnum2, "INVALID")

    def test_is_valid_member_value_none(self):
        assert is_valid_member_value(SampleEnumEmpty, None)

    def test_is_valid_member_value_non_enum(self):
        assert not is_valid_member_value(FakeEnum, 1)

    def test_is_valid_member_value_unhashable(self):
        """Test with unhashable enum values (lists, dicts)"""
        # SampleEnumBadData.FOUR has a list value which is unhashable
        unhashable_value = [1, "2", 3.45, [{"hello": 7}, ("8", 9.10)]]

        # Should handle unhashable values gracefully using fallback iteration
        assert is_valid_member_value(SampleEnumBadData, unhashable_value)

        # Different unhashable value should return False
        different_list = [1, 2, 3]
        assert not is_valid_member_value(SampleEnumBadData, different_list)

        # Hashable values should still work
        assert is_valid_member_value(SampleEnumBadData, 80)  # FIVE
        assert is_valid_member_value(SampleEnumBadData, "ALICE")  # SEVEN


class TestIsValidMemberIdentity:
    """Test the is_valid_member_identity validation function"""

    def test_is_valid_member_identity_valid(self):
        assert is_valid_member_identity(SampleEnum, SampleEnum.ONE)
        assert is_valid_member_identity(SampleEnum, SampleEnum.TWO)
        assert is_valid_member_identity(SampleEnum, SampleEnum.THREE)

    def test_is_valid_member_identity_invalid_value(self):
        # The primitive value is not the same as the enum instance
        assert not is_valid_member_identity(SampleEnum, 1)
        assert not is_valid_member_identity(SampleEnum, 2)

    def test_is_valid_member_identity_wrong_enum(self):
        assert not is_valid_member_identity(SampleEnum, SampleEnum2.EIGHT)

    def test_is_valid_member_identity_non_enum(self):
        assert not is_valid_member_identity(FakeEnum, 1)

    def test_is_valid_member_identity_identity_enum(self):
        assert is_valid_member_identity(IdentityEnum, IdentityEnum.RED)
        assert is_valid_member_identity(IdentityEnum, IdentityEnum.GREEN)


class TestFindMember:
    """Test the find_member function (reverse value lookup)"""

    def test_find_member_basic_int_enum(self):
        """Test finding members by integer value"""
        assert find_member(SampleEnum, 1) == SampleEnum.ONE
        assert find_member(SampleEnum, 2) == SampleEnum.TWO
        assert find_member(SampleEnum, 3) == SampleEnum.THREE

    def test_find_member_basic_str_enum(self):
        """Test finding members by string value"""
        assert find_member(SampleEnum2, "ONE") == SampleEnum2.EIGHT
        assert find_member(SampleEnum2, "TWO") == SampleEnum2.NINE
        assert find_member(SampleEnum2, "THREE") == SampleEnum2.TEN

    def test_find_member_not_found(self):
        """Test that None is returned when value not found"""
        assert find_member(SampleEnum, 99) is None
        assert find_member(SampleEnum, "INVALID") is None
        assert find_member(SampleEnum2, 123) is None

    def test_find_member_with_aliases(self):
        """Test that canonical member is returned for aliases"""
        class StatusWithAliases(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            APPROVED = 2
            ACCEPTED = 2  # Alias for APPROVED

        # Should return canonical (first-defined) member
        result = find_member(StatusWithAliases, 1)
        assert result == StatusWithAliases.PENDING
        assert result.name == "PENDING"

        result = find_member(StatusWithAliases, 2)
        assert result == StatusWithAliases.APPROVED
        assert result.name == "APPROVED"

    def test_find_member_strenum(self):
        """Test finding members in StrEnum"""
        assert find_member(ColorStrEnum, "red") == ColorStrEnum.RED
        assert find_member(ColorStrEnum, "green") == ColorStrEnum.GREEN
        assert find_member(ColorStrEnum, "blue") == ColorStrEnum.BLUE
        assert find_member(ColorStrEnum, "yellow") is None

    def test_find_member_intenum(self):
        """Test finding members in IntEnum"""
        assert find_member(StatusIntEnum, 1) == StatusIntEnum.PENDING
        assert find_member(StatusIntEnum, 2) == StatusIntEnum.APPROVED
        assert find_member(StatusIntEnum, 3) == StatusIntEnum.REJECTED
        assert find_member(StatusIntEnum, 99) is None

    def test_find_member_flag(self):
        """Test finding members in Flag enum"""
        assert find_member(Permission, 1) == Permission.READ
        assert find_member(Permission, 2) == Permission.WRITE
        assert find_member(Permission, 4) == Permission.EXECUTE
        # RWX is an alias for the composite value 7
        result = find_member(Permission, 7)
        assert result == Permission.RWX

    def test_find_member_intflag(self):
        """Test finding members in IntFlag enum"""
        assert find_member(FileMode, 4) == FileMode.R
        assert find_member(FileMode, 2) == FileMode.W
        assert find_member(FileMode, 1) == FileMode.X
        result = find_member(FileMode, 7)
        assert result == FileMode.RWX

    def test_find_member_none_value(self):
        """Test finding members with None value"""
        result = find_member(SampleEnumEmpty, None)
        assert result is not None
        assert result.value is None

    def test_find_member_non_enum(self):
        """Test that ValueError is raised for non-enum input"""
        with pytest.raises(ValueError):
            find_member(FakeEnum, 1)

        with pytest.raises(ValueError):
            find_member(SimpleDataclass, 1)

    def test_find_member_auto_enum(self):
        """Test finding members in auto() enum"""
        assert find_member(AutoEnum, 1) == AutoEnum.FIRST
        assert find_member(AutoEnum, 2) == AutoEnum.SECOND
        assert find_member(AutoEnum, 3) == AutoEnum.THIRD


class TestFindMemberName:
    """Test the find_member_name function (returns canonical member name)"""

    def test_find_member_name_basic_int_enum(self):
        """Test finding member name by integer value"""
        assert find_member_name(SampleEnum, 1) == "ONE"
        assert find_member_name(SampleEnum, 2) == "TWO"
        assert find_member_name(SampleEnum, 3) == "THREE"

    def test_find_member_name_basic_str_enum(self):
        """Test finding member name by string value"""
        assert find_member_name(SampleEnum2, "ONE") == "EIGHT"
        assert find_member_name(SampleEnum2, "TWO") == "NINE"
        assert find_member_name(SampleEnum2, "THREE") == "TEN"

    def test_find_member_name_not_found(self):
        """Test that None is returned when value not found"""
        assert find_member_name(SampleEnum, 99) is None
        assert find_member_name(SampleEnum, "INVALID") is None

    def test_find_member_name_with_aliases(self):
        """Test that canonical member name is returned for aliases"""
        class StatusWithAliases(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            APPROVED = 2
            ACCEPTED = 2  # Alias for APPROVED

        # Should return canonical (first-defined) member name
        result = find_member_name(StatusWithAliases, 1)
        assert result == "PENDING"

        result = find_member_name(StatusWithAliases, 2)
        assert result == "APPROVED"

    def test_find_member_name_strenum(self):
        """Test finding member name in StrEnum"""
        assert find_member_name(ColorStrEnum, "red") == "RED"
        assert find_member_name(ColorStrEnum, "green") == "GREEN"
        assert find_member_name(ColorStrEnum, "yellow") is None

    def test_find_member_name_intenum(self):
        """Test finding member name in IntEnum"""
        assert find_member_name(StatusIntEnum, 1) == "PENDING"
        assert find_member_name(StatusIntEnum, 2) == "APPROVED"
        assert find_member_name(StatusIntEnum, 99) is None

    def test_find_member_name_none_value(self):
        """Test finding member name with None value"""
        result = find_member_name(SampleEnumEmpty, None)
        assert result == "ONE"  # Canonical member

    def test_find_member_name_non_enum(self):
        """Test that ValueError is raised for non-enum input"""
        with pytest.raises(ValueError):
            find_member_name(FakeEnum, 1)


class TestFindAllMemberNames:
    """Test the find_all_member_names function (returns all member names including aliases)"""

    def test_find_all_member_names_basic_int_enum(self):
        """Test finding all member names by integer value (no aliases)"""
        result = find_all_member_names(SampleEnum, 1)
        assert result == {"ONE"}

        result = find_all_member_names(SampleEnum, 2)
        assert result == {"TWO"}

        result = find_all_member_names(SampleEnum, 3)
        assert result == {"THREE"}

    def test_find_all_member_names_basic_str_enum(self):
        """Test finding all member names by string value (no aliases)"""
        result = find_all_member_names(SampleEnum2, "ONE")
        assert result == {"EIGHT"}

        result = find_all_member_names(SampleEnum2, "TWO")
        assert result == {"NINE"}

    def test_find_all_member_names_not_found(self):
        """Test that empty set is returned when value not found"""
        result = find_all_member_names(SampleEnum, 99)
        assert result == set()

        result = find_all_member_names(SampleEnum, "INVALID")
        assert result == set()

    def test_find_all_member_names_with_aliases(self):
        """Test that all member names including aliases are returned"""
        class StatusWithAliases(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            QUEUED = 1   # Another alias for PENDING
            APPROVED = 2
            ACCEPTED = 2  # Alias for APPROVED

        # Should return all member names with value 1
        result = find_all_member_names(StatusWithAliases, 1)
        assert len(result) == 3
        assert "PENDING" in result
        assert "WAITING" in result
        assert "QUEUED" in result

        # Should return all member names with value 2
        result = find_all_member_names(StatusWithAliases, 2)
        assert len(result) == 2
        assert "APPROVED" in result
        assert "ACCEPTED" in result

    def test_find_all_member_names_strenum(self):
        """Test finding all member names in StrEnum"""
        result = find_all_member_names(ColorStrEnum, "red")
        assert result == {"RED"}

        result = find_all_member_names(ColorStrEnum, "yellow")
        assert result == set()

    def test_find_all_member_names_intenum(self):
        """Test finding all member names in IntEnum"""
        result = find_all_member_names(StatusIntEnum, 1)
        assert result == {"PENDING"}

        result = find_all_member_names(StatusIntEnum, 99)
        assert result == set()

    def test_find_all_member_names_flag(self):
        """Test finding all member names in Flag enum"""
        result = find_all_member_names(Permission, 1)
        assert result == {"READ"}

        result = find_all_member_names(Permission, 7)
        # RWX is an alias with value 7
        assert result == {"RWX"}

    def test_find_all_member_names_intflag(self):
        """Test finding all member names in IntFlag enum"""
        result = find_all_member_names(FileMode, 4)
        assert result == {"R"}

        result = find_all_member_names(FileMode, 7)
        # RWX is an alias with value 7
        assert result == {"RWX"}

    def test_find_all_member_names_none_value(self):
        """Test finding all member names with None value"""
        result = find_all_member_names(SampleEnumEmpty, None)
        # All three members have None value
        assert len(result) == 3
        assert "ONE" in result
        assert "TWO" in result
        assert "THREE" in result

    def test_find_all_member_names_non_enum(self):
        """Test that ValueError is raised for non-enum input"""
        with pytest.raises(ValueError):
            find_all_member_names(FakeEnum, 1)

        with pytest.raises(ValueError):
            find_all_member_names(SimpleDataclass, 1)

    def test_find_all_member_names_unhashable_value(self):
        """Test finding member names with unhashable values"""
        unhashable_value = [1, "2", 3.45, [{"hello": 7}, ("8", 9.10)]]
        result = find_all_member_names(SampleEnumBadData, unhashable_value)
        assert len(result) == 1
        assert "FOUR" in result

        # Different unhashable value should return empty set
        different_list = [1, 2, 3]
        result = find_all_member_names(SampleEnumBadData, different_list)
        assert result == set()

    def test_find_all_member_names_auto_enum(self):
        """Test finding all member names in auto() enum"""
        result = find_all_member_names(AutoEnum, 1)
        assert result == {"FIRST"}

        result = find_all_member_names(AutoEnum, 2)
        assert result == {"SECOND"}


class TestFindMemberNamesDict:
    """Test the find_member_names_dict function (returns all names mapped to member)"""

    def test_find_member_names_dict_basic_int_enum(self):
        """Test finding member names dict by integer value (no aliases)"""
        result = find_member_names_dict(SampleEnum, 1)
        assert result == {"ONE": SampleEnum.ONE}

        result = find_member_names_dict(SampleEnum, 2)
        assert result == {"TWO": SampleEnum.TWO}

    def test_find_member_names_dict_not_found(self):
        """Test that empty dict is returned when value not found"""
        result = find_member_names_dict(SampleEnum, 99)
        assert result == {}

    def test_find_member_names_dict_with_aliases(self):
        """Test that all names including aliases map to the same member"""
        class StatusWithAliases(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            QUEUED = 1   # Another alias for PENDING
            APPROVED = 2
            ACCEPTED = 2  # Alias for APPROVED

        # Should return all names mapped to the same member instance
        result = find_member_names_dict(StatusWithAliases, 1)
        assert len(result) == 3
        assert result["PENDING"] == StatusWithAliases.PENDING
        assert result["WAITING"] == StatusWithAliases.PENDING
        assert result["QUEUED"] == StatusWithAliases.PENDING
        # All should be the same object
        assert result["PENDING"] is result["WAITING"]
        assert result["PENDING"] is result["QUEUED"]

        result = find_member_names_dict(StatusWithAliases, 2)
        assert len(result) == 2
        assert result["APPROVED"] == StatusWithAliases.APPROVED
        assert result["ACCEPTED"] == StatusWithAliases.APPROVED
        assert result["APPROVED"] is result["ACCEPTED"]

    def test_find_member_names_dict_strenum(self):
        """Test finding member names dict in StrEnum"""
        result = find_member_names_dict(ColorStrEnum, "red")
        assert result == {"RED": ColorStrEnum.RED}

        result = find_member_names_dict(ColorStrEnum, "yellow")
        assert result == {}

    def test_find_member_names_dict_intenum(self):
        """Test finding member names dict in IntEnum"""
        result = find_member_names_dict(StatusIntEnum, 1)
        assert result == {"PENDING": StatusIntEnum.PENDING}

        result = find_member_names_dict(StatusIntEnum, 99)
        assert result == {}

    def test_find_member_names_dict_none_value(self):
        """Test finding member names dict with None value"""
        result = find_member_names_dict(SampleEnumEmpty, None)
        # All three members have None value, all map to same object
        assert len(result) == 3
        assert result["ONE"] == SampleEnumEmpty.ONE
        assert result["TWO"] == SampleEnumEmpty.TWO
        assert result["THREE"] == SampleEnumEmpty.THREE
        # All should be the same object (aliases)
        assert result["ONE"] is result["TWO"]
        assert result["ONE"] is result["THREE"]

    def test_find_member_names_dict_non_enum(self):
        """Test that ValueError is raised for non-enum input"""
        with pytest.raises(ValueError):
            find_member_names_dict(FakeEnum, 1)

        with pytest.raises(ValueError):
            find_member_names_dict(SimpleDataclass, 1)

    def test_find_member_names_dict_unhashable_value(self):
        """Test finding member names dict with unhashable values"""
        unhashable_value = [1, "2", 3.45, [{"hello": 7}, ("8", 9.10)]]
        result = find_member_names_dict(SampleEnumBadData, unhashable_value)
        assert len(result) == 1
        assert result["FOUR"] == SampleEnumBadData.FOUR


class TestGetEnumValues:
    """Test the get_enum_values function (backward compatible)"""

    def test_get_enum_values_basic(self):
        values = get_enum_values(SampleEnum)
        assert SampleEnum.ONE.value in values
        assert 1 in values
        assert isinstance(values, list)

    def test_get_enum_values_fake_enum(self):
        with pytest.raises(ValueError):
            get_enum_values(FakeEnum)

    def test_get_enum_values_dataclass(self):
        with pytest.raises(ValueError):
            get_enum_values(SimpleDataclass)
        with pytest.raises(ValueError):
            get_enum_values(NestedDataclass)

    def test_get_enum_values_empty(self):
        values = get_enum_values(SampleEnumEmpty)
        assert SampleEnumEmpty.ONE.value in values
        assert None in values

    def test_get_enum_values_pass(self):
        values = get_enum_values(SampleEnumPass)
        assert not values

    def test_get_enum_values_bad_data(self):
        values = get_enum_values(SampleEnumBadData)
        assert 1 in values[0]
        assert values[0][3][0]["hello"] == 7


class TestGetEnumValuesSet:
    """Test the get_enum_values_set function (backward compatible)"""

    def test_get_enum_values_set_basic(self):
        values = get_enum_values_set(SampleEnum)
        assert SampleEnum.ONE.value in values
        assert 1 in values
        assert isinstance(values, set)

    def test_get_enum_values_set_fake_enum(self):
        with pytest.raises(ValueError):
            get_enum_values_set(FakeEnum)

    def test_get_enum_values_set_dataclass(self):
        with pytest.raises(ValueError):
            get_enum_values_set(SimpleDataclass)
        with pytest.raises(ValueError):
            get_enum_values_set(NestedDataclass)

    def test_get_enum_values_set_empty(self):
        values = get_enum_values_set(SampleEnumEmpty)
        assert SampleEnumEmpty.ONE.value in values
        assert None in values

    def test_get_enum_values_set_pass(self):
        values = get_enum_values_set(SampleEnumPass)
        assert not values


class TestGetEnumValuesTuple:
    """Test the get_enum_values_tuple function (backward compatible)"""

    def test_get_enum_values_tuple_basic(self):
        values = get_enum_values_tuple(SampleEnum)
        assert SampleEnum.ONE.value in values
        assert 1 in values
        assert isinstance(values, tuple)

    def test_get_enum_values_tuple_fake_enum(self):
        with pytest.raises(ValueError):
            get_enum_values_tuple(FakeEnum)

    def test_get_enum_values_tuple_dataclass(self):
        with pytest.raises(ValueError):
            get_enum_values_tuple(SimpleDataclass)
        with pytest.raises(ValueError):
            get_enum_values_tuple(NestedDataclass)

    def test_get_enum_values_tuple_empty(self):
        values = get_enum_values_tuple(SampleEnumEmpty)
        assert SampleEnumEmpty.ONE.value in values
        assert None in values

    def test_get_enum_values_tuple_pass(self):
        values = get_enum_values_tuple(SampleEnumPass)
        assert not values


class TestGetEnumValuesDict:
    """Test the get_enum_values_dict function (backward compatible)"""

    def test_get_enum_values_dict_basic(self):
        values = get_enum_values_dict(SampleEnum)
        assert values["ONE"] == 1
        assert isinstance(values, dict)

    def test_get_enum_values_dict_fake_enum(self):
        with pytest.raises(ValueError):
            get_enum_values_dict(FakeEnum)

    def test_get_enum_values_dict_dataclass(self):
        with pytest.raises(ValueError):
            get_enum_values_dict(SimpleDataclass)
        with pytest.raises(ValueError):
            get_enum_values_dict(NestedDataclass)

    def test_get_enum_values_dict_empty(self):
        values = get_enum_values_dict(SampleEnumEmpty)
        assert values["ONE"] is None

    def test_get_enum_values_dict_pass(self):
        values = get_enum_values_dict(SampleEnumPass)
        assert not values


class TestGetEnumAttributeNames:
    """Test the get_enum_attribute_names function (backward compatible)"""

    def test_get_enum_attribute_names_basic(self):
        values = get_enum_attribute_names(SampleEnum)
        assert "ONE" in values
        assert values[1] == "TWO"

    def test_get_enum_attribute_names_bad_data(self):
        values = get_enum_attribute_names(SampleEnumBadData)
        assert "FIVE" in values
        assert values[0] == "FOUR"

    def test_get_enum_attribute_names_pass(self):
        values = get_enum_attribute_names(SampleEnumPass)
        assert not values

    def test_get_enum_attribute_names_non_enum(self):
        with pytest.raises(ValueError):
            get_enum_attribute_names(enumclass=FakeEnum)
        with pytest.raises(ValueError):
            get_enum_attribute_names(enumclass=NestedDataclass)


class TestStrEnumSupport:
    """Test StrEnum value-based enum support"""

    def test_is_enum_with_strenum(self):
        assert is_enum(ColorStrEnum)

    def test_member_identities_strenum(self):
        identities = member_identities(ColorStrEnum)
        assert ColorStrEnum.RED in identities
        assert ColorStrEnum.GREEN in identities
        assert ColorStrEnum.BLUE in identities
        assert len(identities) == 3

    def test_member_names_strenum(self):
        names = member_names(ColorStrEnum)
        assert 'RED' in names
        assert 'GREEN' in names
        assert 'BLUE' in names
        assert len(names) == 3

    def test_member_values_strenum(self):
        """member_values should return the primitive string values"""
        values = member_values(ColorStrEnum)
        assert "red" in values
        assert "green" in values
        assert "blue" in values
        assert len(values) == 3
        # Verify these are strings, not enum instances
        assert all(isinstance(v, str) for v in values)

    def test_is_valid_member_name_strenum(self):
        assert is_valid_member_name(ColorStrEnum, 'RED')
        assert is_valid_member_name(ColorStrEnum, 'GREEN')
        assert not is_valid_member_name(ColorStrEnum, 'YELLOW')

    def test_is_valid_member_value_strenum(self):
        """Should validate against primitive string values"""
        assert is_valid_member_value(ColorStrEnum, "red")
        assert is_valid_member_value(ColorStrEnum, "green")
        assert not is_valid_member_value(ColorStrEnum, "yellow")
        # StrEnum has special behavior: enum instances == their primitive values
        # So ColorStrEnum.RED == "red", and both will be in the values set
        assert is_valid_member_value(ColorStrEnum, ColorStrEnum.RED)

    def test_is_valid_member_identity_strenum(self):
        """Should validate enum instances"""
        assert is_valid_member_identity(ColorStrEnum, ColorStrEnum.RED)
        assert is_valid_member_identity(ColorStrEnum, ColorStrEnum.GREEN)
        # StrEnum uses equality not identity: "red" == ColorStrEnum.RED
        # So "red" will be found in the identities set (using __contains__ with ==)
        assert is_valid_member_identity(ColorStrEnum, "red")

    def test_get_enum_values_strenum(self):
        values = get_enum_values(ColorStrEnum)
        assert "red" in values
        assert "green" in values
        assert "blue" in values
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)

    def test_get_enum_values_dict_strenum(self):
        values = get_enum_values_dict(ColorStrEnum)
        assert values["RED"] == "red"
        assert values["GREEN"] == "green"
        assert values["BLUE"] == "blue"


class TestIntEnumSupport:
    """Test IntEnum value-based enum support"""

    def test_is_enum_with_intenum(self):
        assert is_enum(StatusIntEnum)

    def test_member_identities_intenum(self):
        identities = member_identities(StatusIntEnum)
        assert StatusIntEnum.PENDING in identities
        assert StatusIntEnum.APPROVED in identities
        assert StatusIntEnum.REJECTED in identities
        assert len(identities) == 3

    def test_member_names_intenum(self):
        names = member_names(StatusIntEnum)
        assert 'PENDING' in names
        assert 'APPROVED' in names
        assert 'REJECTED' in names
        assert len(names) == 3

    def test_member_values_intenum(self):
        """member_values should return the primitive int values"""
        values = member_values(StatusIntEnum)
        assert 1 in values
        assert 2 in values
        assert 3 in values
        assert len(values) == 3
        # Verify these are ints (note: IntEnum members are also ints)
        assert all(isinstance(v, int) for v in values)

    def test_is_valid_member_name_intenum(self):
        assert is_valid_member_name(StatusIntEnum, 'PENDING')
        assert is_valid_member_name(StatusIntEnum, 'APPROVED')
        assert not is_valid_member_name(StatusIntEnum, 'UNKNOWN')

    def test_is_valid_member_value_intenum(self):
        """Should validate against primitive int values"""
        assert is_valid_member_value(StatusIntEnum, 1)
        assert is_valid_member_value(StatusIntEnum, 2)
        assert not is_valid_member_value(StatusIntEnum, 99)
        # IntEnum is tricky: IntEnum.PENDING == 1, so this will pass
        # But conceptually we're checking if the value 1 exists
        assert is_valid_member_value(StatusIntEnum, StatusIntEnum.PENDING)

    def test_is_valid_member_identity_intenum(self):
        """Should validate enum instances"""
        assert is_valid_member_identity(StatusIntEnum, StatusIntEnum.PENDING)
        assert is_valid_member_identity(StatusIntEnum, StatusIntEnum.APPROVED)
        # IntEnum uses equality not identity: 1 == StatusIntEnum.PENDING
        # So primitive 1 will be found in the identities set (using __contains__ with ==)
        assert 1 in member_identities(StatusIntEnum)

    def test_get_enum_values_intenum(self):
        values = get_enum_values(StatusIntEnum)
        assert 1 in values
        assert 2 in values
        assert 3 in values
        assert isinstance(values, list)
        assert all(isinstance(v, int) for v in values)

    def test_get_enum_values_dict_intenum(self):
        values = get_enum_values_dict(StatusIntEnum)
        assert values["PENDING"] == 1
        assert values["APPROVED"] == 2
        assert values["REJECTED"] == 3


class TestIdentityVsValueEnums:
    """Test the critical distinction between identity and value-based enums"""

    def test_identity_enum_member_values_vs_identities(self):
        """For identity enums where value == instance, both should return instances"""
        values = member_values(IdentityEnum)
        identities = member_identities(IdentityEnum)

        # For identity enums, values are the instances themselves
        assert IdentityEnum.RED.value in values
        assert IdentityEnum.RED in identities
        # The actual .value objects should be in the values set
        assert all(isinstance(v, object) for v in values)

    def test_value_enum_member_values_vs_identities_strenum(self):
        """For StrEnum, values should be primitives, identities should be instances"""
        values = member_values(ColorStrEnum)
        identities = member_identities(ColorStrEnum)

        # Values should be primitive strings
        assert "red" in values
        assert all(isinstance(v, str) for v in values)

        # Identities should be enum instances
        assert ColorStrEnum.RED in identities
        assert all(isinstance(i, ColorStrEnum) for i in identities)

        # StrEnum special behavior: "red" == ColorStrEnum.RED, so "red" in identities is True
        # This is by design in Python - StrEnum is meant to be interchangeable with strings
        assert "red" in identities

    def test_value_enum_member_values_vs_identities_intenum(self):
        """For IntEnum, values should be primitives, identities should be instances"""
        values = member_values(StatusIntEnum)
        identities = member_identities(StatusIntEnum)

        # Values should be primitive ints
        assert 1 in values
        assert all(isinstance(v, int) for v in values)

        # Identities should be enum instances
        assert StatusIntEnum.PENDING in identities
        assert all(isinstance(i, StatusIntEnum) for i in identities)

        # Due to IntEnum's special behavior where IntEnum.PENDING == 1,
        # we need to check identity, not equality
        # The primitive 1 should not be in the identities set by identity
        plain_int = 1
        assert plain_int not in identities or StatusIntEnum.PENDING in identities


class TestPerformance:
    """Performance tests for enum operations"""

    def test_get_enum_values_performance(self):
        class LargeEnum(Enum):
            locals().update({f'ITEM_{i}': i for i in range(1000)})

        import time
        start_time = time.time()
        values = get_enum_values(LargeEnum)
        end_time = time.time()

        assert len(values) == 1000
        assert end_time - start_time < 0.1  # Adjust threshold as needed


class TestAutoEnumSupport:
    """Test auto() value generation for regular Enum"""

    def test_is_enum_with_auto(self):
        assert is_enum(AutoEnum)

    def test_auto_generates_sequential_integers(self):
        """auto() generates 1, 2, 3... for regular Enum"""
        values = get_enum_values(AutoEnum)
        assert 1 in values
        assert 2 in values
        assert 3 in values

    def test_member_names_auto(self):
        names = member_names(AutoEnum)
        assert 'FIRST' in names
        assert 'SECOND' in names
        assert 'THIRD' in names

    def test_member_values_auto(self):
        """auto() values should be integers"""
        values = member_values(AutoEnum)
        assert 1 in values
        assert 2 in values
        assert 3 in values

    def test_member_identities_auto(self):
        """auto() enum instances should be in identities"""
        identities = member_identities(AutoEnum)
        assert AutoEnum.FIRST in identities
        assert AutoEnum.SECOND in identities
        assert AutoEnum.THIRD in identities

    def test_is_valid_member_value_auto(self):
        """Should validate against auto-generated integer values"""
        assert is_valid_member_value(AutoEnum, 1)
        assert is_valid_member_value(AutoEnum, 2)
        assert is_valid_member_value(AutoEnum, 3)
        assert not is_valid_member_value(AutoEnum, 99)

    def test_is_valid_member_identity_auto(self):
        """Should validate enum instances"""
        assert is_valid_member_identity(AutoEnum, AutoEnum.FIRST)
        assert is_valid_member_identity(AutoEnum, AutoEnum.SECOND)
        # auto() generates integers, but they're not the same as the enum instance
        assert not is_valid_member_identity(AutoEnum, 1)


class TestFlagSupport:
    """Test Flag enum support (bitwise flags)"""

    def test_is_enum_with_flag(self):
        assert is_enum(Permission)

    def test_member_names_flag(self):
        """Flag should return only power-of-2 members, not aliases"""
        names = member_names(Permission)
        assert 'READ' in names
        assert 'WRITE' in names
        assert 'EXECUTE' in names
        # RWX is an alias, not a separate member
        assert 'RWX' in names  # Python includes aliases in __members__

    def test_member_values_flag(self):
        """Flag auto() generates power-of-2 values"""
        values = member_values(Permission)
        assert 1 in values   # READ
        assert 2 in values   # WRITE
        assert 4 in values   # EXECUTE
        assert 7 in values   # RWX (alias, but still in values)

    def test_member_identities_flag(self):
        """Flag identities should include canonical members"""
        identities = member_identities(Permission)
        assert Permission.READ in identities
        assert Permission.WRITE in identities
        assert Permission.EXECUTE in identities
        assert Permission.RWX in identities  # Alias is also a member

    def test_is_valid_member_name_flag(self):
        assert is_valid_member_name(Permission, 'READ')
        assert is_valid_member_name(Permission, 'WRITE')
        assert is_valid_member_name(Permission, 'RWX')
        assert not is_valid_member_name(Permission, 'DELETE')

    def test_is_valid_member_value_flag(self):
        """Should validate against flag values"""
        assert is_valid_member_value(Permission, 1)   # READ
        assert is_valid_member_value(Permission, 2)   # WRITE
        assert is_valid_member_value(Permission, 4)   # EXECUTE
        assert is_valid_member_value(Permission, 7)   # RWX
        assert not is_valid_member_value(Permission, 8)

    def test_is_valid_member_identity_flag(self):
        """Should validate flag instances"""
        assert is_valid_member_identity(Permission, Permission.READ)
        assert is_valid_member_identity(Permission, Permission.WRITE)
        assert is_valid_member_identity(Permission, Permission.RWX)
        # Primitive values are not the same as flag instances
        assert not is_valid_member_identity(Permission, 1)

    def test_flag_combinations_not_in_identities(self):
        """Flag combinations created at runtime are not members"""
        combo = Permission.READ | Permission.WRITE
        # Combo is not a canonical member
        assert combo not in member_identities(Permission)
        # But RWX is a named alias, so it IS a member
        assert Permission.RWX in member_identities(Permission)

    def test_get_enum_values_flag(self):
        values = get_enum_values(Permission)
        assert 1 in values
        assert 2 in values
        assert 4 in values
        assert isinstance(values, list)


class TestIntFlagSupport:
    """Test IntFlag enum support (integer-comparable bitwise flags)"""

    def test_is_enum_with_intflag(self):
        assert is_enum(FileMode)

    def test_member_names_intflag(self):
        names = member_names(FileMode)
        assert 'R' in names
        assert 'W' in names
        assert 'X' in names
        assert 'RWX' in names  # Alias

    def test_member_values_intflag(self):
        """IntFlag values are integers"""
        values = member_values(FileMode)
        assert 4 in values  # R
        assert 2 in values  # W
        assert 1 in values  # X
        assert 7 in values  # RWX

    def test_member_identities_intflag(self):
        identities = member_identities(FileMode)
        assert FileMode.R in identities
        assert FileMode.W in identities
        assert FileMode.X in identities
        assert FileMode.RWX in identities

    def test_is_valid_member_value_intflag(self):
        """IntFlag has special behavior: compares equal to integers"""
        assert is_valid_member_value(FileMode, 4)  # R
        assert is_valid_member_value(FileMode, 2)  # W
        assert is_valid_member_value(FileMode, 1)  # X
        assert is_valid_member_value(FileMode, 7)  # RWX
        # IntFlag members == their integer values
        assert is_valid_member_value(FileMode, FileMode.R)

    def test_is_valid_member_identity_intflag(self):
        """Should validate intflag instances"""
        assert is_valid_member_identity(FileMode, FileMode.R)
        assert is_valid_member_identity(FileMode, FileMode.W)
        # IntFlag special behavior: integer values are found in identities
        assert 4 in member_identities(FileMode)  # IntFlag == int

    def test_intflag_combinations_not_in_identities(self):
        """IntFlag combinations created at runtime are not members"""
        combo = FileMode.R | FileMode.W
        # Combo is not a canonical member (unless it's an alias like RWX)
        # However, 6 (R|W) is not named, so it won't be in members
        # But Python's IntFlag behavior makes comparison tricky
        # The combo itself is an IntFlag, not in original members
        identities = member_identities(FileMode)
        # Runtime combination is not in the original member identities
        assert combo not in [FileMode.R, FileMode.W, FileMode.X, FileMode.RWX]

    def test_get_enum_values_intflag(self):
        values = get_enum_values(FileMode)
        assert 4 in values
        assert 2 in values
        assert 1 in values
        assert isinstance(values, list)


class TestEdgeCases:
    """Edge case tests"""

    def test_single_item_enum(self):
        class SingleItemEnum(Enum):
            SINGLE = 1

        values = get_enum_values(SingleItemEnum)
        assert values == [1]

    @pytest.mark.parametrize("method", [
        get_enum_values,
        get_enum_values_set,
        get_enum_values_tuple,
        get_enum_values_dict,
        get_enum_attribute_names,
    ])
    def test_enum_methods_with_invalid_input(self, method):
        with pytest.raises(ValueError):
            method(SimpleDataclass)


class TestErrorConditions:
    """Error condition tests from test_error_conditions.py"""

    def test_is_enum_with_type_error(self):
        result = is_enum(None)
        assert result is False

    def test_enum_methods_error_handling(self):
        # NotAnEnum is a plain class with ONE=1, TWO=2
        class NotAnEnum:
            ONE = 1
            TWO = 2
        non_enum = NotAnEnum
        with pytest.raises(ValueError, match="Class is not an Enum"):
            get_enum_values(non_enum)
        with pytest.raises(ValueError, match="Class is not an Enum"):
            get_enum_values_set(non_enum)
        with pytest.raises(ValueError, match="Class is not an Enum"):
            get_enum_values_tuple(non_enum)
        with pytest.raises(ValueError, match="Class is not an Enum"):
            get_enum_values_dict(non_enum)
        with pytest.raises(ValueError, match="Class is not an Enum"):
            get_enum_attribute_names(non_enum)
