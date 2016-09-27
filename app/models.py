from app import db


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(40))
    username = db.Column(db.String(30))


class phone_number(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(40))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
