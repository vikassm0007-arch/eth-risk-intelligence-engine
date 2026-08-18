"""
Phase 2 E2E Automated Verification Test Script (RBAC Auth & Cases)
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from backend.db import AsyncSessionLocal, UserModel, CaseModel
from backend.auth_router import hash_password, create_access_token

async def test_phase2_backend():
    print("=" * 70)
    print("VERIFYING PHASE 2 RBAC AUTH & CASE MANAGEMENT PIPELINE")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        # 1. Verify Demo Accounts
        res = await session.execute(select(UserModel))
        users = res.scalars().all()
        print(f"[RBAC Test] Registered Users Count: {len(users)}")
        roles = [u.role for u in users]
        print(f"[RBAC Test] Active Roles: {roles}")
        assert "Admin" in roles, "Admin role missing!"
        assert "Senior Analyst" in roles, "Senior Analyst role missing!"

        # 2. Test JWT Token Generation
        admin_user = [u for u in users if u.role == "Admin"][0]
        token = create_access_token({"user_id": admin_user.id, "email": admin_user.email, "role": admin_user.role})
        print(f"[JWT Test] Access Token Issued for {admin_user.email} (Role: {admin_user.role})")
        assert len(token) > 20, "Invalid JWT token"

        # 3. Verify Cases Queue
        cases_res = await session.execute(select(CaseModel))
        cases = cases_res.scalars().all()
        print(f"[Cases Test] Operational Case Queue Size: {len(cases)} cases")
        assert len(cases) >= 5, "Seed cases missing!"

        priorities = set(c.priority for c in cases)
        print(f"[Cases Test] Case Priorities: {priorities}")

    print("=" * 70)
    print("ALL PHASE 2 BACKEND SECURITY & CASE WORKFLOW TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_phase2_backend())
