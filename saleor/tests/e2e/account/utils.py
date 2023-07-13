from ..utils import get_graphql_content

ACCOUNT_REGISTER_MUTATION = """
mutation AccountRegister($input: AccountRegisterInput!) {
  accountRegister(input: $input) {
    errors {
      field
      message
      code
    }
    requiresConfirmation
    user{
      id
      email
    }
  }
}
"""


def account_register(
    e2e_not_logged_api_client,
    email,
    password,
    channel_slug,
    redirectUrl="http://localhost:3000/",
):
    variables = {
        "input": {
            "email": email,
            "password": password,
            "channel_slug": channel_slug,
            "redirectUrl": redirectUrl,
        }
    }

    response = e2e_not_logged_api_client.post_graphql(
        ACCOUNT_REGISTER_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["accountRegister"]["errors"] == []

    data = content["data"]["accountRegister"]["user"]
    assert data["id"] is not None
    assert data["email"] == email

    return data
