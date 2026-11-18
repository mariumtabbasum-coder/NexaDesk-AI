import datetime
def calculate_age(date_str):
    try:
        birth=datetime.date.fromisoformat(date_str); today=datetime.date.today()
        years=today.year-birth.year-((today.month,today.day)<(birth.month,birth.day))
        months=(today.month-birth.month)%12
        return {"message":f"You are {years} years old (approximately {months} additional month(s) since your last birthday).","years":years}
    except Exception: return {"message":"Invalid date. Use YYYY-MM-DD."}
