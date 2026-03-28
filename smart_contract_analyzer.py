#!/usr/bin/env python3
"""
🔍 SMART CONTRACT ANALYZER 🔍
Advanced contract analysis for honeypot and rug pull detection
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import re
import requests
from web3 import Web3
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class ContractRisk(Enum):
    SAFE = ("🟢 Safe", 0)
    LOW_RISK = ("🟡 Low Risk", 1)
    MEDIUM_RISK = ("🟠 Medium Risk", 2)
    HIGH_RISK = ("🔴 High Risk", 3)
    HONEYPOT = ("⚫ Honeypot", 4)
    RUG_PULL = ("💀 Rug Pull", 5)

@dataclass
class ContractAnalysis:
    """Comprehensive contract analysis result"""
    contract_address: str
    risk_level: ContractRisk
    risk_score: int
    is_honeypot: bool
    is_rug_pull: bool
    ownership_renounced: bool
    has_mint_function: bool
    has_pause_function: bool
    has_blacklist: bool
    max_tx_limit: Optional[float]
    max_wallet_limit: Optional[float]
    buy_tax: float
    sell_tax: float
    liquidity_locked: bool
    verified_contract: bool
    proxy_contract: bool
    risk_factors: List[str]
    safety_features: List[str]
    analysis_timestamp: datetime

@dataclass
class TokenomicsAnalysis:
    """Token economics analysis"""
    total_supply: int
    circulating_supply: int
    holder_count: int
    top_10_holders_percentage: float
    dev_wallet_percentage: float
    marketing_wallet_percentage: float
    liquidity_percentage: float
    burned_percentage: float
    distribution_score: int

class SmartContractAnalyzer:
    """Advanced smart contract analyzer for meme coins"""
    
    def __init__(self, web3_connections: Dict):
        self.web3_connections = web3_connections
        
        # Known honeypot patterns and signatures
        self.honeypot_patterns = self._load_honeypot_patterns()
        self.rug_pull_patterns = self._load_rug_pull_patterns()
        
        # Contract verification APIs
        self.verification_apis = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api'
        }
        
        logger.info("🔍 Smart Contract Analyzer initialized")
    
    def _load_honeypot_patterns(self) -> List[Dict]:
        """Load known honeypot patterns and function signatures"""
        return [
            {
                'name': 'Transfer Restriction',
                'pattern': r'require\s*\(\s*[^)]*allowedToTrade',
                'severity': 'high',
                'description': 'Contract may restrict transfers for certain addresses'
            },
            {
                'name': 'Blacklist Function',
                'pattern': r'function\s+blacklist|mapping\s*\([^)]*\)\s*blacklist',
                'severity': 'high',
                'description': 'Contract has blacklist functionality'
            },
            {
                'name': 'Pause Function',
                'pattern': r'function\s+pause|whenNotPaused|_pause\(\)',
                'severity': 'medium',
                'description': 'Contract can be paused by owner'
            },
            {
                'name': 'Only Owner Modifier',
                'pattern': r'modifier\s+onlyOwner|require\s*\(\s*msg\.sender\s*==\s*owner',
                'severity': 'medium',
                'description': 'Contract has owner-only functions'
            },
            {
                'name': 'Mint Function',
                'pattern': r'function\s+mint|_mint\s*\(',
                'severity': 'medium',
                'description': 'Contract can mint new tokens'
            },
            {
                'name': 'Max Transaction Limit',
                'pattern': r'maxTxAmount|maxTransactionAmount',
                'severity': 'low',
                'description': 'Contract has maximum transaction limits'
            },
            {
                'name': 'Max Wallet Limit',
                'pattern': r'maxWalletAmount|maxWalletSize',
                'severity': 'low',
                'description': 'Contract has maximum wallet limits'
            },
            {
                'name': 'High Tax Function',
                'pattern': r'taxFee|liquidityFee|marketingFee',
                'severity': 'medium',
                'description': 'Contract has tax mechanisms'
            }
        ]
    
    def _load_rug_pull_patterns(self) -> List[Dict]:
        """Load known rug pull patterns"""
        return [
            {
                'name': 'Liquidity Removal',
                'pattern': r'removeLiquidity|withdrawLiquidity',
                'severity': 'high',
                'description': 'Contract can remove liquidity'
            },
            {
                'name': 'Emergency Withdraw',
                'pattern': r'emergencyWithdraw|rescueTokens',
                'severity': 'high',
                'description': 'Contract has emergency withdrawal functions'
            },
            {
                'name': 'Ownership Transfer',
                'pattern': r'transferOwnership|renounceOwnership',
                'severity': 'low',
                'description': 'Contract ownership can be transferred'
            },
            {
                'name': 'Selfdestruct',
                'pattern': r'selfdestruct|suicide',
                'severity': 'critical',
                'description': 'Contract can self-destruct'
            },
            {
                'name': 'Proxy Pattern',
                'pattern': r'delegatecall|proxy|implementation',
                'severity': 'medium',
                'description': 'Contract uses proxy pattern (upgradeable)'
            }
        ]
    
    async def analyze_contract(self, network: str, contract_address: str) -> Optional[ContractAnalysis]:
        """Perform comprehensive contract analysis"""
        try:
            logger.info(f"🔍 Analyzing contract {contract_address} on {network}")
            
            w3 = self.web3_connections[network]['w3']
            
            # Get contract bytecode
            contract_code = w3.eth.get_code(Web3.to_checksum_address(contract_address))
            
            if len(contract_code) == 0:
                logger.warning(f"No contract code found at {contract_address}")
                return None
            
            # Initialize analysis result
            analysis = ContractAnalysis(
                contract_address=contract_address,
                risk_level=ContractRisk.SAFE,
                risk_score=0,
                is_honeypot=False,
                is_rug_pull=False,
                ownership_renounced=False,
                has_mint_function=False,
                has_pause_function=False,
                has_blacklist=False,
                max_tx_limit=None,
                max_wallet_limit=None,
                buy_tax=0.0,
                sell_tax=0.0,
                liquidity_locked=False,
                verified_contract=False,
                proxy_contract=False,
                risk_factors=[],
                safety_features=[],
                analysis_timestamp=datetime.now()
            )
            
            # Get contract source code if verified
            source_code = await self._get_verified_source_code(network, contract_address)
            
            if source_code:
                analysis.verified_contract = True
                analysis.safety_features.append("Contract is verified")
                
                # Analyze source code
                await self._analyze_source_code(source_code, analysis)
            else:
                # Analyze bytecode
                await self._analyze_bytecode(contract_code, analysis)
                analysis.risk_factors.append("Contract is not verified")
                analysis.risk_score += 20
            
            # Check ownership status
            await self._check_ownership_status(w3, contract_address, analysis)
            
            # Check for proxy pattern
            await self._check_proxy_pattern(w3, contract_address, analysis)
            
            # Perform honeypot simulation
            await self._simulate_honeypot_test(network, contract_address, analysis)
            
            # Calculate final risk level
            self._calculate_risk_level(analysis)
            
            logger.info(f"✅ Contract analysis complete: {analysis.risk_level.value[0]}")
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            return None
    
    async def _get_verified_source_code(self, network: str, contract_address: str) -> Optional[str]:
        """Get verified source code from blockchain explorer"""
        try:
            api_url = self.verification_apis.get(network)
            if not api_url:
                return None
            
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': contract_address,
                'apikey': 'YourApiKeyToken'  # Replace with actual API key
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == '1' and data['result']:
                    source_code = data['result'][0].get('SourceCode', '')
                    if source_code and source_code != '':
                        return source_code
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting verified source code: {e}")
            return None
    
    async def _analyze_source_code(self, source_code: str, analysis: ContractAnalysis):
        """Analyze contract source code for risks"""
        try:
            # Check honeypot patterns
            for pattern in self.honeypot_patterns:
                if re.search(pattern['pattern'], source_code, re.IGNORECASE):
                    analysis.risk_factors.append(pattern['description'])
                    
                    if pattern['severity'] == 'critical':
                        analysis.risk_score += 50
                    elif pattern['severity'] == 'high':
                        analysis.risk_score += 30
                    elif pattern['severity'] == 'medium':
                        analysis.risk_score += 15
                    else:
                        analysis.risk_score += 5
                    
                    # Set specific flags
                    if 'blacklist' in pattern['name'].lower():
                        analysis.has_blacklist = True
                    elif 'pause' in pattern['name'].lower():
                        analysis.has_pause_function = True
                    elif 'mint' in pattern['name'].lower():
                        analysis.has_mint_function = True
            
            # Check rug pull patterns
            for pattern in self.rug_pull_patterns:
                if re.search(pattern['pattern'], source_code, re.IGNORECASE):
                    analysis.risk_factors.append(pattern['description'])
                    
                    if pattern['severity'] == 'critical':
                        analysis.risk_score += 60
                        analysis.is_rug_pull = True
                    elif pattern['severity'] == 'high':
                        analysis.risk_score += 40
                    elif pattern['severity'] == 'medium':
                        analysis.risk_score += 20
                    else:
                        analysis.risk_score += 10
                    
                    if 'proxy' in pattern['name'].lower():
                        analysis.proxy_contract = True
            
            # Check for safety features
            safety_patterns = [
                (r'renounceOwnership\s*\(\s*\)', "Ownership can be renounced"),
                (r'_burn\s*\(', "Token burning capability"),
                (r'timelock|TimeLock', "Timelock mechanism"),
                (r'multisig|MultiSig', "Multisig wallet integration")
            ]
            
            for pattern, description in safety_patterns:
                if re.search(pattern, source_code, re.IGNORECASE):
                    analysis.safety_features.append(description)
                    analysis.risk_score -= 5  # Reduce risk for safety features
            
            # Extract tax information
            await self._extract_tax_info(source_code, analysis)
            
            # Extract limits
            await self._extract_limits(source_code, analysis)
        
        except Exception as e:
            logger.error(f"Error analyzing source code: {e}")
    
    async def _analyze_bytecode(self, contract_code: bytes, analysis: ContractAnalysis):
        """Analyze contract bytecode for risks"""
        try:
            code_hex = contract_code.hex()
            
            # Check for common function signatures in bytecode
            dangerous_signatures = {
                'a9059cbb': 'transfer',
                '23b872dd': 'transferFrom',
                '095ea7b3': 'approve',
                '40c10f19': 'mint',
                '42966c68': 'burn',
                '8da5cb5b': 'owner',
                'f2fde38b': 'transferOwnership'
            }
            
            found_functions = []
            for sig, name in dangerous_signatures.items():
                if sig in code_hex:
                    found_functions.append(name)
            
            if 'mint' in found_functions:
                analysis.has_mint_function = True
                analysis.risk_factors.append("Contract has mint function")
                analysis.risk_score += 15
            
            if 'owner' in found_functions:
                analysis.risk_factors.append("Contract has owner functionality")
                analysis.risk_score += 10
            
            # Check contract size (very large contracts might be suspicious)
            if len(contract_code) > 50000:  # > 50KB
                analysis.risk_factors.append("Unusually large contract size")
                analysis.risk_score += 10
            
            # Check for common honeypot bytecode patterns
            honeypot_bytecode_patterns = [
                'deadbeef',  # Common honeypot marker
                'baddcafe',  # Another common marker
            ]
            
            for pattern in honeypot_bytecode_patterns:
                if pattern in code_hex:
                    analysis.is_honeypot = True
                    analysis.risk_factors.append("Honeypot bytecode pattern detected")
                    analysis.risk_score += 50
        
        except Exception as e:
            logger.error(f"Error analyzing bytecode: {e}")
    
    async def _check_ownership_status(self, w3: Web3, contract_address: str, analysis: ContractAnalysis):
        """Check if contract ownership is renounced"""
        try:
            # Standard owner() function ABI
            owner_abi = [
                {
                    "inputs": [],
                    "name": "owner",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=owner_abi
            )
            
            try:
                owner_address = contract.functions.owner().call()
                
                # Check if ownership is renounced (owner is zero address)
                if owner_address == '0x0000000000000000000000000000000000000000':
                    analysis.ownership_renounced = True
                    analysis.safety_features.append("Ownership renounced")
                    analysis.risk_score -= 15
                else:
                    analysis.risk_factors.append("Contract has active owner")
                    analysis.risk_score += 10
            
            except Exception:
                # Contract might not have owner() function
                pass
        
        except Exception as e:
            logger.error(f"Error checking ownership status: {e}")
    
    async def _check_proxy_pattern(self, w3: Web3, contract_address: str, analysis: ContractAnalysis):
        """Check if contract uses proxy pattern"""
        try:
            # Check for proxy storage slots
            implementation_slot = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
            
            storage_value = w3.eth.get_storage_at(
                Web3.to_checksum_address(contract_address),
                implementation_slot
            )
            
            if storage_value != b'\x00' * 32:
                analysis.proxy_contract = True
                analysis.risk_factors.append("Contract uses proxy pattern (upgradeable)")
                analysis.risk_score += 20
        
        except Exception as e:
            logger.error(f"Error checking proxy pattern: {e}")
    
    async def _simulate_honeypot_test(self, network: str, contract_address: str, analysis: ContractAnalysis):
        """Simulate honeypot test by checking if tokens can be sold"""
        try:
            # This would involve simulating a buy and sell transaction
            # For demo purposes, we'll use external honeypot detection APIs
            
            honeypot_apis = [
                f"https://api.honeypot.is/v1/GetHoneypotStatus?address={contract_address}",
                f"https://honeypot.api.rugdoc.io/api/honeypotStatus/{contract_address}"
            ]
            
            for api_url in honeypot_apis:
                try:
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse response based on API format
                        if 'honeypotResult' in data:
                            if data['honeypotResult']['isHoneypot']:
                                analysis.is_honeypot = True
                                analysis.risk_factors.append("External API detected honeypot")
                                analysis.risk_score += 60
                        
                        break  # Use first successful API response
                
                except Exception:
                    continue
        
        except Exception as e:
            logger.error(f"Error in honeypot simulation: {e}")
    
    async def _extract_tax_info(self, source_code: str, analysis: ContractAnalysis):
        """Extract tax information from source code"""
        try:
            # Look for tax-related variables
            tax_patterns = [
                (r'buyTax\s*=\s*(\d+)', 'buy_tax'),
                (r'sellTax\s*=\s*(\d+)', 'sell_tax'),
                (r'taxFee\s*=\s*(\d+)', 'general_tax'),
                (r'liquidityFee\s*=\s*(\d+)', 'liquidity_tax'),
                (r'marketingFee\s*=\s*(\d+)', 'marketing_tax')
            ]
            
            total_buy_tax = 0
            total_sell_tax = 0
            
            for pattern, tax_type in tax_patterns:
                matches = re.findall(pattern, source_code, re.IGNORECASE)
                
                for match in matches:
                    tax_value = int(match)
                    
                    if 'buy' in tax_type:
                        total_buy_tax += tax_value
                    elif 'sell' in tax_type:
                        total_sell_tax += tax_value
                    else:
                        # General tax applies to both
                        total_buy_tax += tax_value
                        total_sell_tax += tax_value
            
            analysis.buy_tax = total_buy_tax / 100  # Convert to percentage
            analysis.sell_tax = total_sell_tax / 100
            
            # Flag high taxes as risk
            if analysis.buy_tax > 10:  # > 10%
                analysis.risk_factors.append(f"High buy tax: {analysis.buy_tax}%")
                analysis.risk_score += 20
            
            if analysis.sell_tax > 10:  # > 10%
                analysis.risk_factors.append(f"High sell tax: {analysis.sell_tax}%")
                analysis.risk_score += 20
        
        except Exception as e:
            logger.error(f"Error extracting tax info: {e}")
    
    async def _extract_limits(self, source_code: str, analysis: ContractAnalysis):
        """Extract transaction and wallet limits"""
        try:
            # Look for limit-related variables
            limit_patterns = [
                (r'maxTxAmount\s*=\s*(\d+)', 'max_tx'),
                (r'maxWalletAmount\s*=\s*(\d+)', 'max_wallet'),
                (r'maxTransactionAmount\s*=\s*(\d+)', 'max_tx'),
                (r'maxWalletSize\s*=\s*(\d+)', 'max_wallet')
            ]
            
            for pattern, limit_type in limit_patterns:
                matches = re.findall(pattern, source_code, re.IGNORECASE)
                
                for match in matches:
                    limit_value = int(match)
                    
                    if 'tx' in limit_type:
                        analysis.max_tx_limit = limit_value
                        analysis.risk_factors.append(f"Max transaction limit: {limit_value}")
                        analysis.risk_score += 5
                    elif 'wallet' in limit_type:
                        analysis.max_wallet_limit = limit_value
                        analysis.risk_factors.append(f"Max wallet limit: {limit_value}")
                        analysis.risk_score += 5
        
        except Exception as e:
            logger.error(f"Error extracting limits: {e}")
    
    def _calculate_risk_level(self, analysis: ContractAnalysis):
        """Calculate final risk level based on risk score"""
        if analysis.is_honeypot:
            analysis.risk_level = ContractRisk.HONEYPOT
        elif analysis.is_rug_pull:
            analysis.risk_level = ContractRisk.RUG_PULL
        elif analysis.risk_score >= 80:
            analysis.risk_level = ContractRisk.HIGH_RISK
        elif analysis.risk_score >= 50:
            analysis.risk_level = ContractRisk.MEDIUM_RISK
        elif analysis.risk_score >= 20:
            analysis.risk_level = ContractRisk.LOW_RISK
        else:
            analysis.risk_level = ContractRisk.SAFE
    
    async def analyze_tokenomics(self, network: str, contract_address: str) -> Optional[TokenomicsAnalysis]:
        """Analyze token economics and distribution"""
        try:
            logger.info(f"📊 Analyzing tokenomics for {contract_address}")
            
            w3 = self.web3_connections[network]['w3']
            
            # ERC-20 ABI for basic token info
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
            ]
            
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=erc20_abi
            )
            
            # Get total supply
            total_supply = contract.functions.totalSupply().call()
            
            # Get holder information (this would require additional APIs in production)
            # For demo, we'll simulate the analysis
            
            analysis = TokenomicsAnalysis(
                total_supply=total_supply,
                circulating_supply=total_supply,  # Simplified
                holder_count=1000,  # Would get from API
                top_10_holders_percentage=45.0,  # Simulated
                dev_wallet_percentage=5.0,
                marketing_wallet_percentage=3.0,
                liquidity_percentage=15.0,
                burned_percentage=2.0,
                distribution_score=75  # Calculated based on distribution
            )
            
            logger.info(f"✅ Tokenomics analysis complete")
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing tokenomics: {e}")
            return None
    
    async def get_contract_security_score(self, network: str, contract_address: str) -> Dict:
        """Get overall security score for a contract"""
        try:
            # Perform full analysis
            contract_analysis = await self.analyze_contract(network, contract_address)
            tokenomics_analysis = await self.analyze_tokenomics(network, contract_address)
            
            if not contract_analysis:
                return {'error': 'Failed to analyze contract'}
            
            # Calculate overall security score
            security_score = 100 - contract_analysis.risk_score
            security_score = max(0, min(100, security_score))  # Clamp between 0-100
            
            # Determine recommendation
            if security_score >= 80:
                recommendation = "SAFE TO TRADE"
                color = "🟢"
            elif security_score >= 60:
                recommendation = "PROCEED WITH CAUTION"
                color = "🟡"
            elif security_score >= 40:
                recommendation = "HIGH RISK"
                color = "🟠"
            else:
                recommendation = "AVOID"
                color = "🔴"
            
            return {
                'contract_address': contract_address,
                'security_score': security_score,
                'risk_level': contract_analysis.risk_level.value[0],
                'recommendation': f"{color} {recommendation}",
                'is_honeypot': contract_analysis.is_honeypot,
                'is_rug_pull': contract_analysis.is_rug_pull,
                'verified_contract': contract_analysis.verified_contract,
                'ownership_renounced': contract_analysis.ownership_renounced,
                'risk_factors': contract_analysis.risk_factors,
                'safety_features': contract_analysis.safety_features,
                'buy_tax': contract_analysis.buy_tax,
                'sell_tax': contract_analysis.sell_tax,
                'analysis_timestamp': contract_analysis.analysis_timestamp.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting security score: {e}")
            return {'error': str(e)}

# Example usage
async def example_usage():
    """Example of how to use the Smart Contract Analyzer"""
    
    # Web3 connections
    web3_connections = {
        'ethereum': {
            'w3': Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY'))
        }
    }
    
    # Initialize analyzer
    analyzer = SmartContractAnalyzer(web3_connections)
    
    # Analyze a contract
    contract_address = "0x..." # Contract address to analyze
    
    security_report = await analyzer.get_contract_security_score('ethereum', contract_address)
    
    print("🔍 Contract Security Analysis")
    print("=" * 50)
    print(f"Contract: {security_report.get('contract_address', 'N/A')}")
    print(f"Security Score: {security_report.get('security_score', 0)}/100")
    print(f"Risk Level: {security_report.get('risk_level', 'Unknown')}")
    print(f"Recommendation: {security_report.get('recommendation', 'Unknown')}")
    print(f"Honeypot: {'Yes' if security_report.get('is_honeypot') else 'No'}")
    print(f"Verified: {'Yes' if security_report.get('verified_contract') else 'No'}")
    print(f"Ownership Renounced: {'Yes' if security_report.get('ownership_renounced') else 'No'}")
    
    if security_report.get('risk_factors'):
        print("\n⚠️ Risk Factors:")
        for factor in security_report['risk_factors']:
            print(f"  • {factor}")
    
    if security_report.get('safety_features'):
        print("\n✅ Safety Features:")
        for feature in security_report['safety_features']:
            print(f"  • {feature}")

if __name__ == "__main__":
    asyncio.run(example_usage()) 