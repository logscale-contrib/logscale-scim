import time
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import sys
import os

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

LOGSCALE_GQL_MUTATION_ASSIGN_GROUP_TO_ORGANIZATION_ROLE = """mutation AssignOrganizationRoleToGroup($input: AssignOrganizationRoleToGroupInput!) {
  assignOrganizationRoleToGroup(input: $input) {
    group {
      role {
        displayName
      }
    }
  }
}"""
LOGSCALE_GQL_MUTATION_ASSIGN_GROUP_TO_CLUSTER_ROLE = """mutation AssignSystemRoleToGroup($input: AssignSystemRoleToGroupInput!) {
  assignSystemRoleToGroup(input: $input) {
    group {
      role {
        id
      }
    }
  }
}"""

LOGSCALE_GQL_MUTATION_ROLE_ADD = """mutation CreateRole($input: AddRoleInput!) {
  createRole(input: $input) {
    role {
      displayName
      id
    }
  }
}"""

LOGSCALE_GQL_MUTATION_ROLE_UPDATE = """mutation UpdateRole($input: UpdateRoleInput!) {
  updateRole(input: $input) {
    role {
      id
    }
  }
}"""

LOGSCALE_GQL_QUERY_ROLES = """query Roles {
  roles {
    id
    displayName
  }
}"""

LOGSCALE_GQL_QUERY_GROUP_BY_DISPLAY_NAME = """query GroupByDisplayName($displayName: String!) {
  groupByDisplayName(displayName: $displayName) {
    id    
    organizationRoles {
      role {
        displayName
        id
      }
    }
    systemRoles {
      role {
        id
        displayName
      }
    }
  }
}"""

LOGSCALE_SYSTEM_PERMISSIONS = [
    "ReadHealthCheck",
    "ManageCluster",
    "ChangeSystemPermissions",
]
LOGSCALE_ORG_PERMISSIONS = [
    "ChangeIPFilters",
    "DeleteAllViews",
    "DeleteAllRepositories",
    "ChangeSecurityPolicies",
    "ChangeOrganizationPermissions",
    "ViewAllInternalNotifications",
    "ChangeSessions",
    "ManageViewConnections",
    "IngestAcrossAllReposWithinOrganization",
    "ChangeFieldAliases",
    "CreateRepository",
    "ManageUsers",
    "ViewUsage",
    "ChangeTriggersToRunAsOtherUsers",
    "ViewFleetManagement",
    "ChangeAllViewOrRepositoryPermissions",
    "ChangeFleetManagement",
]

LOGSCALE_API_TOKEN = os.environ.get(
    "LOGSCALE_API_TOKEN",
    "i89DYiy1nZ2Gor5kv7a8Al1w~Uii4hoj25iq39bNrqcdDDYGxLGeEpYf8exOHlkRp1Vjj",
)
LOGSCALE_URL = os.environ.get(
    "LOGSCALE_URL", "https://logscale.weka2.ref.logsr.life/graphql"
)
LOGSCALE_ROLE_CLUSTER = os.environ.get(
    "LOGSCALE_ROLE_CLUSTER", "scim-management-cluster"
)
LOGSCALE_ROLE_ORGANIZATION = os.environ.get(
    "LOGSCALE_GROUP_ORGANIZATION", "scim-management-organization"
)

LOGSCALE_GROUP_CLUSTER = os.environ.get(
    "LOGSCALE_GROUP_CLUSTER", "logscale-management-cluster"
)
LOGSCALE_GROUP_ORGANIZATION = os.environ.get(
    "LOGSCALE_GROUP_ORGANIZATION", "logscale-management-organization"
)


def sync_logscale_roles(
    logscaleClient: Client,
    existingRoles: dict,
    roleName: str,
    groupName: str,
    assignmentMutation: str,
    organizationPermissions: list[str] = [],
    systemPermissions: list[str] = [],
    viewPermissions: list[str] = [],
):
    if roleName in existingRoles:
        logging.info(f"Role {roleName} exists")
        params = {
            "input": {
                "displayName": roleName,
                "roleId": existingRoles[roleName]["id"],
                "organizationPermissions": organizationPermissions,
                "systemPermissions": systemPermissions,
                "viewPermissions": viewPermissions,
            }
        }
        result = logscaleClient.execute(
            gql(LOGSCALE_GQL_MUTATION_ROLE_UPDATE), variable_values=params
        )
        logging.info(
            f"Role={roleName} action=updated id={existingRoles[roleName]['id']}"
        )
        roleid = existingRoles[roleName]["id"]
    else:
        logging.info(f"Role {roleName} does not exist")
        params = {
            "input": {
                "displayName": roleName,
                "organizationPermissions": organizationPermissions,
                "systemPermissions": systemPermissions,
                "viewPermissions": viewPermissions,
            }
        }
        result = logscaleClient.execute(
            gql(LOGSCALE_GQL_MUTATION_ROLE_ADD), variable_values=params
        )
        logging.info(
            f"Role={roleName} action=created id={result['createRole']['role']['id']}"
        )
        roleid = result["createRole"]["role"]["id"]

    logging.info(f"Role {roleName} id={roleid} assigned to group {groupName}")
    while True:
        params = {"displayName": groupName}
        try:
            group = logscaleClient.execute(
                gql(LOGSCALE_GQL_QUERY_GROUP_BY_DISPLAY_NAME), variable_values=params
            )

            break

        except TransportQueryError as e:
            if (
                e.errors[0]["message"] == "There were errors in the input."
                and e.errors[0]["state"][groupName] == "Group does not exist!"
            ):
                logging.info("Group Cluster not found waiting for it to be created")
                time.sleep(10)
            else:
                logging.exception("TransportQueryError")

    # LOGSCALE_GQL_MUTATION_ASSIGN_GROUP_TO_ROLE
    params = {
        "input": {
            "groupId": group["groupByDisplayName"]["id"],
            "roleId": roleid,
        }
    }
    logscaleClient.execute(
        gql(assignmentMutation),
        variable_values=params,
    )


def main():
    headers = {"Authorization": f"Bearer {LOGSCALE_API_TOKEN}"}

    transport = RequestsHTTPTransport(
        url=LOGSCALE_URL, verify=True, retries=3, headers=headers
    )

    logscaleClient = Client(transport=transport, fetch_schema_from_transport=False)

    roles = logscaleClient.execute(gql(LOGSCALE_GQL_QUERY_ROLES))
    existingRoles = {}
    for role in roles["roles"]:
        if role["displayName"] not in ["Admin", "Member", "Deleter"]:
            existingRoles[role["displayName"]] = {"id": role["id"]}

    logging.info(f"Roles: {existingRoles}")

    sync_logscale_roles(
        logscaleClient,
        existingRoles,
        LOGSCALE_ROLE_ORGANIZATION,
        LOGSCALE_GROUP_ORGANIZATION,
        LOGSCALE_GQL_MUTATION_ASSIGN_GROUP_TO_ORGANIZATION_ROLE,
        organizationPermissions=LOGSCALE_ORG_PERMISSIONS,
    )
    sync_logscale_roles(
        logscaleClient,
        existingRoles,
        LOGSCALE_ROLE_CLUSTER,
        LOGSCALE_GROUP_CLUSTER,
        LOGSCALE_GQL_MUTATION_ASSIGN_GROUP_TO_CLUSTER_ROLE,
        systemPermissions=LOGSCALE_SYSTEM_PERMISSIONS,
    )


if __name__ == "__main__":
    main()
