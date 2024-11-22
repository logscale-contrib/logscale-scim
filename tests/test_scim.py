import pytest
import json

def test_get_user(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "user": {
            "id": "1",
            "userName": "testuser",
            "emails": [{"value": "testuser@example.com"}]
        }
    }
    response = client.get('/Users/1', headers={"Authorization": "Bearer test_scim_token"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "1"
    assert data["userName"] == "testuser"
    assert data["emails"][0]["value"] == "testuser@example.com"

def test_create_user(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "createUser": {
            "user": {
                "id": "1",
                "userName": "testuser",
                "emails": [{"value": "testuser@example.com"}]
            }
        }
    }
    new_user = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "testuser",
        "emails": [{"value": "testuser@example.com"}],
        "password": "password123"
    }
    response = client.post('/Users', headers={"Authorization": "Bearer test_scim_token"}, json=new_user)
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == "1"
    assert data["userName"] == new_user["userName"]
    assert data["emails"][0]["value"] == new_user["emails"][0]["value"]

def test_replace_user(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "replaceUser": {
            "user": {
                "id": "1",
                "userName": "updateduser",
                "emails": [{"value": "updateduser@example.com"}]
            }
        }
    }
    updated_user = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "updateduser",
        "emails": [{"value": "updateduser@example.com"}],
        "password": "newpassword123"
    }
    response = client.put('/Users/1', headers={"Authorization": "Bearer test_scim_token"}, json=updated_user)
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "1"
    assert data["userName"] == updated_user["userName"]
    assert data["emails"][0]["value"] == updated_user["emails"][0]["value"]

def test_update_user(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "updateUser": {
            "user": {
                "id": "1",
                "userName": "testuser",
                "emails": [{"value": "partialupdate@example.com"}]
            }
        }
    }
    partial_update = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "replace",
                "path": "emails[value eq \"testuser@example.com\"].value",
                "value": "partialupdate@example.com"
            }
        ]
    }
    response = client.patch('/Users/1', headers={"Authorization": "Bearer test_scim_token"}, json=partial_update)
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "1"
    assert data["emails"][0]["value"] == "partialupdate@example.com"

def test_delete_user(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "deleteUser": {
            "id": "1"
        }
    }
    response = client.delete('/Users/1', headers={"Authorization": "Bearer test_scim_token"})
    assert response.status_code == 204

def test_get_group(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "group": {
            "id": "1",
            "displayName": "testgroup"
        }
    }
    response = client.get('/Groups/1', headers={"Authorization": "Bearer test_scim_token"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "1"
    assert data["displayName"] == "testgroup"

def test_create_group(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "createGroup": {
            "group": {
                "id": "1",
                "displayName": "testgroup"
            }
        }
    }
    new_group = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "testgroup"
    }
    response = client.post('/Groups', headers={"Authorization": "Bearer test_scim_token"}, json=new_group)
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == "1"
    assert data["displayName"] == new_group["displayName"]

def test_replace_group(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "replaceGroup": {
            "group": {
                "id": "1",
                "displayName": "updatedgroup"
            }
        }
    }
    updated_group = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "updatedgroup"
    }
    response = client.put('/Groups/1', headers={"Authorization": "Bearer test_scim_token"}, json=updated_group)
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "1"
    assert data["displayName"] == updated_group["displayName"]

def test_update_group(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "updateGroup": {
            "group": {
                "id": "1",
                "displayName": "partialupdategroup"
            }
        }
    }
    partial_update = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "replace",
                "path": "displayName",
                "value": "partialupdategroup"
            }
        ]
    }
    response = client.patch('/Groups/1', headers={"Authorization": "Bearer test_scim_token"}, json=partial_update)
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "1"
    assert data["displayName"] == partial_update["Operations"][0]["value"]

def test_delete_group(client, mock_graphql_client):
    mock_graphql_client.execute.return_value = {
        "deleteGroup": {
            "id": "1"
        }
    }
    response = client.delete('/Groups/1', headers={"Authorization": "Bearer test_scim_token"})
    assert response.status_code == 204