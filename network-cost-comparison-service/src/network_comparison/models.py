"""Data models for network cost comparison.

This module provides data models for comparing network costs
across different cloud providers (AWS, Azure, GCP).
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, validator


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class NetworkServiceType(str, Enum):
    """Types of network services."""
    VPC = "vpc"  # AWS VPC, Azure VNet, GCP VPC
    LOAD_BALANCER = "load_balancer"  # ALB/NLB, Azure LB, GCP LB
    CDN = "cdn"  # CloudFront, Azure CDN, Cloud CDN
    DNS = "dns"  # Route53, Azure DNS, Cloud DNS
    VPN = "vpn"  # VPN Gateway, VPN Gateway, Cloud VPN
    TRANSIT = "transit"  # Transit Gateway, Virtual WAN, Cloud Router
    WAF = "waf"  # WAF, Azure WAF, Cloud Armor
    DDOS = "ddos"  # Shield, DDoS Protection, Cloud Armor
    NAT = "nat"  # NAT Gateway, NAT Gateway, Cloud NAT


class LoadBalancerType(str, Enum):
    """Types of load balancers."""
    APPLICATION = "application"  # Layer 7
    NETWORK = "network"  # Layer 4
    GATEWAY = "gateway"  # Layer 3/4
    INTERNAL = "internal"  # Internal load balancing


class CdnType(str, Enum):
    """Types of CDN configurations."""
    STANDARD = "standard"  # Basic CDN
    PREMIUM = "premium"  # Enhanced features
    CUSTOM = "custom"  # Custom configurations
    SECURITY = "security"  # Security-focused


class DnsType(str, Enum):
    """Types of DNS services."""
    PUBLIC = "public"  # Internet-facing DNS
    PRIVATE = "private"  # Internal DNS
    GLOBAL = "global"  # Global DNS services
    GEO = "geo"  # Geo-based routing


class VpnType(str, Enum):
    """Types of VPN connections."""
    SITE_TO_SITE = "site_to_site"
    POINT_TO_SITE = "point_to_site"
    ROUTE_BASED = "route_based"
    POLICY_BASED = "policy_based"


class TransitType(str, Enum):
    """Types of transit services."""
    HUB_SPOKE = "hub_spoke"
    MESH = "mesh"
    GLOBAL = "global"
    REGIONAL = "regional"


class WafType(str, Enum):
    """Types of WAF configurations."""
    BASIC = "basic"
    ADVANCED = "advanced"
    CUSTOM = "custom"
    MANAGED = "managed"


class DdosType(str, Enum):
    """Types of DDoS protection."""
    STANDARD = "standard"
    ADVANCED = "advanced"
    PREMIUM = "premium"


class NatType(str, Enum):
    """Types of NAT services."""
    GATEWAY = "gateway"
    INSTANCE = "instance"
    MANAGED = "managed"


class NetworkRequirements(BaseModel):
    """Network requirements for comparison."""
    service_type: NetworkServiceType
    region: str
    bandwidth_gbps: float = Field(gt=0)
    data_transfer_gb: Optional[float] = None
    requests_per_second: Optional[int] = None
    zones: Optional[int] = Field(None, ge=1)
    high_availability: bool = False
    cross_region: bool = False
    required_features: Set[str] = Field(default_factory=set)
    required_certifications: Set[str] = Field(default_factory=set)

    # Service-specific fields
    load_balancer_type: Optional[LoadBalancerType] = None
    cdn_type: Optional[CdnType] = None
    dns_type: Optional[DnsType] = None
    vpn_type: Optional[VpnType] = None
    transit_type: Optional[TransitType] = None
    waf_type: Optional[WafType] = None
    ddos_type: Optional[DdosType] = None
    nat_type: Optional[NatType] = None

    @validator("bandwidth_gbps")
    def validate_bandwidth(cls, v):
        """Validate bandwidth requirements."""
        if v <= 0:
            raise ValueError("Bandwidth must be greater than 0")
        return v

    @validator("data_transfer_gb")
    def validate_data_transfer(cls, v):
        """Validate data transfer requirements."""
        if v is not None and v < 0:
            raise ValueError("Data transfer must be non-negative")
        return v

    @validator("requests_per_second")
    def validate_requests(cls, v):
        """Validate requests per second."""
        if v is not None and v < 0:
            raise ValueError("Requests per second must be non-negative")
        return v


class NetworkOption(BaseModel):
    """Network service option from a provider."""
    provider: CloudProvider
    service_type: NetworkServiceType
    region: str
    min_bandwidth_gbps: float
    max_bandwidth_gbps: Optional[float] = None
    min_requests_per_second: Optional[int] = None
    max_requests_per_second: Optional[int] = None
    features: Set[str] = Field(default_factory=set)
    certifications: Set[str] = Field(default_factory=set)
    high_availability: bool = False
    cross_region: bool = False

    # Service-specific fields
    load_balancer_type: Optional[LoadBalancerType] = None
    cdn_type: Optional[CdnType] = None
    dns_type: Optional[DnsType] = None
    vpn_type: Optional[VpnType] = None
    transit_type: Optional[TransitType] = None
    waf_type: Optional[WafType] = None
    ddos_type: Optional[DdosType] = None
    nat_type: Optional[NatType] = None


class CostComponent(BaseModel):
    """Individual cost component."""
    name: str  # e.g., "Data Processing", "Data Transfer", "Fixed"
    monthly_cost: Decimal
    details: Optional[Dict[str, str]] = None


class NetworkCostEstimate(BaseModel):
    """Cost estimate for a network service option."""
    provider: CloudProvider
    service_type: NetworkServiceType
    region: str
    bandwidth_gbps: float
    data_transfer_gb: Optional[float] = None
    requests_per_second: Optional[int] = None
    monthly_cost: Decimal
    cost_components: List[CostComponent] = Field(default_factory=list)
    features: Set[str] = Field(default_factory=set)
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    # Service-specific fields
    load_balancer_type: Optional[LoadBalancerType] = None
    cdn_type: Optional[CdnType] = None
    dns_type: Optional[DnsType] = None
    vpn_type: Optional[VpnType] = None
    transit_type: Optional[TransitType] = None
    waf_type: Optional[WafType] = None
    ddos_type: Optional[DdosType] = None
    nat_type: Optional[NatType] = None


class NetworkComparison(BaseModel):
    """Comparison of network options across providers."""
    requirements: NetworkRequirements
    estimates: List[NetworkCostEstimate]
    recommended_option: Optional[NetworkCostEstimate] = None
    comparison_date: datetime = Field(default_factory=datetime.utcnow)
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notes: Optional[str] = None


class ComparisonFilter(BaseModel):
    """Filter criteria for network comparisons."""
    providers: Optional[Set[CloudProvider]] = None
    service_types: Optional[Set[NetworkServiceType]] = None
    regions: Optional[Set[str]] = None
    min_bandwidth_gbps: Optional[float] = None
    max_bandwidth_gbps: Optional[float] = None
    min_data_transfer_gb: Optional[float] = None
    max_data_transfer_gb: Optional[float] = None
    min_requests_per_second: Optional[int] = None
    max_requests_per_second: Optional[int] = None
    required_features: Optional[Set[str]] = None
    required_certifications: Optional[Set[str]] = None
    max_monthly_cost: Optional[Decimal] = None
    high_availability: Optional[bool] = None
    cross_region: Optional[bool] = None

    # Service-specific filters
    load_balancer_types: Optional[Set[LoadBalancerType]] = None
    cdn_types: Optional[Set[CdnType]] = None
    dns_types: Optional[Set[DnsType]] = None
    vpn_types: Optional[Set[VpnType]] = None
    transit_types: Optional[Set[TransitType]] = None
    waf_types: Optional[Set[WafType]] = None
    ddos_types: Optional[Set[DdosType]] = None
    nat_types: Optional[Set[NatType]] = None


class ComparisonResult(BaseModel):
    """Result of a network cost comparison."""
    comparison: NetworkComparison
    filters_applied: ComparisonFilter
    total_options_considered: int
    filtered_options_count: int
    processing_time_ms: float
    cache_hit: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = None


class PricingTier(BaseModel):
    """Pricing tier for network costs."""
    min_usage: float  # Minimum usage (GB, requests, etc.)
    max_usage: Optional[float] = None  # Maximum usage
    price_per_unit: Decimal  # Price per unit
    unit: str  # e.g., "GB", "request", "hour"
    conditions: Optional[Dict[str, str]] = None


class OperationalMetrics(BaseModel):
    """Operational metrics for network services."""
    availability_sla: str  # e.g., "99.99%"
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    jitter_ms: Optional[float] = None
    throughput_gbps: Optional[float] = None
    concurrent_connections: Optional[int] = None
    ssl_tls_support: bool = True
    ddos_protection: bool = True
    monitoring_included: bool = True
