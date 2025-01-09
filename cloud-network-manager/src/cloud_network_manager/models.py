"""Data models for cloud network management.

This module provides data models for managing network resources and VPN
connections across different cloud providers.
"""

from datetime import datetime
from enum import Enum
from ipaddress import IPv4Network
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, IPvAnyNetwork


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class NetworkType(str, Enum):
    """Types of network resources."""
    VPC = "vpc"  # AWS VPC
    VNET = "vnet"  # Azure VNet
    VPC_NETWORK = "vpc_network"  # GCP VPC Network


class VPNType(str, Enum):
    """Types of VPN connections."""
    SITE_TO_SITE = "site_to_site"
    ROUTE_BASED = "route_based"
    POLICY_BASED = "policy_based"


class VPNStatus(str, Enum):
    """Status of VPN connections."""
    PENDING = "pending"
    AVAILABLE = "available"
    DELETING = "deleting"
    DELETED = "deleted"
    FAILED = "failed"


class NetworkConfiguration(BaseModel):
    """Configuration for a cloud network (VPC/VNet)."""
    provider: CloudProvider
    network_type: NetworkType
    name: str
    region: str
    cidr_block: IPv4Network
    subnets: List[IPv4Network] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


class VPNGatewayConfiguration(BaseModel):
    """Configuration for a VPN gateway."""
    name: str
    type: VPNType
    bandwidth: str  # e.g., "1Gbps"
    availability_zones: List[str] = Field(default_factory=list)
    bgp_asn: Optional[int] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class IPSecConfiguration(BaseModel):
    """IPSec configuration for VPN tunnels."""
    ike_version: str = "2"
    phase1_dh_group_numbers: List[int] = [2, 14, 15, 16, 17, 18, 19, 20, 21]
    phase1_encryption_algorithms: List[str] = ["AES256", "AES192", "AES128"]
    phase1_integrity_algorithms: List[str] = ["SHA2-256", "SHA2-384", "SHA2-512"]
    phase2_dh_group_numbers: List[int] = [2, 14, 15, 16, 17, 18, 19, 20, 21]
    phase2_encryption_algorithms: List[str] = ["AES256", "AES192", "AES128"]
    phase2_integrity_algorithms: List[str] = ["SHA2-256", "SHA2-384", "SHA2-512"]
    pre_shared_key: Optional[str] = None


class VPNTunnelConfiguration(BaseModel):
    """Configuration for a VPN tunnel."""
    name: str
    inside_cidr: Optional[IPv4Network] = None
    pre_shared_key: Optional[str] = None
    ipsec_config: Optional[IPSecConfiguration] = None
    bgp_config: Optional[Dict[str, str]] = None


class VPNConnection(BaseModel):
    """VPN connection between two networks."""
    id: str
    name: str
    source_network: NetworkConfiguration
    target_network: NetworkConfiguration
    source_gateway: VPNGatewayConfiguration
    target_gateway: VPNGatewayConfiguration
    tunnels: List[VPNTunnelConfiguration]
    status: VPNStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict)


class RouteTableEntry(BaseModel):
    """Entry in a route table."""
    destination_cidr: IPv4Network
    target: str  # VPN Gateway ID, Internet Gateway ID, etc.
    description: Optional[str] = None


class RouteTable(BaseModel):
    """Route table for a network."""
    id: str
    network_id: str
    routes: List[RouteTableEntry] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


class NetworkACLRule(BaseModel):
    """Rule for a Network ACL."""
    rule_number: int
    protocol: str
    action: str  # "allow" or "deny"
    cidr_block: IPv4Network
    from_port: Optional[int] = None
    to_port: Optional[int] = None
    icmp_type: Optional[int] = None
    icmp_code: Optional[int] = None


class NetworkACL(BaseModel):
    """Network Access Control List."""
    id: str
    network_id: str
    inbound_rules: List[NetworkACLRule] = Field(default_factory=list)
    outbound_rules: List[NetworkACLRule] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


class SecurityGroupRule(BaseModel):
    """Rule for a Security Group."""
    description: Optional[str] = None
    protocol: str
    from_port: Optional[int] = None
    to_port: Optional[int] = None
    cidr_blocks: List[IPv4Network] = Field(default_factory=list)
    source_security_groups: List[str] = Field(default_factory=list)


class SecurityGroup(BaseModel):
    """Security Group for network resources."""
    id: str
    name: str
    network_id: str
    description: str
    inbound_rules: List[SecurityGroupRule] = Field(default_factory=list)
    outbound_rules: List[SecurityGroupRule] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


class NetworkMetrics(BaseModel):
    """Metrics for network monitoring."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bytes_in: int = 0
    bytes_out: int = 0
    packets_in: int = 0
    packets_out: int = 0
    active_connections: int = 0


class VPNMetrics(BaseModel):
    """Metrics for VPN monitoring."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tunnel_status: str
    bytes_in: int = 0
    bytes_out: int = 0
    packets_in: int = 0
    packets_out: int = 0
    tunnel_state_changes: int = 0
    replay_packets: int = 0
    authentication_failures: int = 0


class NetworkEvent(BaseModel):
    """Event related to network resources."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resource_id: str
    resource_type: str
    event_type: str
    description: str
    details: Dict[str, str] = Field(default_factory=dict)


class NetworkState(BaseModel):
    """Current state of the network infrastructure."""
    networks: Dict[str, NetworkConfiguration] = Field(default_factory=dict)
    vpn_connections: Dict[str, VPNConnection] = Field(default_factory=dict)
    route_tables: Dict[str, RouteTable] = Field(default_factory=dict)
    network_acls: Dict[str, NetworkACL] = Field(default_factory=dict)
    security_groups: Dict[str, SecurityGroup] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class NetworkDiff(BaseModel):
    """Difference between two network states."""
    networks_added: List[NetworkConfiguration] = Field(default_factory=list)
    networks_removed: List[NetworkConfiguration] = Field(default_factory=list)
    networks_modified: List[NetworkConfiguration] = Field(default_factory=list)
    vpn_connections_added: List[VPNConnection] = Field(default_factory=list)
    vpn_connections_removed: List[VPNConnection] = Field(default_factory=list)
    vpn_connections_modified: List[VPNConnection] = Field(default_factory=list)
    route_tables_modified: List[RouteTable] = Field(default_factory=list)
    network_acls_modified: List[NetworkACL] = Field(default_factory=list)
    security_groups_modified: List[SecurityGroup] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NetworkValidationError(BaseModel):
    """Error found during network validation."""
    resource_id: str
    resource_type: str
    error_type: str
    description: str
    severity: str  # "high", "medium", "low"
    recommendation: Optional[str] = None


class NetworkValidationResult(BaseModel):
    """Result of network validation checks."""
    valid: bool
    errors: List[NetworkValidationError] = Field(default_factory=list)
    warnings: List[NetworkValidationError] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
