from peewee import Model, IntegerField, CharField, ForeignKeyField, FloatField, SqliteDatabase, IntegrityError

db = SqliteDatabase(None, pragmas={'foreign_keys': 1})

class ProfileModel(Model):
    name = CharField(unique=True)
    aircraft = CharField(unique=False)

    class Meta:
        database = db


class SequenceModel(Model):
    identifier = IntegerField()
    profile = ForeignKeyField(ProfileModel, backref='sequences')

    class Meta:
        database = db


class WaypointModel(Model):
    name = CharField(null=True, default="")
    latitude = FloatField()
    longitude = FloatField()
    elevation = IntegerField(default=0)
    profile = ForeignKeyField(ProfileModel, backref='waypoints')
    sequence = ForeignKeyField(SequenceModel, backref='waypoints', null=True)
    wp_type = CharField()
    station = IntegerField(default=0)

    class Meta:
        database = db
