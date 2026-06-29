from datetime import datetime, timedelta, timezone

LOCAL_TIMEZONE = timezone(timedelta(hours=-3))


def format_currency(value: float | None) -> str:
    if value is None:
        return "N/D"
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(LOCAL_TIMEZONE).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return value


def parse_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
