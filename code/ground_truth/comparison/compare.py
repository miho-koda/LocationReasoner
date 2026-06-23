import operator
def compare(operator_str):
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq
    }
    return ops[operator_str]