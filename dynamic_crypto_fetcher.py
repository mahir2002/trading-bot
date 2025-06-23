#!/usr/bin/env python3
"""
Dynamic Cryptocurrency Fetcher
Fetches all available trading pairs from Binance API instead of hardcoded data
"""

import requests
import json
from typing import Dict, List
import logging

class DynamicCryptoFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.binance.com/api/v3"
        
    def get_all_usdt_pairs(self) -> Dict[str, Dict]:
        """
        Fetch all USDT trading pairs from Binance API dynamically
        Returns a dictionary with symbol info including categories
        """
        try:
            # Get exchange info from Binance
            response = requests.get(f"{self.base_url}/exchangeInfo")
            response.raise_for_status()
            data = response.json()
            
            usdt_pairs = {}
            
            for symbol_info in data['symbols']:
                symbol = symbol_info['symbol']
                
                # Only include USDT pairs that are actively trading
                if (symbol.endswith('USDT') and 
                    symbol_info['status'] == 'TRADING' and
                    symbol_info['quoteAsset'] == 'USDT'):
                    
                    base_asset = symbol_info['baseAsset']
                    
                    # Categorize based on common patterns
                    category = self.categorize_crypto(base_asset, symbol)
                    
                    usdt_pairs[symbol] = {
                        'name': self.get_crypto_name(base_asset),
                        'emoji': self.get_crypto_emoji(base_asset),
                        'category': category,
                        'baseAsset': base_asset,
                        'status': symbol_info['status']
                    }
            
            self.logger.info(f"✅ Fetched {len(usdt_pairs)} USDT trading pairs dynamically")
            return usdt_pairs
            
        except Exception as e:
            self.logger.error(f"Error fetching crypto pairs: {e}")
            return self.get_fallback_pairs()
    
    def categorize_crypto(self, base_asset: str, symbol: str) -> str:
        """
        Categorize cryptocurrency based on common patterns
        """
        base_asset = base_asset.upper()
        
        # Major cryptocurrencies
        major_coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'LTC', 'BCH', 'ETC', 'XLM', 'VET', 'TRX', 'FIL', 'EOS', 'THETA', 'AAVE']
        if base_asset in major_coins:
            return 'Major'
        
        # DeFi tokens
        defi_tokens = ['UNI', 'AAVE', 'COMP', 'MKR', 'SUSHI', 'CRV', '1INCH', 'YFI', 'CAKE', 'ALPHA', 'SNX', 'BAL', 'RUNE', 'KAVA', 'DYDX', 'GMX', 'JOE', 'SPELL', 'CVX', 'FXS', 'FRAX', 'LIDO', 'RPL', 'LDO']
        if base_asset in defi_tokens:
            return 'DeFi'
        
        # Memecoins
        meme_coins = ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK', 'WIF', 'BABYDOGE', 'ELON', 'AKITA', 'KISHU', 'SAFEMOON', 'DOGELON', 'HOGE', 'WOJAK', 'LADYS', 'TURBO', 'AIDOGE', 'PEPE2', 'MEME', 'DEGEN']
        if base_asset in meme_coins:
            return 'Meme'
        
        # Gaming & NFT
        gaming_tokens = ['AXS', 'SAND', 'MANA', 'ENJ', 'GALA', 'ILV', 'ALICE', 'TLM', 'CHR', 'YGG', 'SLP', 'GHST', 'REVV', 'SUPER', 'PYR', 'NFTX', 'RARI', 'WHALE', 'FLOW', 'WAX', 'IMX', 'GODS', 'VOXEL', 'HIGH']
        if base_asset in gaming_tokens:
            return 'Gaming'
        
        # AI & Data
        ai_tokens = ['FET', 'OCEAN', 'AGIX', 'RENDER', 'GRT', 'NMR', 'CTXC', 'DKA', 'AIOZ', 'PHB', 'COTI', 'RNDR', 'TAO', 'ARKM', 'WLD', 'AI', 'GPT', 'RNDR']
        if base_asset in ai_tokens:
            return 'AI'
        
        # Layer 1 & 2
        layer1_tokens = ['NEAR', 'ATOM', 'ALGO', 'FTM', 'ONE', 'HBAR', 'EGLD', 'THETA', 'LUNA', 'LUNC', 'USTC', 'ROSE', 'KLAY', 'WAVES', 'ICX', 'QTUM', 'ZIL', 'ONT', 'VET', 'IOST', 'TOMO', 'WAN', 'NULS', 'STEEM', 'LSK', 'ARK', 'STRAT', 'NAS', 'PIVX', 'SYS', 'DGB', 'RVN', 'MONA', 'VTC', 'GRS', 'PART', 'NAV', 'XZC', 'DASH', 'ZEC', 'XMR', 'DCR', 'SC', 'ZEN', 'BTCD', 'VIA', 'BLK', 'POT', 'DOGE', 'LTC', 'PPC', 'NMC', 'FTC', 'AUR', 'IXC', 'DVC', 'TRC', 'FRC', 'NVC', 'CNC', 'BQC', 'BTB', 'YAC', 'NET', 'GDC', 'WDC', 'KGC', 'HBN', 'TIPS', 'PHS', 'ALF', 'FST', 'DBL', 'SRC', 'LBRY', 'XPY', 'XCP', 'BITB', 'GEO', 'FLDC', 'MZC', 'UNO', 'PKB', 'CGA', 'SPA', 'NLG', 'GRLC']
        layer2_tokens = ['OP', 'ARB', 'LRC', 'IMX', 'METIS', 'BOBA', 'CELR', 'SKALE', 'MATIC']
        if base_asset in layer1_tokens:
            return 'Layer1'
        if base_asset in layer2_tokens:
            return 'Layer2'
        
        # Exchange tokens
        exchange_tokens = ['CRO', 'FTT', 'KCS', 'HT', 'OKB', 'LEO', 'BGB', 'GT', 'MX', 'WBT', 'BKRW', 'TKX']
        if base_asset in exchange_tokens:
            return 'Exchange'
        
        # Privacy coins
        privacy_coins = ['XMR', 'ZEC', 'DASH', 'FIRO', 'BEAM', 'GRIN', 'ARRR', 'DERO', 'HAVEN', 'OXEN']
        if base_asset in privacy_coins:
            return 'Privacy'
        
        # Stablecoins (though these shouldn't be in USDT pairs typically)
        stablecoins = ['USDC', 'BUSD', 'DAI', 'TUSD', 'USDD', 'FRAX', 'LUSD', 'USDP', 'GUSD', 'HUSD']
        if base_asset in stablecoins:
            return 'Stablecoin'
        
        # Storage & Infrastructure
        storage_tokens = ['FIL', 'AR', 'STORJ', 'SIA', 'BTT', 'HOT', 'ANKR', 'NKN', 'POKT', 'FLUX']
        if base_asset in storage_tokens:
            return 'Storage'
        
        # Oracle & Data
        oracle_tokens = ['LINK', 'BAND', 'API3', 'TRB', 'DIA', 'NEST', 'DOS', 'FLUX']
        if base_asset in oracle_tokens:
            return 'Oracle'
        
        # Social & Content
        social_tokens = ['CHZ', 'ENJ', 'MANA', 'THETA', 'TFUEL', 'LPT', 'AUDIO', 'RALLY', 'WHALE', 'MASK']
        if base_asset in social_tokens:
            return 'Social'
        
        # Enterprise & Business
        enterprise_tokens = ['VET', 'WTC', 'AMB', 'TRAC', 'TEL', 'DENT', 'KEY', 'DATA', 'DOCK', 'CENNZ']
        if base_asset in enterprise_tokens:
            return 'Enterprise'
        
        # Default category
        return 'Other'
    
    def get_crypto_name(self, base_asset: str) -> str:
        """
        Get full name for cryptocurrency
        """
        name_mapping = {
            # Major Cryptocurrencies
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'BNB',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'SOL': 'Solana',
            'DOT': 'Polkadot',
            'AVAX': 'Avalanche',
            'MATIC': 'Polygon',
            'LINK': 'Chainlink',
            'LTC': 'Litecoin',
            'BCH': 'Bitcoin Cash',
            'ETC': 'Ethereum Classic',
            'XLM': 'Stellar',
            'VET': 'VeChain',
            'TRX': 'TRON',
            'FIL': 'Filecoin',
            'EOS': 'EOS',
            'THETA': 'Theta Network',
            'AAVE': 'Aave',
            
            # DeFi Tokens
            'UNI': 'Uniswap',
            'COMP': 'Compound',
            'MKR': 'Maker',
            'SUSHI': 'SushiSwap',
            'CRV': 'Curve',
            '1INCH': '1inch',
            'YFI': 'Yearn Finance',
            'CAKE': 'PancakeSwap',
            'ALPHA': 'Alpha Finance',
            'SNX': 'Synthetix',
            'BAL': 'Balancer',
            'RUNE': 'THORChain',
            'KAVA': 'Kava',
            'DYDX': 'dYdX',
            'GMX': 'GMX',
            'JOE': 'Trader Joe',
            'SPELL': 'Spell Token',
            'CVX': 'Convex Finance',
            'FXS': 'Frax Share',
            'FRAX': 'Frax',
            'LDO': 'Lido DAO',
            'RPL': 'Rocket Pool',
            
            # Memecoins
            'DOGE': 'Dogecoin',
            'SHIB': 'Shiba Inu',
            'PEPE': 'Pepe',
            'FLOKI': 'Floki',
            'BONK': 'Bonk',
            'WIF': 'Dogwifhat',
            'BABYDOGE': 'Baby Doge Coin',
            'ELON': 'Dogelon Mars',
            'AKITA': 'Akita Inu',
            'KISHU': 'Kishu Inu',
            'SAFEMOON': 'SafeMoon',
            'DOGELON': 'Dogelon Mars',
            'HOGE': 'Hoge Finance',
            'WOJAK': 'Wojak',
            'LADYS': 'Milady Meme Coin',
            'TURBO': 'Turbo',
            'AIDOGE': 'AiDoge',
            'PEPE2': 'Pepe 2.0',
            'MEME': 'Memecoin',
            'DEGEN': 'Degen',
            
            # Gaming & NFT
            'AXS': 'Axie Infinity',
            'SAND': 'Sandbox',
            'MANA': 'Decentraland',
            'ENJ': 'Enjin',
            'GALA': 'Gala',
            'ILV': 'Illuvium',
            'ALICE': 'My Neighbor Alice',
            'TLM': 'Alien Worlds',
            'CHR': 'Chromia',
            'YGG': 'Yield Guild Games',
            'SLP': 'Smooth Love Potion',
            'GHST': 'Aavegotchi',
            'REVV': 'REVV',
            'SUPER': 'SuperFarm',
            'PYR': 'Vulcan Forged',
            'NFTX': 'NFTX',
            'RARI': 'Rarible',
            'WHALE': 'WHALE',
            'FLOW': 'Flow',
            'WAX': 'WAX',
            'IMX': 'Immutable X',
            'GODS': 'Gods Unchained',
            'VOXEL': 'Voxies',
            'HIGH': 'Highstreet',
            
            # AI & Data
            'FET': 'Fetch.ai',
            'OCEAN': 'Ocean Protocol',
            'AGIX': 'SingularityNET',
            'RENDER': 'Render',
            'GRT': 'The Graph',
            'NMR': 'Numeraire',
            'CTXC': 'Cortex',
            'DKA': 'dKargo',
            'AIOZ': 'AIOZ Network',
            'PHB': 'Phoenix Global',
            'COTI': 'COTI',
            'RNDR': 'Render Token',
            'TAO': 'Bittensor',
            'ARKM': 'Arkham',
            'WLD': 'Worldcoin',
            'AI': 'Sleepless AI',
            'GPT': 'CryptoGPT',
            
            # Layer 1 & 2
            'NEAR': 'NEAR Protocol',
            'ATOM': 'Cosmos',
            'ALGO': 'Algorand',
            'FTM': 'Fantom',
            'ONE': 'Harmony',
            'HBAR': 'Hedera',
            'EGLD': 'MultiversX',
            'LUNA': 'Terra Luna Classic',
            'LUNC': 'Terra Luna Classic',
            'USTC': 'TerraClassicUSD',
            'ROSE': 'Oasis Network',
            'KLAY': 'Klaytn',
            'WAVES': 'Waves',
            'ICX': 'ICON',
            'QTUM': 'Qtum',
            'ZIL': 'Zilliqa',
            'ONT': 'Ontology',
            'IOST': 'IOST',
            'TOMO': 'TomoChain',
            'WAN': 'Wanchain',
            'NULS': 'NULS',
            'STEEM': 'Steem',
            'LSK': 'Lisk',
            'ARK': 'Ark',
            'STRAT': 'Stratis',
            'NAS': 'Nebulas',
            'PIVX': 'PIVX',
            'SYS': 'Syscoin',
            'DGB': 'DigiByte',
            'RVN': 'Ravencoin',
            'MONA': 'MonaCoin',
            'VTC': 'Vertcoin',
            'GRS': 'Groestlcoin',
            'PART': 'Particl',
            'NAV': 'NavCoin',
            'XZC': 'Firo',
            'DASH': 'Dash',
            'ZEC': 'Zcash',
            'XMR': 'Monero',
            'DCR': 'Decred',
            'SC': 'Siacoin',
            'ZEN': 'Horizen',
            'OP': 'Optimism',
            'ARB': 'Arbitrum',
            'METIS': 'Metis',
            'BOBA': 'Boba Network',
            'CELR': 'Celer Network',
            'SKALE': 'SKALE',
            
            # Exchange Tokens
            'CRO': 'Cronos',
            'FTT': 'FTX Token',
            'KCS': 'KuCoin Token',
            'HT': 'Huobi Token',
            'OKB': 'OKB',
            'LEO': 'UNUS SED LEO',
            'BGB': 'Bitget Token',
            'GT': 'GateToken',
            'MX': 'MX Token',
            
            # Privacy Coins
            'FIRO': 'Firo',
            'BEAM': 'Beam',
            'GRIN': 'Grin',
            'ARRR': 'Pirate Chain',
            'DERO': 'Dero',
            'HAVEN': 'Haven Protocol',
            'OXEN': 'Oxen',
            
            # Storage & Infrastructure
            'AR': 'Arweave',
            'STORJ': 'Storj',
            'SIA': 'Siacoin',
            'BTT': 'BitTorrent',
            'HOT': 'Holo',
            'ANKR': 'Ankr',
            'NKN': 'NKN',
            'POKT': 'Pocket Network',
            'FLUX': 'Flux',
            
            # Oracle & Data
            'BAND': 'Band Protocol',
            'API3': 'API3',
            'TRB': 'Tellor',
            'DIA': 'DIA',
            'NEST': 'NEST Protocol',
            'DOS': 'DOS Network',
            
            # Social & Content
            'CHZ': 'Chiliz',
            'TFUEL': 'Theta Fuel',
            'LPT': 'Livepeer',
            'AUDIO': 'Audius',
            'RALLY': 'Rally',
            'MASK': 'Mask Network',
            
            # Enterprise & Business
            'WTC': 'Waltonchain',
            'AMB': 'Ambrosus',
            'TRAC': 'OriginTrail',
            'TEL': 'Telcoin',
            'DENT': 'Dent',
            'KEY': 'SelfKey',
            'DATA': 'Streamr',
            'DOCK': 'Dock',
            'CENNZ': 'Centrality',
            
            # Additional Popular Coins
            'HIVE': 'Hive',
            'STEEM': 'Steem',
            'EOS': 'EOS',
            'NEO': 'Neo',
            'GAS': 'Gas',
            'IOTA': 'IOTA',
            'XTZ': 'Tezos',
            'KSM': 'Kusama',
            'COMP': 'Compound',
            'BAT': 'Basic Attention Token',
            'ZRX': '0x',
            'REP': 'Augur',
            'KNC': 'Kyber Network',
            'LRC': 'Loopring',
            'RLC': 'iExec RLC',
            'STORJ': 'Storj',
            'GNT': 'Golem',
            'ANT': 'Aragon',
            'MLN': 'Melon',
            'SALT': 'SALT',
            'BNT': 'Bancor',
            'ICN': 'Iconomi',
            'WTC': 'Waltonchain',
            'REQ': 'Request Network',
            'MOD': 'Modum',
            'EVX': 'Everex',
            'CTR': 'Centra',
            'IOST': 'Internet of Services',
            'GO': 'GoChain',
            'ZIL': 'Zilliqa',
            'WAN': 'Wanchain',
            'POWR': 'Power Ledger',
            'ELF': 'aelf',
            'AION': 'Aion',
            'NEBL': 'Neblio',
            'BRD': 'Bread',
            'EDO': 'Eidoo',
            'WINGS': 'Wings',
            'NAV': 'NavCoin',
            'LUN': 'Lunyr',
            'TRIG': 'Triggers',
            'APPC': 'AppCoins',
            'VIBES': 'VIBES',
            'RCN': 'Ripio Credit Network',
            'PIVX': 'PIVX',
            'IOS': 'IOST',
            'CHAT': 'ChatCoin',
            'STEEM': 'Steem',
            'NANO': 'Nano',
            'VIA': 'Viacoin',
            'BLK': 'BlackCoin',
            'POT': 'PotCoin',
            'DGB': 'DigiByte',
            'MONA': 'MonaCoin',
            'CLOAK': 'CloakCoin',
            'SYS': 'Syscoin',
            'NEOS': 'NeosCoin',
            'DGD': 'DigixDAO',
            'GNO': 'Gnosis',
            'MCO': 'Monaco',
            'WTC': 'Waltonchain',
            'LRC': 'Loopring',
            'QTUM': 'Qtum',
            'YOYO': 'YOYOW',
            'ICO': 'ICO',
            'ELEC': 'Electrify.Asia',
            'ACAT': 'Alphacat',
            'BRDS': 'Birds',
            'NEBL': 'Neblio',
            'VIBE': 'VIBE',
            'LLT': 'LLToken',
            'BNTY': 'Bounty0x',
            'ICX': 'ICON',
            'TVK': 'Terra Virtua Kolect',
            'FOR': 'ForTube',
            'HARD': 'Kava Lend',
            'DODO': 'DODO',
            'TKO': 'Tokocrypto',
            'PROM': 'Prometeus',
            'PROS': 'Prosper',
            'BETH': 'Binance Beacon ETH',
            'SKL': 'SKALE Network',
            'SUSD': 'sUSD',
            'COVER': 'Cover Protocol',
            'GLMR': 'Moonbeam',
            'BAKE': 'BakeryToken',
            'BURGER': 'BurgerCities',
            'ATA': 'Automata Network',
            'CHESS': 'Tranchess',
            'TITAN': 'TitanSwap',
            'ASR': 'AS Roma Fan Token',
            'PSG': 'Paris Saint-Germain Fan Token',
            'JUV': 'Juventus Fan Token',
            'BAR': 'FC Barcelona Fan Token',
            'ATM': 'Atletico Madrid Fan Token',
            'SANTOS': 'Santos FC Fan Token',
            'CITY': 'Manchester City Fan Token',
            'OG': 'OG Fan Token'
        }
        
        return name_mapping.get(base_asset.upper(), base_asset)
    
    def get_crypto_emoji(self, base_asset: str) -> str:
        """
        Get emoji for cryptocurrency - Expanded mapping
        """
        emoji_mapping = {
            # Major Cryptocurrencies
            'BTC': '₿',
            'ETH': '⟠',
            'BNB': '🟡',
            'XRP': '💧',
            'ADA': '🔵',
            'SOL': '🌞',
            'DOT': '🔴',
            'AVAX': '🔺',
            'MATIC': '🟣',
            'LINK': '🔗',
            'LTC': '🥈',
            'BCH': '💚',
            'ETC': '🟢',
            'XLM': '⭐',
            'VET': '✅',
            'TRX': '🔥',
            'FIL': '📁',
            'EOS': '⚫',
            'THETA': '📺',
            'AAVE': '👻',
            
            # DeFi Tokens
            'UNI': '🦄',
            'COMP': '🏛️',
            'MKR': '🏗️',
            'SUSHI': '🍣',
            'CRV': '📈',
            '1INCH': '📏',
            'YFI': '💰',
            'CAKE': '🥞',
            'ALPHA': '🐺',
            'SNX': '⚡',
            'BAL': '⚖️',
            'RUNE': '🔱',
            'KAVA': '☕',
            'DYDX': '📊',
            'GMX': '📈',
            'JOE': '🏔️',
            'SPELL': '🪄',
            'CVX': '🔄',
            'FXS': '💎',
            'FRAX': '🏦',
            'LDO': '🌊',
            'RPL': '🚀',
            
            # Memecoins
            'DOGE': '🐕',
            'SHIB': '🐕‍🦺',
            'PEPE': '🐸',
            'FLOKI': '🐕‍🦺',
            'BONK': '🔨',
            'WIF': '🎩',
            'BABYDOGE': '🐶',
            'ELON': '🚀',
            'AKITA': '🐕',
            'KISHU': '🐕',
            'SAFEMOON': '🌙',
            'DOGELON': '🚀',
            'HOGE': '💎',
            'WOJAK': '😭',
            'LADYS': '👸',
            'TURBO': '💨',
            'AIDOGE': '🤖',
            'PEPE2': '🐸',
            'MEME': '😂',
            'DEGEN': '🎲',
            
            # Gaming & NFT
            'AXS': '🎮',
            'SAND': '🏖️',
            'MANA': '🌐',
            'ENJ': '💎',
            'GALA': '🎪',
            'ILV': '⚔️',
            'ALICE': '🐰',
            'TLM': '👽',
            'CHR': '🎨',
            'YGG': '🏰',
            'SLP': '💕',
            'GHST': '👻',
            'REVV': '🏎️',
            'SUPER': '🦸',
            'PYR': '🔥',
            'NFTX': '🖼️',
            'RARI': '🎨',
            'WHALE': '🐋',
            'FLOW': '🌊',
            'WAX': '🕯️',
            'IMX': '♾️',
            'GODS': '⚡',
            'VOXEL': '🧊',
            'HIGH': '🏢',
            
            # AI & Data
            'FET': '🤖',
            'OCEAN': '🌊',
            'AGIX': '🧠',
            'RENDER': '🎨',
            'GRT': '📊',
            'NMR': '🔢',
            'CTXC': '🧠',
            'DKA': '📦',
            'AIOZ': '📡',
            'PHB': '🔥',
            'COTI': '💳',
            'RNDR': '🎬',
            'TAO': '🧘',
            'ARKM': '🕵️',
            'WLD': '🌍',
            'AI': '🤖',
            'GPT': '💬',
            
            # Layer 1 & 2
            'NEAR': '🔮',
            'ATOM': '⚛️',
            'ALGO': '🔷',
            'FTM': '👻',
            'ONE': '1️⃣',
            'HBAR': '♦️',
            'EGLD': '⚡',
            'LUNA': '🌙',
            'LUNC': '🌙',
            'USTC': '💵',
            'ROSE': '🌹',
            'KLAY': '🎯',
            'WAVES': '🌊',
            'ICX': '🔷',
            'QTUM': '⚡',
            'ZIL': '💎',
            'ONT': '🔗',
            'IOST': '🌐',
            'TOMO': '⚡',
            'WAN': '🌐',
            'NULS': '🔗',
            'STEEM': '📝',
            'LSK': '🔗',
            'ARK': '🚢',
            'STRAT': '💎',
            'NAS': '🌌',
            'PIVX': '🔒',
            'SYS': '⚙️',
            'DGB': '💎',
            'RVN': '🐦',
            'MONA': '🐱',
            'VTC': '💚',
            'GRS': '🔷',
            'PART': '🔒',
            'NAV': '🧭',
            'XZC': '🔒',
            'DASH': '💨',
            'ZEC': '🛡️',
            'XMR': '🔒',
            'DCR': '🗳️',
            'SC': '📁',
            'ZEN': '🧘',
            'OP': '🔴',
            'ARB': '🔵',
            'METIS': '🌟',
            'BOBA': '🧋',
            'CELR': '⚡',
            'SKALE': '⚡',
            
            # Exchange Tokens
            'CRO': '💎',
            'FTT': '🔥',
            'KCS': '💎',
            'HT': '🔥',
            'OKB': '⭕',
            'LEO': '🦁',
            'BGB': '💎',
            'GT': '🚪',
            'MX': '❌',
            
            # Privacy Coins
            'FIRO': '🔒',
            'BEAM': '💡',
            'GRIN': '😁',
            'ARRR': '🏴‍☠️',
            'DERO': '🔒',
            'HAVEN': '🏠',
            'OXEN': '🐂',
            
            # Storage & Infrastructure
            'AR': '🗄️',
            'STORJ': '☁️',
            'SIA': '📁',
            'BTT': '📁',
            'HOT': '🔥',
            'ANKR': '⚓',
            'NKN': '🌐',
            'POKT': '📱',
            'FLUX': '⚡',
            
            # Oracle & Data
            'BAND': '📡',
            'API3': '🔌',
            'TRB': '📊',
            'DIA': '💎',
            'NEST': '🪺',
            'DOS': '💻',
            
            # Social & Content
            'CHZ': '⚽',
            'TFUEL': '📺',
            'LPT': '📹',
            'AUDIO': '🎵',
            'RALLY': '📢',
            'MASK': '🎭',
            
            # Enterprise & Business
            'WTC': '📦',
            'AMB': '🌿',
            'TRAC': '🔍',
            'TEL': '📞',
            'DENT': '📱',
            'KEY': '🔑',
            'DATA': '📊',
            'DOCK': '⚓',
            'CENNZ': '🏢',
            
            # Additional Popular Coins
            'HIVE': '🐝',
            'NEO': '🔮',
            'GAS': '⛽',
            'IOTA': '🔗',
            'XTZ': '🏛️',
            'KSM': '🐦',
            'BAT': '🦇',
            'ZRX': '0️⃣',
            'REP': '📊',
            'KNC': '🔗',
            'LRC': '🔄',
            'RLC': '⚡',
            'GNT': '🐐',
            'ANT': '🐜',
            'MLN': '🍈',
            'SALT': '🧂',
            'BNT': '🏦',
            'ICN': '📊',
            'REQ': '📋',
            'MOD': '📦',
            'EVX': '💱',
            'CTR': '🎯',
            'GO': '🚀',
            'POWR': '⚡',
            'ELF': '🧝',
            'AION': '⚛️',
            'NEBL': '🌌',
            'BRD': '🍞',
            'EDO': '💎',
            'WINGS': '🪶',
            'LUN': '🌙',
            'TRIG': '🔫',
            'APPC': '📱',
            'VIBES': '🎵',
            'RCN': '💳',
            'IOS': '📱',
            'CHAT': '💬',
            'NANO': '⚡',
            'VIA': '🛣️',
            'BLK': '⚫',
            'POT': '🌿',
            'CLOAK': '🥷',
            'NEOS': '🔮',
            'DGD': '💎',
            'GNO': '🧠',
            'MCO': '💳',
            'YOYO': '🪀',
            'ICO': '💰',
            'ELEC': '⚡',
            'ACAT': '🐱',
            'BRDS': '🐦',
            'VIBE': '🎵',
            'LLT': '🔗',
            'BNTY': '💰',
            'TVK': '📺',
            'FOR': '🏦',
            'HARD': '💎',
            'DODO': '🦤',
            'TKO': '🥊',
            'PROM': '🎭',
            'PROS': '📈',
            'BETH': '⟠',
            'SKL': '⚡',
            'SUSD': '💵',
            'COVER': '🛡️',
            'GLMR': '🌙',
            'BAKE': '🍰',
            'BURGER': '🍔',
            'ATA': '🤖',
            'CHESS': '♟️',
            'TITAN': '⚡',
            'ASR': '⚽',
            'PSG': '⚽',
            'JUV': '⚽',
            'BAR': '⚽',
            'ATM': '⚽',
            'SANTOS': '⚽',
            'CITY': '⚽',
            'OG': '🎮'
        }
        
        return emoji_mapping.get(base_asset.upper(), '💰')
    
    def get_top_volume_pairs(self, limit: int = 100) -> List[str]:
        """
        Get top trading pairs by 24h volume
        """
        try:
            response = requests.get(f"{self.base_url}/ticker/24hr")
            response.raise_for_status()
            data = response.json()
            
            # Filter USDT pairs and sort by volume
            usdt_pairs = [
                ticker for ticker in data 
                if ticker['symbol'].endswith('USDT')
            ]
            
            # Sort by quote volume (USDT volume)
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Return top symbols
            return [ticker['symbol'] for ticker in usdt_pairs[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error fetching top volume pairs: {e}")
            return []
    
    def get_fallback_pairs(self) -> Dict[str, Dict]:
        """
        Fallback hardcoded pairs if API fails
        """
        return {
            'BTCUSDT': {'name': 'Bitcoin', 'emoji': '₿', 'category': 'Major'},
            'ETHUSDT': {'name': 'Ethereum', 'emoji': '⟠', 'category': 'Major'},
            'BNBUSDT': {'name': 'BNB', 'emoji': '🟡', 'category': 'Major'},
            'ADAUSDT': {'name': 'Cardano', 'emoji': '🔵', 'category': 'Major'},
            'SOLUSDT': {'name': 'Solana', 'emoji': '🌞', 'category': 'Major'},
            'DOGEUSDT': {'name': 'Dogecoin', 'emoji': '🐕', 'category': 'Meme'},
            'SHIBUSDT': {'name': 'Shiba Inu', 'emoji': '🐕‍🦺', 'category': 'Meme'},
        }
    
    def filter_by_category(self, pairs: Dict[str, Dict], category: str) -> Dict[str, Dict]:
        """
        Filter pairs by category
        """
        return {
            symbol: info for symbol, info in pairs.items()
            if info['category'] == category
        }
    
    def get_training_symbols(self, pairs: Dict[str, Dict]) -> List[str]:
        """
        Dynamically select diverse training symbols
        """
        training_symbols = []
        
        # Get top symbols from each category
        categories = ['Major', 'DeFi', 'Meme', 'Gaming', 'AI', 'Layer1']
        
        for category in categories:
            category_pairs = self.filter_by_category(pairs, category)
            # Add top 2-3 symbols from each category
            symbols = list(category_pairs.keys())[:3]
            training_symbols.extend(symbols)
        
        return training_symbols[:15]  # Limit to 15 for training efficiency
    
    def get_comprehensive_market_coverage(self, min_volume_usdt: float = 100000) -> Dict[str, Dict]:
        """
        Get comprehensive market coverage with ALL available USDT pairs
        Filters by minimum volume to exclude very low-volume pairs
        """
        try:
            # Get all USDT pairs
            all_pairs = self.get_all_usdt_pairs()
            
            # Get 24hr ticker data for volume filtering
            response = requests.get(f"{self.base_url}/ticker/24hr")
            response.raise_for_status()
            ticker_data = response.json()
            
            # Create volume lookup
            volume_lookup = {}
            for ticker in ticker_data:
                if ticker['symbol'].endswith('USDT'):
                    volume_lookup[ticker['symbol']] = float(ticker['quoteVolume'])
            
            # Filter by volume and add market data
            filtered_pairs = {}
            for symbol, info in all_pairs.items():
                volume = volume_lookup.get(symbol, 0)
                if volume >= min_volume_usdt:
                    info['volume_24h'] = volume
                    filtered_pairs[symbol] = info
            
            self.logger.info(f"✅ Comprehensive coverage: {len(filtered_pairs)} pairs (min volume: ${min_volume_usdt:,.0f})")
            return filtered_pairs
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive coverage: {e}")
            return self.get_all_usdt_pairs()

def main():
    """Test the dynamic fetcher with comprehensive statistics"""
    fetcher = DynamicCryptoFetcher()
    
    print("🚀 COMPREHENSIVE CRYPTOCURRENCY COVERAGE TEST")
    print("=" * 60)
    
    # Get all USDT pairs
    pairs = fetcher.get_all_usdt_pairs()
    print(f"📊 Total USDT pairs found: {len(pairs)}")
    
    # Show breakdown by category
    categories = {}
    for symbol, info in pairs.items():
        category = info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(symbol)
    
    print(f"\n📈 Breakdown by category:")
    total_categorized = 0
    for category, symbols in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   {category}: {len(symbols)} pairs")
        total_categorized += len(symbols)
        
        # Show some examples for each category
        if len(symbols) > 0:
            examples = symbols[:5]  # Show first 5 as examples
            example_names = [pairs[s]['name'] for s in examples]
            print(f"      Examples: {', '.join(example_names)}")
    
    print(f"\n📊 Total categorized: {total_categorized}")
    
    # Get comprehensive market coverage with different volume filters
    print(f"\n💰 Volume-based filtering:")
    for min_volume in [10000, 50000, 100000, 500000]:
        filtered = fetcher.get_comprehensive_market_coverage(min_volume_usdt=min_volume)
        print(f"   Min ${min_volume:,} volume: {len(filtered)} pairs")
    
    # Get top volume pairs
    top_pairs = fetcher.get_top_volume_pairs(50)
    print(f"\n🔥 Top 50 by volume:")
    for i, symbol in enumerate(top_pairs[:20], 1):
        if symbol in pairs:
            name = pairs[symbol]['name']
            category = pairs[symbol]['category']
            print(f"   {i:2d}. {symbol:12} - {name:20} ({category})")
    
    # Show some interesting statistics
    print(f"\n🎯 Interesting Statistics:")
    
    # Count by first letter
    first_letters = {}
    for symbol in pairs.keys():
        first_letter = symbol[0]
        first_letters[first_letter] = first_letters.get(first_letter, 0) + 1
    
    print(f"   Most common starting letters:")
    for letter, count in sorted(first_letters.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {letter}: {count} coins")
    
    # Show category diversity
    print(f"   Category diversity: {len(categories)} different categories")
    print(f"   Average coins per category: {len(pairs) / len(categories):.1f}")
    
    # Get training symbols
    training_symbols = fetcher.get_training_symbols(pairs)
    print(f"\n🧠 Suggested training symbols ({len(training_symbols)}):")
    for symbol in training_symbols:
        if symbol in pairs:
            name = pairs[symbol]['name']
            category = pairs[symbol]['category']
            print(f"   {symbol:12} - {name:20} ({category})")
    
    print(f"\n✅ COMPREHENSIVE COVERAGE COMPLETE!")
    print(f"🎉 Your system now has access to {len(pairs)} cryptocurrencies!")
    print(f"🚀 No more missing out on new or smaller coins!")

if __name__ == "__main__":
    main() 