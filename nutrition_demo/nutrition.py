"""Exact Decimal arithmetic. Round only at the presentation boundary."""
from decimal import Decimal
from .models import Nutrients, ZERO, decimal


def scale_nutrients(value, used, reference):
    return value.scale(decimal(used) / decimal(reference, positive=True))


def per_box(total, boxes):
    if type(boxes) is not int or boxes <= 0:
        raise ValueError('Boxes must be a positive integer')
    return total.scale(Decimal(1) / boxes)


def used_cost(price, used, package_quantity):
    return decimal(price) * decimal(used) / decimal(package_quantity, positive=True)


def aggregate_cost(values):
    values = list(values)
    known = sum((decimal(v) for v in values if v is not None), Decimal(0))
    complete = all(v is not None for v in values)
    return {'known_subtotal': known, 'complete': complete, 'total': known if complete else None}


def validate_targets(actual, targets):
    limits = {'kcal': ('0.95','1.05'), 'protein_g': ('1','1.1'), 'carbs_g': ('0.9','1.1'), 'fat_g': ('0.9','1.1')}
    metrics = {}
    for k,(lo,hi) in limits.items():
        t, a = getattr(targets,k),getattr(actual,k)
        if t <= 0:
            raise ValueError('All nutrient targets must be positive')
        lower, upper = t * Decimal(lo), t * Decimal(hi)
        metrics[k] = {'actual': a, 'target': t, 'lower': lower, 'upper': upper,
                      'difference': a-t, 'ratio': a/t, 'passed': lower <= a <= upper}
    return {'passed': all(v['passed'] for v in metrics.values()), 'metrics': metrics}


def checked_quantity(quantity, unit, state, reference):
    if unit != reference['unit'] or state != reference['state']:
        raise ValueError('Unit/state mismatch: no unverified conversion or density assumption')
    return decimal(quantity)
