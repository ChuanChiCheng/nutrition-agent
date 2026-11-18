from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal, InvalidOperation
import json
from typing import Any


def decimal(value: Any, *, positive=False) -> Decimal:
    if isinstance(value, bool):
        raise ValueError('Boolean is not a quantity')
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError('Invalid quantity') from None
    if not d.is_finite() or d < 0 or (positive and d == 0):
        raise ValueError('Quantity must be finite and nonnegative (positive when required)')
    return d


def encode(value):
    if is_dataclass(value):
        return encode(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def dumps(value):
    return json.dumps(encode(value), ensure_ascii=False, allow_nan=False, sort_keys=True)


@dataclass(frozen=True)
class Nutrients:
    kcal: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, decimal(getattr(self, name)))

    @classmethod
    def from_dict(cls, values):
        if set(values) != set(cls.__dataclass_fields__):
            raise ValueError('Missing or unknown nutrient fields')
        return cls(**values)

    def __add__(self, other):
        return Nutrients(**{k: getattr(self, k) + getattr(other, k) for k in self.__dataclass_fields__})

    def scale(self, factor):
        factor = decimal(factor)
        return Nutrients(**{k: getattr(self, k) * factor for k in self.__dataclass_fields__})


ZERO = Nutrients(0, 0, 0, 0)


@dataclass(frozen=True)
class IngredientAllocation:
    cooking_ingredient_id: str
    quantity: Decimal
    unit: str


@dataclass(frozen=True)
class BatchOutput:
    name: str
    boxes: int
    allocations: list[IngredientAllocation]


@dataclass(frozen=True)
class Result:
    ok: bool
    data: dict = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True)
class Preview:
    id: str
    kind: str
    state_version: int
    changes: list[dict]
    summary: str
