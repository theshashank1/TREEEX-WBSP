import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from server.api.auth import Provider, Signup, signin, signup
from server.schemas.auth import SigninResponse, SignupResponse


class TestAuthRefreshToken(unittest.IsolatedAsyncioTestCase):
    async def test_signin_returns_refresh_token(self):
        # Mock dependencies
        session_dep = MagicMock()
        session_dep.execute = AsyncMock()
        session_dep.rollback = AsyncMock()
        session_dep.commit = AsyncMock()
        session_dep.refresh = AsyncMock()

        supabase_dep = MagicMock()

        # Mock Supabase response
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email_confirmed_at = "2023-01-01T00:00:00Z"

        mock_session = MagicMock()
        mock_session.access_token = "mock_access_token"
        mock_session.refresh_token = "mock_refresh_token"

        supabase_response = MagicMock()
        supabase_response.user = mock_user
        supabase_response.session = mock_session

        supabase_dep.auth.sign_in_with_password.return_value = supabase_response

        # Mock DB User
        mock_db_user = MagicMock()
        mock_db_user.id = mock_user.id
        # scalar_one_or_none result
        session_dep.execute.return_value.scalar_one_or_none.return_value = mock_db_user

        # Input data
        data = Signup(email="test@example.com", password="password")

        # Call endpoint
        # Call endpoint
        try:
            response = await signin(data, session_dep, supabase_dep, Provider.email)
        except Exception as e:
            if hasattr(e, "detail"):
                print(f"Signin failed with detail: {e.detail}")
            print(f"Signin failed with exception: {e}")
            raise e

        # Verify
        self.assertIsInstance(response, SigninResponse)
        self.assertEqual(response.refresh_token, "mock_refresh_token")
        self.assertEqual(response.access_token, "mock_access_token")

    async def test_signup_returns_refresh_token(self):
        # Mock dependencies
        session_dep = MagicMock()
        session_dep.add = MagicMock()
        session_dep.commit = AsyncMock()
        session_dep.refresh = AsyncMock()
        session_dep.execute = AsyncMock()

        supabase_dep = MagicMock()

        # Mock Supabase response
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email_confirmed_at = "2023-01-01T00:00:00Z"

        mock_session = MagicMock()
        mock_session.access_token = "mock_access_token"
        mock_session.refresh_token = "mock_refresh_token"

        supabase_response = MagicMock()
        supabase_response.user = mock_user
        supabase_response.session = mock_session

        supabase_dep.auth.sign_up.return_value = supabase_response

        # Input data
        data = Signup(email="test@example.com", password="password", name="Test")

        # Call endpoint
        try:
            response = await signup(data, session_dep, supabase_dep, Provider.email)
        except Exception as e:
            if hasattr(e, "detail"):
                print(f"Signup failed with detail: {e.detail}")
            print(f"Signup failed with exception: {e}")
            raise e

        # Verify
        self.assertIsInstance(response, SignupResponse)
        self.assertEqual(response.refresh_token, "mock_refresh_token")
        self.assertEqual(response.access_token, "mock_access_token")


if __name__ == "__main__":
    unittest.main()
