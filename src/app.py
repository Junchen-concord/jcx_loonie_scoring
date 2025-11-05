from flask import Flask, request, jsonify
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec import FlaskApiSpec, doc, marshal_with, use_kwargs
from Plaid_Model.model import ibvmodel
from ND_Model.model import ndmodeling
from IsGood_Model.model import isgoodmodel
from werkzeug.exceptions import HTTPException
from api_types.errors import BadRequestSchema, GenericErrorSchema, HTTPErrorSchema
from api_types.nd import NDOutput, NDPayloadSchema
from config import MODEL_VERSION
import json
from config import logger
from app_utils import run
from api_types.health import HealthCheckResponse
from api_types.plaid import PlaidOutput, PlaidPayloadSchema


# Helpers
def _validate_json_content_type(request):
    """Validates that the request content type is application/json."""
    if not request.is_json:
        return jsonify(
            {
                "error": "Invalid Content-Type",
                "message": "Request must be application/json",
            }
        ), 400
    return None


def _validate_non_empty_json_body(json_data):
    """Validates that the JSON body is not empty."""
    if not json_data:
        return jsonify({"error": "Invalid Request", "message": "Request body cannot be empty"}), 400
    return None


def _run_model_prediction(model_function, json_data, **kwargs):
    """Runs the specified model prediction function."""
    try:
        result = model_function(json_data, **kwargs)
        return result
    except json.JSONDecodeError as e:
        return jsonify(
            {
                "error": "Invalid JSON",
                "message": "Failed to decode JSON payload",
                "detail": str(e),
            }
        ), 400
    except Exception:
        # Let the global error handler catch other exceptions
        raise


def create_app():
    app = Flask(__name__)

    # --- Error Handlers ---
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        """Handle HTTP errors."""
        response = e.get_response()
        response.data = json.dumps(
            {
                "code": e.code,
                "name": e.name,
                "description": e.description,
            }
        )
        response.content_type = "application/json"
        return response

    @app.errorhandler(400)
    def handle_bad_request(e):
        """Handle bad request errors, including invalid JSON."""
        return jsonify(
            {
                "error": "Bad Request",
                "message": str(e),
                "detail": "The request payload is not valid JSON or is missing required fields",
            }
        ), 400

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        """Handle all other errors."""
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

    # --- Routes ---
    @marshal_with(HealthCheckResponse, code=200)
    @doc(description="Liveness probe.", tags=["Health"])
    @app.route("/liveness")
    def liveness():
        return jsonify(
            {
                "status": 200,
                "message": "health check succeeded",
                "modelVersion": MODEL_VERSION,
            }
        ), 200

    @marshal_with(HealthCheckResponse, code=200)
    @doc(description="Readiness probe.", tags=["Health"])
    @app.route("/readiness")
    def readiness():
        return jsonify(
            {
                "status": 200,
                "message": "health check succeeded",
                "modelVersion": MODEL_VERSION,
            }
        ), 200

    @use_kwargs(PlaidPayloadSchema)
    @marshal_with(PlaidOutput, code=200)
    @marshal_with(BadRequestSchema, code=400)
    @marshal_with(HTTPErrorSchema, code=404)
    @marshal_with(GenericErrorSchema, code=500)
    @doc(description="Runs the Plaid_Model", tags=["Plaid Model"])
    @app.route("/api/v1/plaidModel", methods=["POST"])
    def plaid_model():
        logger.info("[POST] /api/v1/plaidModel")
        content_type_error = _validate_json_content_type(request)
        if content_type_error:
            return content_type_error

        json_data = request.get_json()
        empty_body_error = _validate_non_empty_json_body(json_data)
        if empty_body_error:
            return empty_body_error

        return _run_model_prediction(
            ibvmodel,
            json_data,
        )

    @use_kwargs(NDPayloadSchema)
    @marshal_with(NDOutput, code=200)
    @marshal_with(BadRequestSchema, code=400)
    @marshal_with(HTTPErrorSchema, code=404)
    @marshal_with(GenericErrorSchema, code=500)
    @doc(description="Runs the ND_Model", tags=["ND Model"])
    @app.route("/api/v1/ndModel", methods=["POST"])
    def nd_model():
        logger.info("[POST] /api/v1/ndModel")
        content_type_error = _validate_json_content_type(request)
        if content_type_error:
            return content_type_error

        json_data = request.get_json()
        empty_body_error = _validate_non_empty_json_body(json_data)
        if empty_body_error:
            return empty_body_error

        return _run_model_prediction(
            ndmodeling,
            json_data,
        )

    @use_kwargs(PlaidPayloadSchema)
    @marshal_with(PlaidOutput, code=200)
    @marshal_with(BadRequestSchema, code=400)
    @marshal_with(HTTPErrorSchema, code=404)
    @marshal_with(GenericErrorSchema, code=500)
    @doc(description="Runs the IsGood_Model", tags=["Is Good Model"])
    @app.route("/api/v1/isGoodModel", methods=["POST"])
    def is_good_model():
        logger.info("[POST] /api/v1/isGoodModel")
        content_type_error = _validate_json_content_type(request)
        if content_type_error:
            return content_type_error

        json_data = request.get_json()
        empty_body_error = _validate_non_empty_json_body(json_data)
        if empty_body_error:
            return empty_body_error
        return _run_model_prediction(
            isgoodmodel,
            json_data,
        )

    # ===============================
    # Docs
    # ===============================

    spec = APISpec(
        title="Loonie_Scoringv16 Model Service",
        version=MODEL_VERSION,
        # openapi_version="3.0.2",
        openapi_version="2.0",
        plugins=[MarshmallowPlugin()],
        serve=True,
        swagger_ui=True,
    )

    app.config.update(
        {
            "APISPEC_SPEC": spec,
            "APISPEC_SWAGGER_URL": "/swagger/",
            "APISPEC_SWAGGER_UI_URL": "/swagger-ui/",
        }
    )

    docs = FlaskApiSpec(app)
    docs.register(liveness)
    docs.register(readiness)
    docs.register(plaid_model)
    docs.register(nd_model)
    docs.register(is_good_model)

    return app


if __name__ == "__main__":
    app = create_app()
    run(app)
