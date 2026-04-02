from fastapi.testclient import TestClient
from app.main import app
import asyncio

# This is a simplified test setup. 
# In a real scenario, you'd use a test database.

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to VerbumLab API"}

def test_auth_routes_exist():
    # Verify that the routes are registered
    routes = [route.path for route in app.routes]
    assert "/api/v1/auth/register" in routes
    assert "/api/v1/auth/login" in routes
    assert "/api/v1/users/me" in routes
    assert "/api/v1/users/me/password" in routes

if __name__ == "__main__":
    test_read_main()
    test_auth_routes_exist()
    print("Basic route verification passed!")
