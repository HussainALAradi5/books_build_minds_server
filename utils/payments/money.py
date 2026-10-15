from decimal import Decimal, ROUND_HALF_UP
from constants.library_policy import CURRENCY_SCALE, RENTAL_RATE

def price_minor(price, rental=False) -> int:
    value = Decimal(str(price)) * (RENTAL_RATE if rental else Decimal(1))
    # BHD has three decimal places; preserve fils in the immutable quote.
    if not value.is_finite() or value <= 0:
        raise ValueError("Book price must be positive")
    amount = int(value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP) * CURRENCY_SCALE)
    if not 100 <= amount <= 99_999_999:
        raise ValueError("Price is outside the supported payment range")
    return amount
