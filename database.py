from peewee import *

db = SqliteDatabase('supermarkets.db')

class Supermarkets(Model):
    company = CharField()
    headquarters = CharField()
    served_countries = TextField()
    num_locations = IntegerField()
    num_employees = IntegerField()

    class Meta:
        database = db

def init_db():
    db.connect()
    db.drop_tables([Supermarkets], safe=True)  # Drop the old table
    db.create_tables([Supermarkets], safe=True)  # Create the new table