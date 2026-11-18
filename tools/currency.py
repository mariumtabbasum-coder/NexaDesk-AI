import requests

TIMEOUT = 10


def _er_api(amount, base, target):
    """open.er-api.com: free, no key, 160+ currencies (includes PKR)."""
    r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()
    if d.get("result") != "success":
        raise ValueError("er-api error")
    return d["rates"][target]


def _frankfurter_v2(amount, base, target):
    r = requests.get(f"https://api.frankfurter.dev/v2/rate/{base}/{target}", timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()
    if "rate" in d:
        return d["rate"]
    return d["rates"][target]


def _frankfurter_v1(amount, base, target):
    # v1 uses base/symbols (NOT from/to) and only supports ~30 ECB currencies
    r = requests.get("https://api.frankfurter.dev/v1/latest",
                     params={"base": base, "symbols": target}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["rates"][target]


PROVIDERS = (_er_api, _frankfurter_v2, _frankfurter_v1)


def convert_currency(amount, base, target):
    base, target = (base or "USD").upper(), (target or "PKR").upper()
    if base == target:
        return {"message": f"{amount:,.2f} {base} = {amount:,.2f} {target} (rate: 1)", "rate": 1, "result": amount}
    for provider in PROVIDERS:
        try:
            rate = float(provider(amount, base, target))
            total = amount * rate
            return {"message": f"{amount:,.2f} {base} = {total:,.2f} {target} (rate: {rate:,.4f})",
                    "rate": rate, "result": total}
        except Exception:
            continue  # try the next provider
    return {"message": f"Sorry, I couldn't get the {base} to {target} rate right now. "
                       "Please check the currency codes and your internet connection, then try again."}