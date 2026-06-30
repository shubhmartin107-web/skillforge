# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x     | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in SkillForge, please report it privately.

**Do not** report security vulnerabilities through public GitHub issues.

Instead, please email: **security@skillforge.ai**

You should receive a response within 48 hours. If for some reason you do not, please follow up.

## Scope

Security issues include but are not limited to:

- Sandbox escape (skill execution isolation)
- Unauthorized file system access
- Unauthorized network access
- Remote code execution
- Sensitive data exposure
- Authentication/authorization bypass

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm receipt within 48 hours
2. Investigate and develop a fix
3. Release a security patch as soon as possible
4. Publicly disclose the issue after the fix is released

## Security Measures

SkillForge implements:

- **Sandboxed execution** via subprocess isolation with resource limits
- **Capability-based permissions**: skills declare exactly what they need
- **Audit logging**: all skill operations are logged with sensitive data redaction
- **Input validation**: strict schema validation for all skill inputs
- **No arbitrary code execution**: direct import with function resolution
