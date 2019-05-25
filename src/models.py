from peewee import *

db = SqliteDatabase(None, pragmas={'foreign_keys': 1})


class ProfileModel(Model):
    name = CharField(unique=True)
    aircraft = CharField()

    class Meta:
        database = db


class MissionModel(Model):
    number = IntegerField()
    name = CharField(null=True, default="")
    latitude = FloatField()
    longitude = FloatField()
    elevation = FloatField()
    profile = ForeignKeyField(ProfileModel, backref='missions')

    class Meta:
        database = db


class WaypointModel(Model):
    name = CharField(null=True, default="")
    latitude = FloatField()
    longitude = FloatField()
    elevation = FloatField()
    profile = ForeignKeyField(ProfileModel, backref='waypoints')

    class Meta:
        database = db
