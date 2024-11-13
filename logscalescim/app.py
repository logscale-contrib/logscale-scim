import os
from flask import Flask, jsonify, make_response, request, Response
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import sys

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

LOGSCALE_SCIM_PATH_PREFIX = "/api/ext/scim/v2"

LOGSCALE_GQL_MUTATION_GROUP_ADD = """mutation AddGroup($displayName: String!, $lookupName: String) {
  addGroup(displayName: $displayName, lookupName: $lookupName) {
    group {
      id
    }
  }
}"""
LOGSCALE_GQL_MUTATION_GROUP_UPDATE = """mutation UpdateGroup($input: UpdateGroupInput!) {
  updateGroup(input: $input) {
    group {
      id
      lookupName
    }
  }
}"""

LOGSCALE_GQL_MUTATION_GROUP_DELETE = """mutation RemoveGroup($groupId: String!) {
  removeGroup(groupId: $groupId) {
    group {
      id
      lookupName
    }
  }
}"""

LOGSCALE_GQL_MUTATION_GROUP_ADD_USERS = """mutation AddUsersToGroup($input: AddUsersToGroupInput!) {
  addUsersToGroup(input: $input) {
    group {
      id
      lookupName
    }
  }
}"""

LOGSCALE_GQL_MUTATION_GROUP_REMOVE_USERS = """mutation RemoveUsersFromGroup($input: RemoveUsersFromGroupInput!) {
  removeUsersFromGroup(input: $input) {
    group {
      id
    }
  }
}"""


LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID = """mutation UpdateUserById($input: UpdateUserByIdInput!) {
  updateUserById(input: $input) {
    user {
      id
    }
  }
}"""
LOGSCALE_GQL_MUTATION_USER_ADD = """mutation AddUserV2($input: AddUserInputV2!) {
  addUserV2(input: $input) {
    ... on User {
      id
    }
  }
}"""

LOGSCALE_GQL_MUTATION_USER_REMOVE = """mutation RemoveUserById($input: RemoveUserByIdInput!) {
  removeUserById(input: $input) {
    user {
      id
    }
  }
}"""

LOGSCALE_GQL_QUERY_GROUP_BY_DISPLAY_NAME = """query GroupByDisplayName($displayName: String!) {
  groupByDisplayName(displayName: $displayName) {
    id
  }
}"""

LOGSCALE_GQL_QUERY_GROUP_BY_ID = """query Group($groupId: String!) {
  group(groupId: $groupId) {
    id
  }
}"""

LOGSCALE_API_TOKEN = os.environ.get(
    "LOGSCALE_API_TOKEN",
    "",
)
LOGSCALE_URL = os.environ.get(
    "LOGSCALE_URL", ""
)
SCIM_TOKEN  = os.environ.get(
    "SCIM_TOKEN", ""
)
application = Flask(__name__)
app = application

FlaskInstrumentor().instrument_app(app)

filter_regex = r"\"?(.*)\"?$"

headers = {"Authorization": f"Bearer {LOGSCALE_API_TOKEN}"}

transport = RequestsHTTPTransport(
    url=LOGSCALE_URL, verify=False, retries=3, headers=headers
)

logscaleClient = Client(transport=transport, fetch_schema_from_transport=False)


@app.errorhandler(Exception)
def handle_exception(e):
    # log the exception
    logging.exception("Exception occurred")
    # return a custom error page or message
    return make_response(jsonify({"exception": e}), 500)


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if request.authorization and request.authorization.type == "bearer":
            token = request.authorization.token
        elif "x-access-tokens" in request.headers:
            token = request.headers["x-access-tokens"]

        if not token:
            return jsonify({"message": "a valid token is missing"})

        if token == SCIM_TOKEN:
            return f(jsonify({"message": "authorized"}), *args, **kwargs)
        else:
            raise Exception("Invalid token")

    return decorator

@app.route("/", methods=["GET"])
def get_root():

    response = make_response(
        jsonify(
            {
                "result": "success"
            }
        ),
        200,
    )
    response.mimetype = "application/scim+json"
    return response

@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/ServiceProviderConfig", methods=["GET"])
def get_service_provider_config():
    safecontext = {}
    logging.info(safecontext)

    response = make_response(
        jsonify(
            {
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"
                ],
                "patch": {"supported": True},
                "bulk": {"supported": True, "maxOperations": 10, "maxPayloadSize": 0},
                "filter": {"supported": False, "maxResults": 25},
                "changePassword": {"supported": False},
                "sort": {"supported": False},
                "etag": {"supported": False},
                "authenticationSchemes": [
                    {
                        "name": "OAuth Bearer Token",
                        "description": "Authentication scheme using the OAuth Bearer Token Standard",
                        "specUri": "http://www.rfc-editor.org/info/rfc6750",
                        "documentationUri": "https://developer.xurrent.com/v1/oauth/",
                        "type": "oauthbearertoken",
                        "primary": True,
                    }
                ],
                "meta": {
                    "location": f"{request.base_url}/scim/v2/ServiceProviderConfig",
                    "resourceType": "ServiceProviderConfig",
                    "created": "2024-10-06T00:00Z",
                    "lastModified": "2024-10-06T00:00Z",
                    "version": "1",
                },
            }
        ),
        200,
    )
    response.mimetype = "application/scim+json"
    return response


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


def lookup_user_by_email(username, email):

    query = gql(
        """query Users($search: String) {
  users(search: $search) {id,username, email, displayName}
}"""
    )
    params = {"search": email}
    try:
        result = logscaleClient.execute(query, variable_values=params)
        logging.debug(result)
        for user in result["users"]:
            if user["email"] == email and user["username"] == username:
                return user["id"]
        for user in result["users"]:
            if user["email"] == email:
                return user["id"]

    except TransportQueryError:
        logging.exception("TransportQueryError")

    return None


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Users", methods=["POST"])
@token_required
def user_post(context):

    logging.debug(request.json)
    userdata = request.json
    """
    {'userName': 'akadmin', 'name': {'formatted': 'authentik Default Admin', 'familyName': 'Default Admin', 'givenName': 'authentik'}, 'displayName': 'authentik Default Admin', 'active': True, 'emails': [{...}], 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'], 'externalId': 'e89f4b0dcc531b703369420fbe0d6504b8f5c8a5fc419527358d07308a47b3c7'}
    """

    # [{'message': 'Variable \'$input\' expected value of type \'AddUserInputV2!\' but got: {"displayName":"authentik Default Admin","email":"ryan.faircloth@crowdstrike.com","firstName":"authentik","lastName":"Default Admin","username":"akadmin"}. Reason: \'displayName\' Field \'displayName\' is not defined in the input type \'AddUserInputV2\'. (line 1, column 20):\nmutation AddUserV2($input: AddUserInputV2!) {\n                   ^', 'locations': [...], 'isHumioUpdating': False}]
    for email in userdata["emails"]:
        if email["primary"]:
            email = email["value"]

    existingID = lookup_user_by_email(userdata["userName"], email)
    if existingID:
        resultkey = "updateUserById"
        query = gql(LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID)
        params = {
            "input": {"userId": existingID, "fullName": userdata["name"]["formatted"]}
        }
        if "familyName" in userdata["name"]:
            params["input"]["lastName"] = userdata["name"]["familyName"]
        if "givenName" in userdata["name"]:
            params["input"]["firstName"] = userdata["name"]["givenName"]
        for email in userdata["emails"]:
            if email["primary"]:
                params["input"]["email"] = email["value"]

        try:
            logging.debug(query)
            result = logscaleClient.execute(query, variable_values=params)
            logging.debug(result)

        except TransportQueryError as e:
            logging.exception("TransportQueryError")
            return "", 500
        id = result[resultkey]["user"]["id"]
    else:
        resultkey = "addUserV2"
        query = gql(LOGSCALE_GQL_MUTATION_USER_ADD)

        params = {
            "input": {
                "fullName": userdata["name"]["formatted"],
                "username": userdata["userName"],
            }
        }
        if "familyName" in userdata["name"]:
            params["input"]["lastName"] = userdata["name"]["familyName"]
        if "givenName" in userdata["name"]:
            params["input"]["firstName"] = userdata["name"]["givenName"]
        for email in userdata["emails"]:
            if email["primary"]:
                params["input"]["email"] = email["value"]

        try:
            logging.debug(query)
            result = logscaleClient.execute(query, variable_values=params)
            logging.debug(result)

        except TransportQueryError as e:
            logging.exception("TransportQueryError")
            return "", 500

        id = result[resultkey]["id"]

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": id,
                "externalId": userdata["externalId"],
                "meta": {
                    "location": f"{request.base_url}/Users/{id}",
                    "resourceType": "User",
                    "created": "2024-10-06T00:00Z",
                    "lastModified": "2024-10-06T00:00Z",
                },
            }
        ),
        201,
    )


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Users/<id>", methods=["PUT"])
@token_required
def user_put(context, *args, **kwargs):

    logging.debug(request.json)
    userdata = request.json
    """
    {'userName': 'akadmin', 'name': {'formatted': 'authentik Default Admin', 'familyName': 'Default Admin', 'givenName': 'authentik'}, 'displayName': 'authentik Default Admin', 'active': True, 'emails': [{...}], 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'], 'externalId': 'e89f4b0dcc531b703369420fbe0d6504b8f5c8a5fc419527358d07308a47b3c7'}
    """

    resultkey = "updateUserById"
    query = gql(LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID)
    params = {
        "input": {"userId": kwargs["id"], "fullName": userdata["name"]["formatted"]}
    }
    if "familyName" in userdata["name"]:
        params["input"]["lastName"] = userdata["name"]["familyName"]
    if "givenName" in userdata["name"]:
        params["input"]["firstName"] = userdata["name"]["givenName"]
    for email in userdata["emails"]:
        if email["primary"]:
            params["input"]["email"] = email["value"]

    try:
        logging.debug(query)
        result = logscaleClient.execute(query, variable_values=params)
        logging.debug(result)

    except TransportQueryError as e:
        logging.exception("TransportQueryError")
        return "", 500

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": result[resultkey]["user"]["id"],
                "externalId": kwargs["id"],
                "meta": {
                    "location": f"{request.base_url}/Users/{kwargs['id']}",
                    "resourceType": "Group",
                    "created": "2024-10-06T00:00Z",
                    "lastModified": "2024-10-06T00:00Z",
                },
            }
        ),
        201,
    )


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Users/<id>", methods=["DELETE"])
@token_required
def user_delete(context, *args, **kwargs):

    query = gql(LOGSCALE_GQL_MUTATION_USER_REMOVE)
    params = {"input": {"id": kwargs["id"]}}

    try:
        logging.debug(query)
        result = logscaleClient.execute(query, variable_values=params)
        logging.debug(result)

    except TransportQueryError as e:
        logging.exception("TransportQueryError")
        return "", 500

    return "", 204


def get_group_by_id(id):

    params = {{"groupId": id}}
    logscaleClient.execute(gql(LOGSCALE_GQL_QUERY_GROUP_BY_ID), variable_values=params)


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Groups", methods=["POST"])
@token_required
def groups_post(context):

    logging.info(request.json)
    userdata = request.json
    """
    {'displayName': 'authentik Admins', 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:Group'], 'externalId': '433a38d7-721c-424f-adb7-9ee1b8b87608'}
    """

    params = {
        "displayName": userdata["displayName"],
        "lookupName": userdata["externalId"],
    }

    query = gql(LOGSCALE_GQL_MUTATION_GROUP_ADD)
    try:
        logging.debug(query)
        result = logscaleClient.execute(query, variable_values=params)
        logging.debug(result)

    except TransportQueryError:
        logging.exception("TransportQueryError")
        return "", 500

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": result["addGroup"]["group"]["id"],
                "externalId": userdata["externalId"],
                "meta": {
                    "location": f"{request.base_url}/scim/v2/ServiceProviderConfig",
                    "resourceType": "Group",
                    "created": "2024-10-06T00:00Z",
                    "lastModified": "2024-10-06T00:00Z",
                },
            }
        ),
        201,
    )


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Groups/<id>", methods=["PUT"])
@token_required
def groups_put(context, *args, **kwargs):
    safecontext = {}
    logging.info(safecontext)
    logging.info(request.json)
    userdata = request.json
    """
    {'id': 'hyKYMwxAUd54lnAc6i2TYI39jDBonrVV', 'displayName': 'authentik Admins', 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:Group'], 'externalId': '433a38d7-721c-424f-adb7-9ee1b8b87608'}
    """

    params = {
        "input": {
            "groupId": kwargs["id"],
            "displayName": userdata["displayName"],
            "lookupName": userdata["externalId"],
        }
    }

    query = gql(LOGSCALE_GQL_MUTATION_GROUP_UPDATE)

    try:

        result = logscaleClient.execute(query, variable_values=params)
        logging.debug(result)

    except TransportQueryError:
        logging.exception("TransportQueryError")
        return "", 500

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": result["updateGroup"]["group"]["id"],
                "externalId": userdata["externalId"],
                "meta": {
                    "location": f"{request.base_url}/Groups/{result['updateGroup']['group']['id']}",
                    "resourceType": "Group",
                    "created": "2024-10-06T00:00Z",
                    "lastModified": "2024-10-06T00:00Z",
                },
            }
        ),
        200,
    )


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Groups/<id>", methods=["PATCH"])
@token_required
def groups_patch(context, *args, **kwargs):
    safecontext = {}
    logging.info(safecontext)
    logging.info(request.json)
    userdata = request.json
    """
    {'Operations': [{...}], 'schemas': ['urn:ietf:params:scim:api:messages:2.0:PatchOp']}
    [{'op': 'replace', 'path': 'displayName', 'value': 'weka2-logscale-usersx'}]
    {'op': 'add', 'path': 'members', 'value': [{'value': 'b0PWHGSfJGY97Cjd37eQ81nv'}]}
    """

    """
    {"Operations": [
        {"op": "add", "path": "members", "value": [{"value": "b0PWHGSfJGY97Cjd37eQ81nv"}]}, {"op": "add", "path": "members", "value": [{"value": "BTckjpsawMXSMJZf0PbQUQMJ"}]}], "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]}
    """

    # for operation in userdata['Operations']
    for operation in userdata["Operations"]:
        params = {
            "input": {
                "groupId": kwargs["id"],
            }
        }
        if operation["op"] == "replace":
            resultkey = "updateGroup"
            query = gql(LOGSCALE_GQL_MUTATION_GROUP_UPDATE)
            if "displayName" in userdata["Operations"][0]["path"]:
                params["input"]["displayName"] = userdata["Operations"][0]["value"]

            if "externalId" in userdata["Operations"][0]["path"]:
                params["input"]["lookupName"] = userdata["Operations"][0]["value"]
        elif operation["op"] == "add" and operation["path"] == "members":
            resultkey = "addUsersToGroup"
            query = gql(LOGSCALE_GQL_MUTATION_GROUP_ADD_USERS)
            params["input"]["groupId"] = kwargs["id"]
            params["input"]["users"] = []
            for value in operation["value"]:
                params["input"]["users"].append(value["value"])
        elif operation["op"] == "remove" and operation["path"] == "members":
            resultkey = "addUsersToGroup"
            query = gql(LOGSCALE_GQL_MUTATION_GROUP_REMOVE_USERS)
            params["input"]["groupId"] = kwargs["id"]
            params["input"]["users"] = []
            for value in operation["value"]:
                params["input"]["users"].append(value["value"])

        try:
            result = logscaleClient.execute(query, variable_values=params)
            logging.debug(result)

        except TransportQueryError:
            logging.exception("TransportQueryError")
            return "", 500

    return "", 204


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Groups/<id>", methods=["DELETE"])
@token_required
def groups_delete(context, *args, **kwargs):

    params = {"groupId": kwargs["id"]}

    query = gql(LOGSCALE_GQL_MUTATION_GROUP_DELETE)

    try:

        result = logscaleClient.execute(query, variable_values=params)
        logging.debug(result)

    except TransportQueryError:
        logging.exception("TransportQueryError")
        return "", 500

    return "", 204


@app.route(f"{LOGSCALE_SCIM_PATH_PREFIX}/Schemas", methods=["GET"])
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


if __name__ == "__main__":
    app.run(debug=True)
