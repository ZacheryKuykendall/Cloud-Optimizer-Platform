"""Data models for Azure-GCP VPN connections.

This module provides data models for managing Site-to-Site VPN connections
between Azure Virtual Network Gateways and Google Cloud VPN Gateways.
"""

from datetime import datetime
from enum import Enum
from ipaddress import IPv4Network
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, IPvAnyNetwork


class VpnType(str, Enum):
    """VPN connection types."""
    ROUTE_BASED = "route-based"
    POLICY_BASED = "policy-based"


class TunnelProtocol(str, Enum):
    """VPN tunnel protocols."""
    IPSEC = "ipsec"
    IKEv2 = "ikev2"


class VpnStatus(str, Enum):
    """VPN connection status."""
    AVAILABLE = "available"
    PENDING = "pending"
    DELETING = "deleting"
    DELETED = "deleted"
    MODIFYING = "modifying"
    FAILED = "failed"


class TunnelStatus(str, Enum):
    """VPN tunnel status."""
    UP = "up"
    DOWN = "down"
    NEGOTIATING = "negotiating"


class IkeVersion(str, Enum):
    """IKE protocol versions."""
    V1 = "ikev1"
    V2 = "ikev2"


class DhGroup(str, Enum):
    """Diffie-Hellman groups."""
    GROUP2 = "2"
    GROUP14 = "14"
    GROUP24 = "24"
    GROUP_ECP256 = "ECP256"
    GROUP_ECP384 = "ECP384"


class IkeEncryption(str, Enum):
    """IKE encryption algorithms."""
    AES128 = "AES128"
    AES192 = "AES192"
    AES256 = "AES256"
    DES = "DES"
    DES3 = "3DES"


class IkeIntegrity(str, Enum):
    """IKE integrity algorithms."""
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA384 = "SHA384"
    MD5 = "MD5"


class IpsecEncryption(str, Enum):
    """IPsec encryption algorithms."""
    AES128 = "AES128"
    AES192 = "AES192"
    AES256 = "AES256"
    DES = "DES"
    DES3 = "3DES"
    GCMAES128 = "GCMAES128"
    GCMAES192 = "GCMAES192"
    GCMAES256 = "GCMAES256"


class IpsecIntegrity(str, Enum):
    """IPsec integrity algorithms."""
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA384 = "SHA384"
    MD5 = "MD5"
    GCMAES128 = "GCMAES128"
    GCMAES192 = "GCMAES192"
    GCMAES256 = "GCMAES256"


class PfsGroup(str, Enum):
    """Perfect Forward Secrecy groups."""
    NONE = "None"
    GROUP1 = "1"
    GROUP2 = "2"
    GROUP14 = "14"
    GROUP24 = "24"
    GROUP_ECP256 = "ECP256"
    GROUP_ECP384 = "ECP384"


class IkeConfig(BaseModel):
    """IKE configuration for VPN tunnel."""
    version: IkeVersion = Field(default=IkeVersion.V2)
    dh_group: DhGroup = Field(default=DhGroup.GROUP14)
    encryption: IkeEncryption = Field(default=IkeEncryption.AES256)
    integrity: IkeIntegrity = Field(default=IkeIntegrity.SHA256)
    lifetime_seconds: int = Field(default=28800)  # 8 hours


class IpsecConfig(BaseModel):
    """IPsec configuration for VPN tunnel."""
    encryption: IpsecEncryption = Field(default=IpsecEncryption.AES256)
    integrity: IpsecIntegrity = Field(default=IpsecIntegrity.SHA256)
    pfs_group: PfsGroup = Field(default=PfsGroup.GROUP14)
    lifetime_seconds: int = Field(default=3600)  # 1 hour


class TunnelConfig(BaseModel):
    """VPN tunnel configuration."""
    inside_cidr: IPv4Network
    preshared_key: str
    protocol: TunnelProtocol = Field(default=TunnelProtocol.IPSEC)
    ike_config: IkeConfig = Field(default_factory=IkeConfig)
    ipsec_config: IpsecConfig = Field(default_factory=IpsecConfig)


class TunnelMonitoring(BaseModel):
    """VPN tunnel monitoring data."""
    status: TunnelStatus
    last_status_change: datetime
    last_error_message: Optional[str] = None
    bytes_in: int = 0
    bytes_out: int = 0
    packets_in: int = 0
    packets_out: int = 0
    replay_window_size: int = Field(default=1024)
    clear_df_bits: bool = Field(default=True)
    fragment_before_encrypt: bool = Field(default=True)
    tcp_mss_adjustment: int = Field(default=1379)
    startup_actions: List[str] = Field(default_factory=list)
    dpd_timeout_seconds: int = Field(default=30)


class RouteEntry(BaseModel):
    """Route entry for VPN connection."""
    destination: IPvAnyNetwork
    next_hop: Optional[str] = None
    origin: str  # e.g., "static", "bgp"
    state: str  # e.g., "active", "inactive"


class BgpConfig(BaseModel):
    """BGP configuration for VPN connection."""
    enabled: bool = Field(default=False)
    asn: Optional[int] = None
    bgp_peer_ip: Optional[str] = None
    bgp_peer_asn: Optional[int] = None


class AzureVNetGateway(BaseModel):
    """Azure Virtual Network Gateway configuration."""
    gateway_id: str
    vnet_name: str
    resource_group: str
    location: str
    sku: str  # e.g., "VpnGw1", "VpnGw2"
    generation: str  # e.g., "Generation1", "Generation2"
    active_active: bool = Field(default=False)
    public_ip_address: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class GcpVpnGateway(BaseModel):
    """Google Cloud VPN Gateway configuration."""
    gateway_id: str
    project_id: str
    network: str
    region: str
    vpn_interfaces: List[str]  # List of interface IPs
    stack_type: str = Field(default="IPV4_ONLY")  # IPV4_ONLY, IPV4_IPV6
    labels: Dict[str, str] = Field(default_factory=dict)


class VpnConnection(BaseModel):
    """VPN connection between Azure and GCP."""
    id: str
    name: str
    description: Optional[str] = None
    type: VpnType = Field(default=VpnType.ROUTE_BASED)
    azure_gateway: AzureVNetGateway
    gcp_gateway: GcpVpnGateway
    tunnels: List[TunnelConfig]
    monitoring: Dict[str, TunnelMonitoring] = Field(default_factory=dict)
    routes: List[RouteEntry] = Field(default_factory=list)
    bgp_config: Optional[BgpConfig] = None
    status: VpnStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)  # GCP uses labels instead of tags


class VpnConnectionSummary(BaseModel):
    """Summary of VPN connection status and metrics."""
    id: str
    name: str
    status: VpnStatus
    tunnel_count: int
    active_tunnels: int
    routes_advertised: int
    last_status_change: datetime
    data_transfer_in_bytes: int
    data_transfer_out_bytes: int
    tunnel_statuses: Dict[str, TunnelStatus]
    bgp_status: Optional[str] = None
    alerts: List[str] = Field(default_factory=list)


class VpnConnectionQuery(BaseModel):
    """Query parameters for VPN connections."""
    ids: Optional[List[str]] = None
    names: Optional[List[str]] = None
    statuses: Optional[List[VpnStatus]] = None
    project_ids: Optional[List[str]] = None
    vnet_names: Optional[List[str]] = None
    resource_groups: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
