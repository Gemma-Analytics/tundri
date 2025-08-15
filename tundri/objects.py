from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class SnowflakeObject:
    """Base class to represent Snowflake objects.

    It has customized behavior for equality checks, set operations and sort. This is
    done to allow for simpler comparisons between objects that exist vs. ought to exist.
    Equality checks ignore the paramaters, which need to be checked using more complex logic.

    Attributes:
        type: object type, e.g. `database`, `warehouse`, etc
        name: object name, e.g. `raw` for a database or `load` for a warehouse
        params: dict with object parameters, e.g. for a user: {'default_warehouse': 'load'}
        required_params: tuple with values expected as keys of `params`
    """

    type: str = None
    name: str = None
    params: Dict = field(default_factory=dict)
    required_params: Tuple = field(default_factory=tuple)

    def __eq__(self, other):
        return (
            self.type.casefold() == other.type.casefold()
            and self.name.casefold() == other.name.casefold()
        )

    def __hash__(self):
        return hash((self.type.casefold(), self.name.casefold()))

    def __lt__(self, other):
        return self.name.casefold() < other.name.casefold()

    def get_missing_required_params(self):
        if self.required_params and not self.params:
            return self.required_params
        return [key for key in self.required_params if key not in self.params.keys()]

    def check_required_params(self):
        return not self.get_missing_required_params()


@dataclass(frozen=True, eq=False)
class Warehouse(SnowflakeObject):
    type: str = "warehouse"
    required_params: Tuple = tuple(["warehouse_size", "auto_suspend"])


@dataclass(frozen=True, eq=False)
class Database(SnowflakeObject):
    type: str = "database"


@dataclass(frozen=True, eq=False)
class Schema(SnowflakeObject):
    type: str = "schema"


@dataclass(frozen=True, eq=False)
class Role(SnowflakeObject):
    type: str = "role"


@dataclass(frozen=True, eq=False)
class User(SnowflakeObject):
    type: str = "user"
    required_params: Tuple = tuple(["default_role"])


class ConfigurationValueError(ValueError):
    pass
