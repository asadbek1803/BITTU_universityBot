# Update imports at the top of your files to include timezone support
from datetime import datetime, timedelta, timezone
import pytz

# Create a timezone object for Tashkent
tashkent_tz = pytz.timezone('Asia/Tashkent')

# Replace all instances of datetime.now() with:
def get_tashkent_time():
    """Returns current time in Tashkent timezone"""
    return datetime.now(pytz.timezone('Asia/Tashkent'))

# Example of usage (replace in your code):
# Before: now = datetime.now()
# After: now = get_tashkent_time()