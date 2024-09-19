from os import environ
from datetime import timedelta, datetime
from pymongo import MongoClient
import pytz
from info import DATABASE_URI, DATABASE_NAME

class VR_db:
    def __init__(self, db_url, db_name, timezone):
        self.client = MongoClient(db_url)
        self.db = self.client[db_name]
        self.collection = self.db.verifications
        self.timezone = pytz.timezone(timezone)

    async def save_verification(self, user_id):
        now = datetime.now(self.timezone)
        year = now.year  
        verification = {"user_id": user_id, "verified_at": now, "year": year}
        self.collection.insert_one(verification)

    def get_start_end_dates(self, time_period, year=None):
        now = datetime.now(self.timezone)
        
        if time_period == 'today':
            start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = now
        elif time_period == 'yesterday':
            start_datetime = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = start_datetime + timedelta(days=1)
        elif time_period == 'this_week':
            start_datetime = now - timedelta(days=now.weekday())
            start_datetime = start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = now            
        elif time_period == 'this_month':
            start_datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_datetime = now
        elif time_period == 'last_month':
            first_day_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end_datetime = first_day_of_current_month - timedelta(microseconds=1)
            start_datetime = last_month_end_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_datetime = last_month_end_datetime
        elif time_period == 'year' and year:
            start_datetime = datetime(year, 1, 1, tzinfo=self.timezone)  # Start of the year
            end_datetime = datetime(year + 1, 1, 1, tzinfo=self.timezone) - timedelta(microseconds=1)  # End of the year
        else:
            raise ValueError("Invalid time period")
        
        return start_datetime, end_datetime

    async def get_vr_count(self, time_period, year=None):
        start_datetime, end_datetime = self.get_start_end_dates(time_period, year)
        count = self.collection.count_documents({'verified_at': {'$gt': start_datetime, '$lt': end_datetime}})
        return count

# Instantiate the VerificationDatabase class with appropriate parameters
vr_db = VR_db(DATABASE_URI, DATABASE_NAME, 'Asia/Kolkata')
