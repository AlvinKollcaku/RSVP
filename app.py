import os
from DB import db
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from blocklist import BLOCKLIST
from flask_migrate import Migrate
from resources.event import blp as eventBlueprint
from resources.rsvp import blp as rsvpBlueprint
from resources.tag import blp as tagBlueprint
from resources.user import blp as userBlueprint

# get - libraries,books via IDs and from books get library it belongsTo
# post - libraries,books

def create_app(db_url=None):
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True  # if an exception happens in flask extension
    # propagate it to main app
    app.config["API_TITLE"] = "Stores REST API"  # flask-smorest documentation
    app.config["API_VERSION"] = "v1"  # flask-smorest documentation
    app.config["OPENAPI_VERSION"] = "3.0.3"  # standard for documentation->flask-sm will use V:3.0.3
    app.config["OPENAPI_URL_PREFIX"] = "/"  # tells flask-smorest where the root of the API is
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"  # documentation config
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    # it tells flask smorest to use swagger-ui for documentation and the swagger code is in the above URL
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    #1)we use db_url variable if defined and if not we use the environment variable for postgres
    #1) that we have defined and if we havent defined that we use sqlite which will create a data.db file
    #1)using environment variables to connect to DB so that you dont share the info when sharing the code
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app) # connecting both apps
    migrate = Migrate(app, db)
    api = Api(app)

    app.config["JWT_SECRET_KEY"] = "249751419766024081467219411349889851747" #Not used for encryption
    #It is use to validate that the current JWT that the client has for the current user is generated
    #by this API and not generated by somewhere else pretending to have generated from here
    #The secret key is usually stored in ENVIRONMENT VARIABLES
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader #whenever you receive a JWT this function runs
    def check_if_token_in_blocklist(jwt_header,jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST #the callback below defines the error message if this returns true

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header,jwt_payload):
        return (
            jsonify(
                {"description":"The token has been revoked","error":"token_revoked"}
            ),
            401,
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        #Normally you would do a database or a config file reading here
        if identity == 1:
            return {"is_admin": True}
        else:
            return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
            {"message":"The token has expired","error":"expired_token"},401,
            ),401
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
            {"message": "Signature verification failed", "error": "invalid_token"}
            ),401
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
            {
                "description": "Signature verification failed",
                "error": "authorization_required"
                }
            ),401
        )

    api.register_blueprint(eventBlueprint)
    api.register_blueprint(rsvpBlueprint)
    api.register_blueprint(tagBlueprint)
    api.register_blueprint(userBlueprint)
    return app

app = create_app()

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == '__main__':
    app.run()

