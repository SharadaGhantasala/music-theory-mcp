"""Print the API's OpenAPI schema: `python -m server.api.schema`. Used to generate TS types."""

import json

from server.api.app import create_app
from server.config import Settings

if __name__ == "__main__":
    app = create_app(Settings(database_url="sqlite:///:memory:", web_dist=""))
    print(json.dumps(app.openapi(), indent=2))
