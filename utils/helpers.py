def get_grade(score):
    """Calculate grade based on score"""
    if score >= 90:
        return 'A+'
    elif score >= 80:
        return 'A'
    elif score >= 70:
        return 'B+'
    elif score >= 60:
        return 'B'
    elif score >= 50:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'

def format_currency(amount):
    """Format currency for display"""
    return f"GH₵ {amount:,.2f}"