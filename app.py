from flask import Flask, jsonify, make_response, request, Response
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid
import jwt
import datetime
import requests
import re
import sys
import copy

from gql import Client, gql
from gql.transport.exceptions import TransportQueryError
from gql.transport.requests import RequestsHTTPTransport

import logging

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)

app = Flask(__name__)
app.config["SECRET_KEY"] = "004f2af45d3a4e161a7dd2d17fdae47f"
FlaskInstrumentor().instrument_app(app)

filter_regex = r"\"?(.*)\"?$"


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if "x-access-tokens" in request.headers:
            token = request.headers["x-access-tokens"]
        elif "Authorization" in request.headers and request.headers[
            "Authorization"
        ].startswith("Bearer"):
            token = request.headers["Authorization"].split()[1]

        if not token:
            return jsonify({"message": "a valid token is missing"})
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            print(data)
        except:
            return jsonify({"message": "token is invalid"})

        return f(data, *args, **kwargs)

    return decorator


@app.route("/register", methods=["GET"])
def register():
    # 401 notauthorized

    token = None
    if "Authorization" in request.headers:
        authhdr = request.headers["Authorization"]
        logging.debug("Authorization Header found")
    if not authhdr:
        logging.debug("Authorization Header not found")
        return make_response(
            jsonify({"message": "Authorization Header is missing"}, 400)
        )
    if not authhdr.startswith("Bearer "):
        logging.debug("Authorization Header found but it is not a Bearer")
        return make_response(
            jsonify({"message": "Authorization Header is invalid must be bearer"}, 400)
        )
    data = request.get_json()
    if not "url" in data:
        logging.debug("Backend URI not provided")
        return make_response(jsonify({"message": "url field not in body"}, 400))
    url = data["url"]

    transport = RequestsHTTPTransport(
        url=url,
        verify=True,
        retries=3,
        headers={"Authorization": request.headers["Authorization"]},
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql(
        """
        query {
            currentUser{
                id,
                displayName,
                isRoot,
                isOrgRoot,
                email,
                countryCode
                    }
        }"""
    )
    try:
        logging.debug(query)
        result = client.execute(query)
        logging.debug(result)
        data = {
            "url": url,
            "Authorization": authhdr,
            "id": result["currentUser"]["id"],
            "displayName": result["currentUser"]["displayName"],
            "email": result["currentUser"]["email"],
        }
        token = jwt.encode(
            data,
            app.config["SECRET_KEY"],
            "HS256",
        )
        return jsonify({"token": token})
    except TransportQueryError:
        logging.exception("TransportQueryError")
        return user_not_found()


def user_not_found():
    response = make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": 0,
                "Resources": [],
                "startIndex": 1,
                "itemsPerPage": 20,
            }
        )
    )
    response.mimetype = "application/scim+json"
    return response


@app.route("/Users", methods=["GET"])
@token_required
def get_user(context):
    safecontext = {
        "url": context["url"],
        "url": context["email"],
        "displayName": context["displayName"],
    }
    logging.info(safecontext)
    if "filter" in request.args:
        filter = request.args.get("filter")
        logging.info(f"Filter {filter}")
        if filter.startswith("userName eq "):
            matches = re.findall(r"[^'\" ]+@[^'\" ]+", filter)
            key = matches[0]
            headers = {"Authorization": f"{context['Authorization']}"}

            transport = RequestsHTTPTransport(
                url=context["url"],
                verify=True,
                retries=3,
                headers=headers,
            )

            client = Client(transport=transport, fetch_schema_from_transport=True)

            query = gql(
                """
query {
    account(username: "$username"){
        id,
        username,
        isRoot,
        isOrganizationRoot,
        fullName,
        firstName,
        lastName,
        email,
        countryCode
    }
}""".replace(
                    "$username", key
                )
            )
            try:
                logging.debug(query)
                result = client.execute(query)
                logging.debug(result)
            except TransportQueryError:
                logging.exception("TransportQueryError")
                return user_not_found()
        else:
            logging.info(f"Invalid filter {filter}")
            return user_not_found()

        return user_not_found()
    else:
        return make_response(jsonify({"message": "Must use query"}, 400))


@app.route("/Users", methods=["POST"])
@token_required
def post_user(context):
    safecontext = {
        "url": context["url"],
        "url": context["email"],
        "displayName": context["displayName"],
    }
    logging.info(safecontext)
    logging.debug(request.json)
    userdata =request.json
    """
    'userName': 'wilson@okuneva.co.uk', 'name': {'familyName': 'Casandra', 'givenName': 'Ashly'}, 'displayName': 'WC0TTNUMRPK2', 'emails': [{'type': 'work', 'value': 'mack@monahan.ca', 'primary': True}], 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User']}
    """
    headers = {"Authorization": f"{context['Authorization']}"}

    transport = RequestsHTTPTransport(
        url=context["url"],
        verify=True,
        retries=3,
        headers=headers,
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)
    q =  """
mutation {
    addUserV2: addUserV2(input: {
    username: "$username",
    fullName: "$fullName",
    firstName: "firstName",
    lastName: "lastName",
    email: "$email"
    })
  {__typename}
}"""   
#company: "$company",
    #countryCode: "$countryCode",
    
    q = q.replace('$username',userdata['userName'])
    q = q.replace('$fullName',userdata['displayName'])
    q = q.replace('$firstName',userdata['name']['familyName'])
    q = q.replace('$lastName',userdata['name']['givenName'])
    for email in userdata['emails']:
        if email['primary']:
            q = q.replace('$email',email['value'])
    q = q.replace('$email',userdata['userName'])
    query = gql(q)
    try:
        logging.debug(query)
        result = client.execute(query)
        logging.debug(result)
        
    except TransportQueryError:
        logging.exception("TransportQueryError")
        return 500


# @app.route("/Users", methods=["GET"])
# @token_required
# def get_user(context):


@app.route("/Schemas", methods=["GET"])
@token_required
def get_schema(context):
    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "itemsPerPage": 50,
                "startIndex": 1,
                "totalResults": 3,
                "Resources": [
                    {
                        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
                        "id": "urn:ietf:params:scim:schemas:core:2.0:User",
                        "name": "User",
                        "description": "User Account",
                        "attributes": [
                            {
                                "name": "id",
                                "type": "string",
                                "multiValued": False,
                                "description": "Unique identifier entity. REQUIRED.",
                                "required": True,
                                "caseExact": True,
                                "mutability": "readOnly",
                                "returned": "default",
                                "uniqueness": "server",
                            },
                            {
                                "name": "userName",
                                "type": "string",
                                "multiValued": False,
                                "description": "Unique identifier for the User, typically used by the user to directly authenticate to the service provider. Each User MUST include a non-empty userName value.  This identifier MUST be unique across the service provider's entire set of Users. REQUIRED.",
                                "required": True,
                                "caseExact": False,
                                "mutability": "writeOnly",
                                "returned": "default",
                                "uniqueness": "server",
                            },
                            {
                                "name": "name",
                                "type": "complex",
                                "multiValued": False,
                                "description": "The components of the user's real name. Providers MAY return just the full name as a single string in the formatted sub-attribute, or they MAY return just the individual component attributes using the other sub-attributes, or they MAY return both.  If both variants are returned, they SHOULD be describing the same name, with the formatted name indicating how the component attributes should be combined.",
                                "required": False,
                                "subAttributes": [
                                    {
                                        "name": "familyName",
                                        "type": "string",
                                        "multiValued": False,
                                        "description": "The family name of the User, or last name in most Western languages (e.g., 'Jensen' given the full name 'Ms. Barbara J Jensen, III').",
                                        "required": False,
                                        "caseExact": False,
                                        "mutability": "readWrite",
                                        "returned": "default",
                                        "uniqueness": "none",
                                    },
                                    {
                                        "name": "givenName",
                                        "type": "string",
                                        "multiValued": False,
                                        "description": "The given name of the User, or first name in most Western languages (e.g., 'Barbara' given the full name 'Ms. Barbara J Jensen, III').",
                                        "required": False,
                                        "caseExact": False,
                                        "mutability": "readWrite",
                                        "returned": "default",
                                        "uniqueness": "none",
                                    },
                                ],
                                "mutability": "readWrite",
                                "returned": "default",
                                "uniqueness": "none",
                            },
                            {
                                "name": "displayName",
                                "type": "string",
                                "multiValued": False,
                                "description": "The name of the User, suitable for display to end-users.  The name SHOULD be the full name of the User being described, if known.",
                                "required": False,
                                "caseExact": False,
                                "mutability": "readWrite",
                                "returned": "default",
                                "uniqueness": "none",
                            },
                            {
                                "name": "emails",
                                "type": "complex",
                                "multiValued": True,
                                "description": "Email addresses for the user.  The value SHOULD be canonicalized by the service provider, e.g., 'bjensen@example.com' instead of 'bjensen@EXAMPLE.COM'. Canonical type values of 'work', 'home', and 'other'.",
                                "required": False,
                                "subAttributes": [
                                    {
                                        "name": "value",
                                        "type": "string",
                                        "multiValued": False,
                                        "description": "Email addresses for the user.  The value SHOULD be canonicalized by the service provider, e.g., 'bjensen@example.com' instead of 'bjensen@EXAMPLE.COM'. Canonical type values of 'work', 'home', and 'other'.",
                                        "required": False,
                                        "caseExact": False,
                                        "mutability": "readWrite",
                                        "returned": "default",
                                        "uniqueness": "none",
                                    },
                                    {
                                        "name": "type",
                                        "type": "string",
                                        "multiValued": False,
                                        "description": "A label indicating the attribute's function, e.g., 'work' or 'home'.",
                                        "required": False,
                                        "caseExact": False,
                                        "canonicalValues": ["work", "home", "other"],
                                        "mutability": "readWrite",
                                        "returned": "default",
                                        "uniqueness": "none",
                                    },
                                    {
                                        "name": "primary",
                                        "type": "boolean",
                                        "multiValued": False,
                                        "description": "A Boolean value indicating the 'primary' or preferred attribute value for this attribute, e.g., the preferred mailing address or primary email address.  The primary attribute value 'true' MUST appear no more than once.",
                                        "required": False,
                                        "mutability": "readWrite",
                                        "returned": "default",
                                    },
                                ],
                                "mutability": "readWrite",
                                "returned": "default",
                                "uniqueness": "none",
                            },
                        ],
                        "meta": {
                            "resourceType": "Schema",
                            "location": "/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User",
                        },
                    },
                    {
                        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
                        "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
                        "name": "Group",
                        "description": "Group",
                        "attributes": [
                            {
                                "name": "displayName",
                                "type": "string",
                                "multiValued": False,
                                "description": "A human-readable name for the Group. REQUIRED.",
                                "required": False,
                                "caseExact": False,
                                "mutability": "readWrite",
                                "returned": "default",
                                "uniqueness": "none",
                            },
                        ],
                        "meta": {
                            "resourceType": "Schema",
                            "location": "/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:Group",
                        },
                    },
                ],
            }
        ),
        200,
    )
