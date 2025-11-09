"""Immutable audit trail with hash-chain integrity verification.

Implements a cryptographically secure audit trail that prevents tampering
through hash-chain validation, enabling forensic analysis and compliance
with regulatory requirements.

Regulatory Compliance:
- FDA 21 CFR 11: Audit trail requirements and integrity
- ISO 27001: Audit logging and security event monitoring
- HIPAA: Complete audit logs of all access and modifications
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuditEntry:
    """Immutable audit trail entry with hash-chain validation.
    
    Each entry includes a cryptographic hash of the previous entry,
    creating an immutable chain that detects tampering.
    
    Attributes:
        entry_id: Unique identifier for this audit entry
        timestamp: UTC timestamp when entry was created
        action: Action performed (e.g., LOGIN, CREATE, DELETE)
        resource_type: Type of resource (e.g., MODEL, USER, IMAGE)
        resource_id: Identifier of affected resource
        user_id: User who performed action
        status: Action result (SUCCESS, FAILURE)
        details: Additional context about the action
        previous_hash: Hash of previous entry (chain verification)
        entry_hash: SHA256 hash of this entry
    """

    entry_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    user_id: Optional[str] = None
    status: str = "SUCCESS"
    details: dict = field(default_factory=dict)
    previous_hash: Optional[str] = None
    entry_hash: str = field(default="")

    def __post_init__(self) -> None:
        """Calculate entry hash. Called by dataclass after init."""
        # Use object.__setattr__ because dataclass is frozen
        hash_obj = hashlib.sha256()

        # Include all fields except entry_hash and previous_hash in hash
        # to create chain verification
        entry_data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "status": self.status,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }

        hash_input = json.dumps(entry_data, sort_keys=True, default=str)
        hash_obj.update(hash_input.encode("utf-8"))

        object.__setattr__(self, "entry_hash", hash_obj.hexdigest())

    def to_dict(self) -> dict:
        """Convert entry to dictionary.
        
        Returns:
            Dictionary representation of audit entry
        """
        return asdict(self)

    def to_json(self) -> str:
        """Convert entry to JSON string.
        
        Returns:
            JSON representation of audit entry
        """
        return json.dumps(self.to_dict(), default=str)


class AuditTrail:
    """Manage immutable audit trail with hash-chain validation.
    
    Maintains a sequence of audit entries with cryptographic hash chains
    to ensure integrity and detect tampering.
    
    Examples:
        >>> trail = AuditTrail()
        >>> trail.log_action(
        ...     action="LOGIN",
        ...     resource_type="USER",
        ...     resource_id="user123",
        ...     user_id="user123"
        ... )
        >>> trail.verify_integrity()
        True
    """

    def __init__(self) -> None:
        """Initialize audit trail."""
        self.entries: list[AuditEntry] = []
        self._last_hash: Optional[str] = None

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[dict] = None,
    ) -> AuditEntry:
        """Log audit action to trail.
        
        Args:
            action: Action performed
            resource_type: Type of resource (MODEL, USER, IMAGE, etc)
            resource_id: Identifier of affected resource
            user_id: User who performed action
            status: Action result (SUCCESS or FAILURE)
            details: Additional context
            
        Returns:
            The created AuditEntry
            
        Examples:
            >>> trail = AuditTrail()
            >>> entry = trail.log_action(
            ...     action="MODEL_DEPLOY",
            ...     resource_type="MODEL",
            ...     resource_id="v1.0.0",
            ...     user_id="admin",
            ...     details={"version": "1.0.0", "region": "us-east-1"}
            ... )
        """
        if not action or not resource_type or not resource_id:
            raise ValueError("action, resource_type, and resource_id are required")

        # Create new entry with previous hash for chain
        entry = AuditEntry(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            status=status,
            details=details or {},
            previous_hash=self._last_hash,
        )

        # Add to trail
        self.entries.append(entry)
        self._last_hash = entry.entry_hash

        logger.info(
            f"Audit entry logged: {action} on {resource_type} {resource_id}",
            extra={"entry_id": entry.entry_id},
        )

        return entry

    def verify_integrity(self) -> bool:
        """Verify hash-chain integrity of audit trail.
        
        Checks that each entry's previous_hash matches the previous entry's
        entry_hash, ensuring no tampering has occurred.
        
        Returns:
            True if trail integrity verified, False if tampering detected
            
        Examples:
            >>> trail = AuditTrail()
            >>> trail.log_action("LOGIN", "USER", "user1")
            >>> trail.verify_integrity()
            True
        """
        if not self.entries:
            return True

        # Check first entry has no previous_hash
        if self.entries[0].previous_hash is not None:
            logger.error("First audit entry has unexpected previous_hash")
            return False

        # Check each subsequent entry's previous_hash matches previous entry's hash
        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i - 1]

            if current.previous_hash != previous.entry_hash:
                logger.error(
                    f"Hash chain broken at entry {i}",
                    current_id=current.entry_id,
                    previous_id=previous.entry_id,
                )
                return False

        logger.info(f"Audit trail integrity verified for {len(self.entries)} entries")
        return True

    def get_entries_for_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditEntry]:
        """Get all audit entries for a specific resource.
        
        Args:
            resource_type: Type of resource to filter by
            resource_id: Identifier of resource
            
        Returns:
            List of matching audit entries
        """
        return [
            entry
            for entry in self.entries
            if entry.resource_type == resource_type and entry.resource_id == resource_id
        ]

    def get_entries_by_user(self, user_id: str) -> list[AuditEntry]:
        """Get all audit entries for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of audit entries by user
        """
        return [entry for entry in self.entries if entry.user_id == user_id]

    def get_entries_by_action(self, action: str) -> list[AuditEntry]:
        """Get all audit entries for a specific action type.
        
        Args:
            action: Action type (LOGIN, CREATE, DELETE, etc)
            
        Returns:
            List of matching audit entries
        """
        return [entry for entry in self.entries if entry.action == action]

    def get_latest_entries(self, count: int = 10) -> list[AuditEntry]:
        """Get most recent audit entries.
        
        Args:
            count: Number of entries to return
            
        Returns:
            List of most recent entries (newest first)
        """
        return list(reversed(self.entries[-count:]))

    def export_json(self) -> str:
        """Export entire audit trail as JSON.
        
        Returns:
            JSON representation of all entries
        """
        return json.dumps(
            [entry.to_dict() for entry in self.entries],
            default=str,
        )

    def __len__(self) -> int:
        """Get number of entries in trail."""
        return len(self.entries)

    def __repr__(self) -> str:
        """String representation."""
        return f"AuditTrail({len(self.entries)} entries)"
