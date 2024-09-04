import requests,os
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema,fields
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity, jwt_required, get_jwt
from flask import jsonify

from DB import db
from models import UserModel, RsvpModel
from schemas import UserSchema, RsvpSchema, PlainRsvpSchema,RsvpUpdateSchema

class LoginSchema(Schema):
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)

blp = Blueprint("Rsvps", "rspvs", description="Operations on users")

@blp.route('/rsvp/<int:event_id>')
class Rsvp(MethodView):
    @jwt_required()
    @blp.arguments(PlainRsvpSchema)
    @blp.response(201, RsvpSchema)
    def post(self, data, event_id): #creating a new rsvp for the logged in user
        current_user_id = get_jwt_identity()

        if RsvpModel.query.filter_by(event_id=event_id, user_id=current_user_id).first():
            abort(400, message="You have already RSVP'd to this event.")

        rsvp = RsvpModel(event_id=event_id, **data, user_id=current_user_id)

        try:
            db.session.add(rsvp)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, message="An error occurred while creating the RSVP.")

        return rsvp

    @jwt_required()
    @blp.arguments(RsvpUpdateSchema)
    @blp.response(200, RsvpSchema)
    def put(self, data, rsvp_id):
        rsvp = RsvpModel.query.get_or_404(rsvp_id)
        rsvp.status = data.get("status", rsvp.status)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, message="An error occurred while updating the RSVP.")

        return rsvp

