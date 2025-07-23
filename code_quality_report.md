# Code Quality Analysis Report
==================================================
Total files analyzed: 53
Total issues found: 91

## Issues by Severity
🔴 Critical: 0
🟠 High: 2
🟡 Medium: 7
🟢 Low: 82

## High Issues
- **sql_injection_risk** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Potential SQL injection risk - use parameterized queries

- **sql_injection_risk** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql_db.py
  Potential SQL injection risk - use parameterized queries

## Medium Issues
- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\check_db_schema.py
  Line 14: Function 'main' is 52 lines long (consider breaking it down)

- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql.py
  Line 137: Function 'main' is 84 lines long (consider breaking it down)

- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\test_db_connection.py
  Line 185: Function 'main' is 61 lines long (consider breaking it down)

- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\app\main.py
  Line 35: Function 'rate_limit_middleware' is 51 lines long (consider breaking it down)

- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Line 16: Function 'signup' is 55 lines long (consider breaking it down)

- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Line 127: Function 'get_me' is 60 lines long (consider breaking it down)

- **long_function** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\shares.py
  Line 17: Function 'share' is 73 lines long (consider breaking it down)

## Low Issues
- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [27, 48, 70, 97, 126, 163]: 'issues = []...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [44, 66, 93, 122, 159, 178]: 'return issues...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [50, 99, 165]: 'for node in ast.walk(tree):...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [56, 85, 103, 114, 142, 152, 170]: 'issues.append({...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [58, 87, 105, 116, 144, 154, 172]: ''file': file_path,...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [59, 106, 117, 173]: ''line': node.lineno,...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [107, 118, 155]: ''severity': 'high',...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\fix_code_issues.py
  Duplicate code found on lines [216, 224, 241]: 'report.append("")...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\init_db.py
  Duplicate code found on lines [36, 56, 84]: 'return True...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql.py
  Duplicate code found on lines [21, 27, 40, 70]: 'import pymysql...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql.py
  Duplicate code found on lines [31, 63, 99, 108]: 'return False...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql.py
  Duplicate code found on lines [33, 59, 95, 135]: 'return True...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql.py
  Duplicate code found on lines [61, 97, 219]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql_db.py
  Duplicate code found on lines [25, 50, 92, 134]: 'return True...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql_db.py
  Duplicate code found on lines [29, 60, 63, 71, 95, 99, 121, 138]: 'return False...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\setup_mysql_db.py
  Duplicate code found on lines [61, 97, 136]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_all_apis.py
  Duplicate code found on lines [97, 111, 161]: 'return result...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_all_apis.py
  Duplicate code found on lines [146, 189, 200, 209, 228, 250, 269, 278]: 'result = self.test_endpoint(...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_all_apis.py
  Duplicate code found on lines [174, 194, 204, 213]: 'headers=headers...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_all_apis.py
  Duplicate code found on lines [184, 221, 242]: 'results = []...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_all_apis.py
  Duplicate code found on lines [196, 206, 215, 225, 233, 256, 275, 284]: 'results.append(result)...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_all_apis.py
  Duplicate code found on lines [217, 235, 264, 286]: 'return results...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_db_connection.py
  Duplicate code found on lines [27, 43, 65, 87, 114, 149, 181]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_db_connection.py
  Duplicate code found on lines [29, 45, 67, 89, 116]: 'traceback.print_exc()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_db_connection.py
  Duplicate code found on lines [64, 86, 113, 144]: 'return True...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_db_connection.py
  Duplicate code found on lines [68, 90, 117, 148, 156, 165, 169, 179, 183]: 'return False...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\test_db_connection.py
  Duplicate code found on lines [199, 225, 242]: 'if 'mysql' in settings.database_url:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\main.py
  Duplicate code found on lines [42, 46, 86]: 'return await call_next(request)...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Duplicate code found on lines [22, 80, 133]: 'db: Database session...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Duplicate code found on lines [33, 68, 92, 100, 121, 145, 154, 161, 184]: 'raise HTTPException(...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Duplicate code found on lines [45, 64, 117, 180]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Duplicate code found on lines [47, 66, 119, 182]: 'import logging...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\auth.py
  Duplicate code found on lines [69, 122, 185]: 'status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\shares.py
  Duplicate code found on lines [41, 101, 118]: 'payload = verify_access_token(token)...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\shares.py
  Duplicate code found on lines [42, 102, 119]: 'if not payload:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\api\users.py
  Duplicate code found on lines [27, 44, 58]: 'current_rank=None,...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [27, 136, 144, 151, 158]: 'self.message = message...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [48, 74, 93, 101, 119, 165, 180, 196, 211]: 'error_response = ErrorResponse(...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [54, 81, 109, 126, 171, 186, 202, 217]: 'return JSONResponse(...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [56, 188, 219]: 'content=error_response.to_dict(),...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [83, 111, 128, 173, 204]: 'content=error_response.to_dict()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [138, 145, 152, 159]: 'super().__init__(self.message)...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\error_handlers.py
  Duplicate code found on lines [167, 182, 198, 213]: 'message=exc.message,...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\security.py
  Duplicate code found on lines [22, 30, 36]: 'return payload...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\validators.py
  Duplicate code found on lines [29, 78, 86, 123, 134, 170, 178, 189, 205]: '@staticmethod...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\validators.py
  Duplicate code found on lines [38, 95, 143]: 'List of validation error messages (empty if valid)...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\validators.py
  Duplicate code found on lines [40, 97, 145, 181, 192, 208]: 'errors = []...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\validators.py
  Duplicate code found on lines [44, 76, 101, 121, 149, 168, 187, 203, 216]: 'return errors...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\core\validators.py
  Duplicate code found on lines [275, 282, 289]: 'raise ValueError("; ".join(errors))...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\schemas\share.py
  Duplicate code found on lines [6, 11, 20]: 'platform: str...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\schemas\user.py
  Duplicate code found on lines [7, 11, 17]: 'email: EmailStr...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\services\email_service.py
  Duplicate code found on lines [24, 49, 54]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\services\leaderboard_service.py
  Duplicate code found on lines [15, 32, 49]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\services\user_service.py
  Duplicate code found on lines [36, 59, 78]: 'db.commit()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\services\user_service.py
  Duplicate code found on lines [37, 60, 79]: 'db.refresh(user)...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\services\user_service.py
  Duplicate code found on lines [38, 46, 61, 80]: 'return user...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\app\utils\cache.py
  Duplicate code found on lines [12, 21, 36]: 'except Exception as e:...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\conftest.py
  Duplicate code found on lines [28, 45, 63, 79, 95, 105]: '@pytest.fixture...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [7, 18, 27]: 'response = client.post("/admin/login", json={...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [11, 36, 50, 58, 73, 111]: 'assert response.status_code == status.HTTP_200_OK...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [12, 37, 51, 59]: 'data = response.json()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [22, 31, 45, 65, 99, 136]: 'assert response.status_code == status.HTTP_403_FOR...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [69, 78, 87, 95]: 'response = client.post("/admin/promote",...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [71, 80, 89, 109, 122]: 'headers=admin_headers...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [103, 116, 129]: 'response = client.post("/admin/send-bulk-email",...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_admin.py
  Duplicate code found on lines [105, 118, 131]: '"subject": "Test Email",...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_auth.py
  Duplicate code found on lines [7, 22, 32, 41]: 'response = client.post("/auth/signup", json={...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_auth.py
  Duplicate code found on lines [13, 55, 81]: 'data = response.json()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_auth.py
  Duplicate code found on lines [25, 35, 73]: '"password": "password123"...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_auth.py
  Duplicate code found on lines [43, 51, 63]: '"email": "test@example.com",...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_auth.py
  Duplicate code found on lines [50, 62, 71]: 'response = client.post("/auth/login", json={...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_auth.py
  Duplicate code found on lines [66, 75, 88, 93]: 'assert response.status_code == status.HTTP_401_UNA...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_leaderboard.py
  Duplicate code found on lines [7, 90, 97]: 'response = client.get("/leaderboard", headers=auth...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_leaderboard.py
  Duplicate code found on lines [8, 17, 30, 38, 50, 59, 91, 98]: 'assert response.status_code == status.HTTP_200_OK...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_leaderboard.py
  Duplicate code found on lines [9, 18, 31, 39, 51, 60, 92, 99]: 'data = response.json()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_shares.py
  Duplicate code found on lines [10, 66, 78, 91, 104]: 'data = response.json()...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_shares.py
  Duplicate code found on lines [56, 111, 116]: 'assert response.status_code == status.HTTP_401_UNA...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_shares.py
  Duplicate code found on lines [61, 73, 85]: 'client.post("/shares/twitter", headers=auth_header...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_shares.py
  Duplicate code found on lines [62, 74, 86]: 'client.post("/shares/facebook", headers=auth_heade...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_shares.py
  Duplicate code found on lines [65, 77, 90, 103]: 'assert response.status_code == status.HTTP_200_OK...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_users.py
  Duplicate code found on lines [8, 25, 37, 50, 57, 65, 75, 81, 88]: 'assert response.status_code == status.HTTP_200_OK...'

- **duplicate_code** in D:\lawvriksh\lawvriksh_betajoining\backend\tests\test_users.py
  Duplicate code found on lines [9, 26, 38, 58, 82, 89]: 'data = response.json()...'
