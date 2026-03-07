# Sample: divide_by_zero.py
# Issues: ZeroDivisionError, no input validation, bare except, unused import

import os
import math

def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)  # crashes if numbers is empty

def get_discount(price, discount_pct):
    return price - (price * discount_pct / 100)  # no bounds check on discount_pct

def process_items(items):
    results = []
    for item in items:
        try:
            result = 100 / item["value"]
            results.append(result)
        except:  # bare except swallows all errors silently
            pass
    return results

scores = [90, 85, 0, 72]
print("Average:", calculate_average(scores))

empty = []
print("Empty avg:", calculate_average(empty))  # ZeroDivisionError at runtime
