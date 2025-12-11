# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.2   | :white_check_mark: |
| 1.0.1   | :white_check_mark: |
| 1.0.0   | :x:                |

---

## Reporting a Vulnerability

**DO NOT** report security vulnerabilities through public GitHub issues.

Instead, please report security vulnerabilities to:
- **Email**: security@medaiflow.com (or your organization's security email)
- **GitHub Security Advisories**: [Create a private security advisory](https://github.com/Transvolve/MedAI_Flow_DevSecOps/security/advisories/new)

You should receive a response within 48 hours. If the issue is confirmed, we will:
1. Assign a CVE identifier (if applicable)
2. Develop and test a fix
3. Release a security patch
4. Publish a security advisory

---

## Security Requirements

### For Production Deployment

Before deploying to production, ensure all of the following are completed:

#### Critical (MUST):
- [ ] Generate persistent JWT secret key (not default)
- [ ] Rotate Azure credentials and store in GitHub Secrets
- [ ] Enable Redis TLS/SSL (`redis_ssl=true`)
- [ ] Set Redis password from Azure Key Vault
- [ ] Enable HTTPS enforcement (`enforce_https=true`)
- [ ] Remove hardcoded users from config.py
- [ ] Configure Azure Key Vault for secrets management
- [ ] Disable ACR admin account (use Managed Identity)
- [ ] Apply Kubernetes security contexts (non-root, read-only FS)
- [ ] Configure network policies
- [ ] Set up centralized logging (Azure Application Insights)

#### High Priority (SHOULD):
- [ ] Enable container image scanning (Trivy/Snyk)
- [ ] Configure Azure Monitor alerts
- [ ] Implement secret rotation policy (90 days)
- [ ] Set up backup/disaster recovery
- [ ] Configure WAF (Azure Front Door)
- [ ] Enable Azure DDoS Protection
- [ ] Implement audit logging for all auth events

#### Recommended (NICE TO HAVE):
- [ ] Container image signing with Cosign
- [ ] Implement service mesh for mTLS
- [ ] Set up SIEM integration
- [ ] Configure honeypots/deception tech
- [ ] Third-party penetration testing

---

## Security Architecture

### Authentication & Authorization
- **Method**: JWT with OAuth2 password flow
- **Token Expiry**: 30 minutes (configurable)
- **Password Hashing**: Argon2id with default parameters
- **RBAC**: Role-based access control (admin, user)
- **Token Revocation**: Redis-backed blacklist

### Network Security
- **TLS**: Enforced for all external communications (TLS 1.2+)
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Rate Limiting**: 60 requests/minute per IP (Redis-backed)
- **Network Policies**: Pod-to-pod communication restricted

### Container Security
- **Base Image**: python:3.11-slim (minimal attack surface)
- **User**: Non-root (UID 1000)
- **Filesystem**: Read-only root filesystem
- **Capabilities**: All dropped
- **Seccomp**: RuntimeDefault profile

### Secrets Management
- **Development**: .env files (gitignored)
- **Production**: Azure Key Vault with CSI driver
- **CI/CD**: GitHub Secrets
- **Kubernetes**: Sealed Secrets (recommended)

---

## Known Security Considerations

### Current Limitations

1. **User Management**: Users are currently hardcoded in `config.py`
   - **Mitigation**: Migrate to database (PostgreSQL + Azure AD)
   - **Timeline**: Q1 2026

2. **Audit Logging**: Basic logging to stdout
   - **Mitigation**: Integrate Azure Application Insights
   - **Timeline**: Q4 2025

3. **Secrets Rotation**: Manual process
   - **Mitigation**: Implement automated rotation
   - **Timeline**: Q1 2026

4. **Container Image Signing**: Not implemented
   - **Mitigation**: Integrate Cosign/Notary
   - **Timeline**: Q2 2026

---

## Security Testing

### Automated Security Scans

Our CI/CD pipeline includes:
- **Bandit**: Python security linter (severity: HIGH/CRITICAL)
- **Safety**: Dependency vulnerability scanner
- **Flake8**: Code quality and security linting

### Manual Security Testing

Recommended frequency:
- **Code Review**: Every pull request
- **Penetration Testing**: Annually (external vendor)
- **Vulnerability Assessment**: Quarterly
- **Security Audit**: Annually (ISO 27001)

---

## Incident Response

### Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **Critical** | Immediate threat to production | 1 hour | Credential leak, active exploit |
| **High** | Significant security risk | 4 hours | Unpatched CVE, privilege escalation |
| **Medium** | Moderate security concern | 24 hours | Information disclosure, weak config |
| **Low** | Minor security issue | 1 week | Outdated dependency, logging gap |

### Response Procedure

1. **Detect**: Monitoring alerts, user reports, security scans
2. **Assess**: Determine severity and impact
3. **Contain**: Isolate affected systems, revoke compromised credentials
4. **Eradicate**: Apply patches, update configurations
5. **Recover**: Restore services, verify integrity
6. **Learn**: Post-incident review, update documentation

### Contacts

- **Security Team**: security@medaiflow.com
- **On-Call Engineer**: (Configured in PagerDuty/Opsgenie)
- **CISO**: ciso@medaiflow.com

---

## Compliance

This project adheres to:
- **FDA 21 CFR Part 820**: Design controls, traceability
- **FDA 21 CFR Part 11**: Electronic records and signatures
- **ISO/IEC 27001:2022**: Information security management
- **ISO 13485**: Medical device quality management
- **ISO 62304**: Medical device software lifecycle
- **ISO 14971**: Risk management for medical devices
- **OWASP Top 10**: Web application security risks
- **NIST SP 800-53**: Security and privacy controls
- **NIST SP 800-190**: Container security

---

## Security Champions

| Role | Responsibility |
|------|----------------|
| **CISO** | Overall security strategy and compliance |
| **Security Engineer** | Security architecture, penetration testing |
| **DevSecOps Lead** | CI/CD security, infrastructure hardening |
| **Quality Assurance** | Security testing, vulnerability validation |

---

## Security Resources

### Internal Documentation
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Risk Management File](compliance/RISK_MANAGEMENT_FILE.md)
- [ISO 27001 Controls](compliance/iso_27001_security_controls.md)
- [FDA Traceability Matrix](compliance/fda_21cfr820_traceability_matrix.md)

### External References
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [FDA Cybersecurity Guidance](https://www.fda.gov/medical-devices/digital-health-center-excellence/cybersecurity)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

---

## Security Updates

Subscribe to security advisories:
- **GitHub**: Watch this repository for security advisories
- **Email**: Subscribe to security-announce@medaiflow.com
- **RSS**: https://github.com/Transvolve/MedAI_Flow_DevSecOps/security/advisories.atom

---

## Acknowledgments

We appreciate responsible disclosure from security researchers. Contributors who report valid security issues will be:
- Acknowledged in our security advisories (unless anonymity is requested)
- Eligible for swag/recognition (if applicable)

---

**Last Updated**: 2025-11-08  
**Next Review**: 2026-02-08
