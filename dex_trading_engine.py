#!/usr/bin/env python3
"""
🔥 ADVANCED DEX TRADING ENGINE 🔥
Direct smart contract interactions, gas optimization, and MEV strategies
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import time
from datetime import datetime, timedelta
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from eth_account import Account
from eth_account.signers.local import LocalAccount
import requests

logger = logging.getLogger(__name__)

class DEXType(Enum):
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    PANCAKESWAP_V2 = "pancakeswap_v2"
    SUSHISWAP = "sushiswap"
    QUICKSWAP = "quickswap"

class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"

@dataclass
class GasStrategy:
    """Gas pricing strategy for different urgency levels"""
    base_gas_price: int
    priority_fee: int
    max_fee_per_gas: int
    gas_limit: int
    urgency_multiplier: float = 1.0

@dataclass
class TradeParams:
    """Parameters for DEX trade execution"""
    token_in: str
    token_out: str
    amount_in: int
    amount_out_min: int
    slippage_tolerance: float
    deadline: int
    gas_strategy: GasStrategy
    dex_type: DEXType
    recipient: str

@dataclass
class TradeResult:
    """Result of a DEX trade execution"""
    tx_hash: str
    status: TransactionStatus
    gas_used: int
    gas_price: int
    amount_in: int
    amount_out: int
    slippage: float
    execution_time: float
    block_number: int
    timestamp: datetime

class DEXTradingEngine:
    """Advanced DEX trading engine with direct smart contract interactions"""
    
    def __init__(self, web3_connections: Dict, private_key: str):
        self.web3_connections = web3_connections
        self.account: LocalAccount = Account.from_key(private_key)
        self.wallet_address = self.account.address
        
        # DEX router addresses and ABIs
        self.dex_configs = self._load_dex_configs()
        self.router_contracts = {}
        self.factory_contracts = {}
        
        # Gas tracking and optimization
        self.gas_tracker = GasTracker()
        
        # MEV protection and strategies
        self.mev_protection = True
        self.flashbots_enabled = False
        
        # Initialize contracts
        self._initialize_contracts()
        
        logger.info(f"🔥 DEX Trading Engine initialized for wallet: {self.wallet_address}")
    
    def _load_dex_configs(self) -> Dict:
        """Load DEX configurations with router addresses and ABIs"""
        return {
            'ethereum': {
                DEXType.UNISWAP_V2: {
                    'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                    'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                    'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
                },
                DEXType.UNISWAP_V3: {
                    'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                    'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                    'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
                },
                DEXType.SUSHISWAP: {
                    'router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                    'factory': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                    'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
                }
            },
            'bsc': {
                DEXType.PANCAKESWAP_V2: {
                    'router': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                    'factory': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
                    'weth': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'  # WBNB
                }
            },
            'polygon': {
                DEXType.QUICKSWAP: {
                    'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                    'factory': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                    'weth': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'  # WMATIC
                }
            }
        }
    
    def _initialize_contracts(self):
        """Initialize smart contracts for all supported DEXs"""
        # Load ABIs
        router_v2_abi = self._load_uniswap_v2_router_abi()
        router_v3_abi = self._load_uniswap_v3_router_abi()
        factory_abi = self._load_factory_abi()
        
        for network, dexs in self.dex_configs.items():
            if network not in self.web3_connections:
                continue
                
            w3 = self.web3_connections[network]['w3']
            self.router_contracts[network] = {}
            self.factory_contracts[network] = {}
            
            for dex_type, config in dexs.items():
                try:
                    # Initialize router contract
                    if dex_type in [DEXType.UNISWAP_V3]:
                        abi = router_v3_abi
                    else:
                        abi = router_v2_abi
                    
                    router_contract = w3.eth.contract(
                        address=Web3.to_checksum_address(config['router']),
                        abi=abi
                    )
                    self.router_contracts[network][dex_type] = router_contract
                    
                    # Initialize factory contract
                    factory_contract = w3.eth.contract(
                        address=Web3.to_checksum_address(config['factory']),
                        abi=factory_abi
                    )
                    self.factory_contracts[network][dex_type] = factory_contract
                    
                    logger.info(f"✅ Initialized {dex_type.value} contracts on {network}")
                    
                except Exception as e:
                    logger.error(f"Error initializing {dex_type.value} on {network}: {e}")
    
    def _load_uniswap_v2_router_abi(self) -> List[Dict]:
        """Load Uniswap V2 Router ABI"""
        return [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForETH",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _load_uniswap_v3_router_abi(self) -> List[Dict]:
        """Load Uniswap V3 Router ABI"""
        return [
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "address", "name": "tokenIn", "type": "address"},
                            {"internalType": "address", "name": "tokenOut", "type": "address"},
                            {"internalType": "uint24", "name": "fee", "type": "uint24"},
                            {"internalType": "address", "name": "recipient", "type": "address"},
                            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                        ],
                        "internalType": "struct ISwapRouter.ExactInputSingleParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInputSingle",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
    
    def _load_factory_abi(self) -> List[Dict]:
        """Load Factory ABI for pair detection"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"}
                ],
                "name": "getPair",
                "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def execute_buy_order(self, network: str, token_address: str, 
                               eth_amount: float, slippage: float = 0.03,
                               dex_type: DEXType = DEXType.UNISWAP_V2) -> Optional[TradeResult]:
        """Execute a buy order for a meme token"""
        try:
            start_time = time.time()
            
            w3 = self.web3_connections[network]['w3']
            router_contract = self.router_contracts[network][dex_type]
            
            # Get WETH address
            weth_address = self.dex_configs[network][dex_type]['weth']
            
            # Convert ETH amount to Wei
            amount_in = w3.to_wei(eth_amount, 'ether')
            
            # Get expected output amount
            path = [weth_address, Web3.to_checksum_address(token_address)]
            amounts_out = router_contract.functions.getAmountsOut(amount_in, path).call()
            amount_out_expected = amounts_out[-1]
            
            # Calculate minimum output with slippage
            amount_out_min = int(amount_out_expected * (1 - slippage))
            
            # Get optimized gas strategy
            gas_strategy = await self.gas_tracker.get_optimal_gas_strategy(network, urgency='high')
            
            # Build transaction
            deadline = int(time.time()) + 300  # 5 minutes
            
            transaction = router_contract.functions.swapExactETHForTokens(
                amount_out_min,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'value': amount_in,
                'gas': gas_strategy.gas_limit,
                'gasPrice': gas_strategy.base_gas_price,
                'nonce': w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"🚀 Buy order submitted: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = await self._wait_for_transaction_receipt(w3, tx_hash, timeout=60)
            
            if receipt and receipt.status == 1:
                # Calculate actual amounts and slippage
                actual_amount_out = self._extract_amount_out_from_receipt(receipt, token_address)
                actual_slippage = (amount_out_expected - actual_amount_out) / amount_out_expected
                
                execution_time = time.time() - start_time
                
                result = TradeResult(
                    tx_hash=tx_hash.hex(),
                    status=TransactionStatus.CONFIRMED,
                    gas_used=receipt.gasUsed,
                    gas_price=receipt.effectiveGasPrice,
                    amount_in=amount_in,
                    amount_out=actual_amount_out,
                    slippage=actual_slippage,
                    execution_time=execution_time,
                    block_number=receipt.blockNumber,
                    timestamp=datetime.now()
                )
                
                logger.info(f"✅ Buy order confirmed: {actual_amount_out} tokens received")
                return result
            else:
                logger.error("❌ Buy order failed")
                return TradeResult(
                    tx_hash=tx_hash.hex(),
                    status=TransactionStatus.FAILED,
                    gas_used=0,
                    gas_price=gas_strategy.base_gas_price,
                    amount_in=amount_in,
                    amount_out=0,
                    slippage=0,
                    execution_time=time.time() - start_time,
                    block_number=0,
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            return None
    
    async def execute_sell_order(self, network: str, token_address: str,
                                token_amount: int, slippage: float = 0.03,
                                dex_type: DEXType = DEXType.UNISWAP_V2) -> Optional[TradeResult]:
        """Execute a sell order for a meme token"""
        try:
            start_time = time.time()
            
            w3 = self.web3_connections[network]['w3']
            router_contract = self.router_contracts[network][dex_type]
            
            # Get WETH address
            weth_address = self.dex_configs[network][dex_type]['weth']
            
            # Get expected output amount
            path = [Web3.to_checksum_address(token_address), weth_address]
            amounts_out = router_contract.functions.getAmountsOut(token_amount, path).call()
            amount_out_expected = amounts_out[-1]
            
            # Calculate minimum output with slippage
            amount_out_min = int(amount_out_expected * (1 - slippage))
            
            # Check and approve token if necessary
            await self._ensure_token_approval(network, token_address, token_amount, router_contract.address)
            
            # Get optimized gas strategy
            gas_strategy = await self.gas_tracker.get_optimal_gas_strategy(network, urgency='high')
            
            # Build transaction
            deadline = int(time.time()) + 300  # 5 minutes
            
            transaction = router_contract.functions.swapExactTokensForETH(
                token_amount,
                amount_out_min,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'gas': gas_strategy.gas_limit,
                'gasPrice': gas_strategy.base_gas_price,
                'nonce': w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"🚀 Sell order submitted: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = await self._wait_for_transaction_receipt(w3, tx_hash, timeout=60)
            
            if receipt and receipt.status == 1:
                # Calculate actual amounts and slippage
                actual_amount_out = self._extract_eth_amount_from_receipt(receipt)
                actual_slippage = (amount_out_expected - actual_amount_out) / amount_out_expected
                
                execution_time = time.time() - start_time
                
                result = TradeResult(
                    tx_hash=tx_hash.hex(),
                    status=TransactionStatus.CONFIRMED,
                    gas_used=receipt.gasUsed,
                    gas_price=receipt.effectiveGasPrice,
                    amount_in=token_amount,
                    amount_out=actual_amount_out,
                    slippage=actual_slippage,
                    execution_time=execution_time,
                    block_number=receipt.blockNumber,
                    timestamp=datetime.now()
                )
                
                logger.info(f"✅ Sell order confirmed: {w3.from_wei(actual_amount_out, 'ether')} ETH received")
                return result
            else:
                logger.error("❌ Sell order failed")
                return TradeResult(
                    tx_hash=tx_hash.hex(),
                    status=TransactionStatus.FAILED,
                    gas_used=0,
                    gas_price=gas_strategy.base_gas_price,
                    amount_in=token_amount,
                    amount_out=0,
                    slippage=0,
                    execution_time=time.time() - start_time,
                    block_number=0,
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            return None
    
    async def _ensure_token_approval(self, network: str, token_address: str, 
                                   amount: int, spender: str):
        """Ensure token is approved for trading"""
        try:
            w3 = self.web3_connections[network]['w3']
            
            # ERC-20 approval ABI
            erc20_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "spender", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "address", "name": "owner", "type": "address"},
                        {"internalType": "address", "name": "spender", "type": "address"}
                    ],
                    "name": "allowance",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            token_contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                self.wallet_address, spender
            ).call()
            
            if current_allowance < amount:
                # Need to approve
                logger.info(f"🔓 Approving token {token_address} for trading")
                
                # Approve maximum amount for efficiency
                max_approval = 2**256 - 1
                
                gas_strategy = await self.gas_tracker.get_optimal_gas_strategy(network, urgency='medium')
                
                approve_txn = token_contract.functions.approve(
                    spender, max_approval
                ).build_transaction({
                    'from': self.wallet_address,
                    'gas': 60000,  # Standard approval gas
                    'gasPrice': gas_strategy.base_gas_price,
                    'nonce': w3.eth.get_transaction_count(self.wallet_address)
                })
                
                signed_txn = self.account.sign_transaction(approve_txn)
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                # Wait for approval confirmation
                receipt = await self._wait_for_transaction_receipt(w3, tx_hash, timeout=30)
                
                if receipt and receipt.status == 1:
                    logger.info("✅ Token approval confirmed")
                else:
                    raise Exception("Token approval failed")
        
        except Exception as e:
            logger.error(f"Error ensuring token approval: {e}")
            raise
    
    async def _wait_for_transaction_receipt(self, w3: Web3, tx_hash: bytes, 
                                          timeout: int = 60) -> Optional[Any]:
        """Wait for transaction receipt with timeout"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    receipt = w3.eth.get_transaction_receipt(tx_hash)
                    return receipt
                except TransactionNotFound:
                    await asyncio.sleep(1)
                    continue
            
            logger.warning(f"Transaction {tx_hash.hex()} timed out after {timeout}s")
            return None
        
        except Exception as e:
            logger.error(f"Error waiting for transaction receipt: {e}")
            return None
    
    def _extract_amount_out_from_receipt(self, receipt: Any, token_address: str) -> int:
        """Extract the actual amount out from transaction receipt"""
        try:
            # Parse logs to find Transfer events
            # This is simplified - in production, use proper log parsing
            return 0  # Placeholder
        except Exception as e:
            logger.error(f"Error extracting amount out: {e}")
            return 0
    
    def _extract_eth_amount_from_receipt(self, receipt: Any) -> int:
        """Extract ETH amount from transaction receipt"""
        try:
            # Parse logs to find ETH transfer
            # This is simplified - in production, use proper log parsing
            return 0  # Placeholder
        except Exception as e:
            logger.error(f"Error extracting ETH amount: {e}")
            return 0
    
    async def get_token_price(self, network: str, token_address: str,
                            dex_type: DEXType = DEXType.UNISWAP_V2) -> Optional[float]:
        """Get current token price in ETH"""
        try:
            w3 = self.web3_connections[network]['w3']
            router_contract = self.router_contracts[network][dex_type]
            weth_address = self.dex_configs[network][dex_type]['weth']
            
            # Get price for 1 token
            one_token = 10**18  # Assuming 18 decimals
            path = [Web3.to_checksum_address(token_address), weth_address]
            
            amounts_out = router_contract.functions.getAmountsOut(one_token, path).call()
            eth_amount = amounts_out[-1]
            
            return w3.from_wei(eth_amount, 'ether')
        
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            return None
    
    async def check_liquidity(self, network: str, token_address: str,
                            dex_type: DEXType = DEXType.UNISWAP_V2) -> Dict:
        """Check liquidity for a token pair"""
        try:
            w3 = self.web3_connections[network]['w3']
            factory_contract = self.factory_contracts[network][dex_type]
            weth_address = self.dex_configs[network][dex_type]['weth']
            
            # Get pair address
            pair_address = factory_contract.functions.getPair(
                Web3.to_checksum_address(token_address),
                weth_address
            ).call()
            
            if pair_address == '0x0000000000000000000000000000000000000000':
                return {'exists': False, 'liquidity_eth': 0, 'liquidity_token': 0}
            
            # Get pair reserves (simplified)
            # In production, use proper pair contract ABI
            return {
                'exists': True,
                'pair_address': pair_address,
                'liquidity_eth': 0,  # Would get from pair contract
                'liquidity_token': 0  # Would get from pair contract
            }
        
        except Exception as e:
            logger.error(f"Error checking liquidity: {e}")
            return {'exists': False, 'liquidity_eth': 0, 'liquidity_token': 0}

class GasTracker:
    """Advanced gas tracking and optimization"""
    
    def __init__(self):
        self.network_configs = {
            'ethereum': {'base_gas': 21000, 'swap_gas': 150000},
            'bsc': {'base_gas': 21000, 'swap_gas': 120000},
            'polygon': {'base_gas': 21000, 'swap_gas': 100000}
        }
    
    async def get_optimal_gas_strategy(self, network: str, urgency: str = 'medium') -> GasStrategy:
        """Get optimal gas strategy based on network conditions"""
        try:
            # Urgency multipliers
            multipliers = {
                'low': 1.0,
                'medium': 1.2,
                'high': 1.5,
                'ultra': 2.0
            }
            
            multiplier = multipliers.get(urgency, 1.2)
            base_config = self.network_configs.get(network, self.network_configs['ethereum'])
            
            # Base gas prices by network
            base_prices = {
                'ethereum': 20000000000,  # 20 gwei
                'bsc': 5000000000,        # 5 gwei
                'polygon': 30000000000    # 30 gwei
            }
            
            base_price = base_prices.get(network, 20000000000)
            
            return GasStrategy(
                base_gas_price=int(base_price * multiplier),
                priority_fee=int(base_price * 0.1),
                max_fee_per_gas=int(base_price * multiplier * 1.5),
                gas_limit=base_config['swap_gas'],
                urgency_multiplier=multiplier
            )
        
        except Exception as e:
            logger.error(f"Error getting gas strategy: {e}")
            # Return default strategy
            return GasStrategy(
                base_gas_price=20000000000,  # 20 gwei
                priority_fee=2000000000,     # 2 gwei
                max_fee_per_gas=50000000000, # 50 gwei
                gas_limit=150000,
                urgency_multiplier=1.2
            )

class MEVProtection:
    """MEV protection and front-running strategies"""
    
    def __init__(self, flashbots_enabled: bool = False):
        self.flashbots_enabled = flashbots_enabled
        self.private_pools = []
    
    async def submit_private_transaction(self, signed_transaction: bytes) -> str:
        """Submit transaction through private mempool"""
        try:
            if self.flashbots_enabled:
                # Submit to Flashbots
                return await self._submit_to_flashbots(signed_transaction)
            else:
                # Use other private pools or direct submission
                return await self._submit_direct(signed_transaction)
        
        except Exception as e:
            logger.error(f"Error submitting private transaction: {e}")
            raise
    
    async def _submit_to_flashbots(self, signed_transaction: bytes) -> str:
        """Submit transaction to Flashbots"""
        # Placeholder for Flashbots integration
        # In production, use flashbots-py library
        pass
    
    async def _submit_direct(self, signed_transaction: bytes) -> str:
        """Submit transaction directly"""
        # Direct submission to avoid public mempool
        pass

# Example usage
async def example_usage():
    """Example of how to use the DEX Trading Engine"""
    
    # Configuration
    web3_connections = {
        'ethereum': {
            'w3': Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY')),
            'chain_id': 1
        }
    }
    
    private_key = "YOUR_PRIVATE_KEY"  # Never hardcode in production
    
    # Initialize trading engine
    trading_engine = DEXTradingEngine(web3_connections, private_key)
    
    # Example: Buy a meme token
    token_address = "0x..." # Token contract address
    eth_amount = 0.1  # 0.1 ETH
    
    result = await trading_engine.execute_buy_order(
        network='ethereum',
        token_address=token_address,
        eth_amount=eth_amount,
        slippage=0.05,  # 5% slippage tolerance
        dex_type=DEXType.UNISWAP_V2
    )
    
    if result and result.status == TransactionStatus.CONFIRMED:
        print(f"✅ Successfully bought tokens!")
        print(f"   TX Hash: {result.tx_hash}")
        print(f"   Tokens received: {result.amount_out}")
        print(f"   Slippage: {result.slippage:.2%}")
        print(f"   Gas used: {result.gas_used}")
    else:
        print("❌ Trade failed")

if __name__ == "__main__":
    asyncio.run(example_usage()) 