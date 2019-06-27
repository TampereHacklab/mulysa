import random


"""
helper methods for handling reference numbers
"""
def format(n):
    """
    Format reference number. returns a string with the number grouped fives
    """
    s = ''

    digits = list(str(n))
    digits.reverse()

    i = 0
    for digit in digits:
        if i > 0 and i % 5 == 0:
            s = ' ' + s
        s = digit + s
        i += 1

    return s

def generate(n: int):
    """
    generate reference number from the given input
    """
    return int('{base}{checksum}'.format(base=n, checksum=get_checksum(n)))

def get_checksum(n: int):
    """
    Calculate and return checksum (and only the checksum) for given input
    """
    if n < 100:
        raise ValueError('Base number must be at least three digits long and cannot be negative')

    # algorithm for finnish bank reference number
    #
    # from right to left sum all digits times the multiplier
    # from the sum deduct the next full 10
    # if checksum is 10 change it to 0

    multip = [7, 3, 1]
    digits = list(str(n))
    digits.reverse()

    s = 0
    i = 0
    for digit in digits:
        s += int(digit)*multip[i % 3]
        i += 1

    check = (((s % 10)*10-s) % 10)
    return check

def generate_random(min: int, max: int):
    """
    Get a new random reference number
    """
    if max < min:
        raise ValueError('Max cant be smaller than min')

    base = random.randint(min, max)
    return generate(base)

def split(n: int):
    """
    split reference number and base and checksum
    returns tuple (base, check)
    """
    base = int(str(n)[:-1])
    check = int(str(n)[:-1])
    return base, check

def validate(n: int):
    """
    validate checksum, raises error if not valid
    """
    base, check = split(n)

    recalculated = generate(base)

    if recalculated != n:
        raise ValueError('Checksum does not match')

def isvalid(n: int):
    """
    returns true for valid checksum, false for invalid
    """
    try:
        validate(n)
    except Exception:
        return False

    return True
