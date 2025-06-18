import hashlib
import time
import json
import ecdsa
import base64
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import random
import threading
import socket
import uuid
import logging
from queue import Queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PythonCoin")

# --------------------------------
# Core Cryptographic Primitives
# --------------------------------

class CryptoUtils:
    """Utility class for cryptographic operations in PythonCoin"""
    
    @staticmethod
    def generate_keypair():
        """Generate a new DSA key pair for a wallet"""
        # Generate a new private key using the SECP256k1 curve (same as Bitcoin)
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key()
        
        # Encode keys for storage
        private_key_encoded = private_key.to_string().hex()
        public_key_encoded = public_key.to_string().hex()
        
        # Generate address from public key
        address = CryptoUtils.pubkey_to_address(public_key_encoded)
        
        return {
            "private_key": private_key_encoded,
            "public_key": public_key_encoded,
            "address": address
        }
    
    @staticmethod
    def pubkey_to_address(public_key_hex):
        """Convert a public key to a PythonCoin address"""
        # Hash the public key with SHA-256 and then RIPEMD-160
        sha256_hash = hashlib.sha256(bytes.fromhex(public_key_hex)).digest()
        ripemd160_hash = hashlib.new('ripemd160')
        ripemd160_hash.update(sha256_hash)
        
        # Add version byte (0x00 for main network)
        versioned_hash = b'\x00' + ripemd160_hash.digest()
        
        # Calculate checksum (first 4 bytes of double SHA-256)
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
        
        # Concatenate versioned hash and checksum
        binary_address = versioned_hash + checksum
        
        # Convert to base58
        return CryptoUtils.base58_encode(binary_address)
    
    @staticmethod
    def base58_encode(data):
        """Encode data in Base58 format (similar to Bitcoin addresses)"""
        # Base58 character set (Bitcoin-specific)
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        
        # Convert binary data to integer
        n = int.from_bytes(data, byteorder='big')
        
        # Encode to Base58
        encoded = ''
        while n > 0:
            n, remainder = divmod(n, 58)
            encoded = alphabet[remainder] + encoded
        
        # Add leading zeros (one '1' for each leading zero byte)
        for byte in data:
            if byte == 0:
                encoded = '1' + encoded
            else:
                break
        
        return encoded
    
    @staticmethod
    def sign_data(private_key_hex, data):
        """Sign data with a private key"""
        # Recreate private key from hex
        private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
        
        # Create a hash of the data to sign
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()
        
        # Sign the hash
        signature = private_key.sign(data_hash)
        
        return signature.hex()
    
    @staticmethod
    def verify_signature(public_key_hex, data, signature_hex):
        """Verify a signature against the original data and public key"""
        try:
            # Recreate public key from hex
            public_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=ecdsa.SECP256k1)
            
            # Create a hash of the data
            data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()
            
            # Verify the signature
            return public_key.verify(bytes.fromhex(signature_hex), data_hash)
        except:
            return False
    
    @staticmethod
    def compute_merkle_root(transaction_hashes):
        """Compute the Merkle root of transaction hashes"""
        if len(transaction_hashes) == 0:
            return hashlib.sha256("".encode()).hexdigest()
        
        if len(transaction_hashes) == 1:
            return transaction_hashes[0]
        
        # If odd number of transactions, duplicate the last one
        if len(transaction_hashes) % 2 != 0:
            transaction_hashes.append(transaction_hashes[-1])
        
        # Pair up transactions and hash them together
        new_level = []
        for i in range(0, len(transaction_hashes), 2):
            combined = transaction_hashes[i] + transaction_hashes[i+1]
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            new_level.append(new_hash)
        
        # Recursively continue until we get a single hash (the Merkle root)
        return CryptoUtils.compute_merkle_root(new_level)

# --------------------------------
# Transaction Classes
# --------------------------------

@dataclass
class TransactionInput:
    """Represents an input to a transaction (spending a previous output)"""
    tx_id: str  # ID of the transaction containing the output to spend
    output_index: int  # Index of the output in the referenced transaction
    signature: str = ""  # Signature proving ownership (filled in later)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class TransactionOutput:
    """Represents an output of a transaction (coins sent to an address)"""
    address: str  # Recipient's address
    amount: float  # Amount of coins
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Transaction:
    """Represents a PythonCoin transaction"""
    sender: str  # Sender's public key
    inputs: List[TransactionInput]  # List of inputs (previous outputs being spent)
    outputs: List[TransactionOutput]  # List of outputs (coins being sent)
    timestamp: float = field(default_factory=time.time)  # Transaction timestamp
    tx_id: str = ""  # Transaction ID (hash)
    signature: str = ""  # Transaction signature
    tx_type: str = "standard"  # Transaction type (standard, data, smart_contract, etc.)
    data: Dict[str, Any] = field(default_factory=dict)  # Extra data for non-standard transactions
    
    def __post_init__(self):
        """Calculate transaction ID after initialization if not provided"""
        if not self.tx_id:
            self.calculate_tx_id()
    
    def calculate_tx_id(self):
        """Calculate the transaction ID (hash of the transaction)"""
        tx_dict = {
            "sender": self.sender,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs],
            "timestamp": self.timestamp,
            "tx_type": self.tx_type,
            "data": self.data
        }
        tx_string = json.dumps(tx_dict, sort_keys=True)
        self.tx_id = hashlib.sha256(tx_string.encode()).hexdigest()
        return self.tx_id
    
    def sign(self, private_key):
        """Sign the transaction with the sender's private key"""
        # Calculate transaction ID if not already done
        if not self.tx_id:
            self.calculate_tx_id()
        
        # Create a simplified representation of the transaction to sign
        tx_for_signing = {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }
        
        # Sign the transaction
        self.signature = CryptoUtils.sign_data(private_key, tx_for_signing)
        
        # Sign each input separately (simplified version)
        for tx_input in self.inputs:
            tx_input.signature = self.signature
        
        return self.signature
    
    def verify(self):
        """Verify the transaction signature"""
        # Skip verification for coinbase transactions
        if len(self.inputs) == 0 and self.tx_type == "coinbase":
            return True
        
        # Skip verification for genesis transactions
        if self.tx_type == "genesis":
            return True
        
        # Create a simplified representation of the transaction to verify
        tx_for_verification = {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }
        
        # Verify the transaction signature
        return CryptoUtils.verify_signature(self.sender, tx_for_verification, self.signature)
    
    def to_dict(self):
        """Convert transaction to a dictionary"""
        return {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs],
            "timestamp": self.timestamp,
            "signature": self.signature,
            "tx_type": self.tx_type,
            "data": self.data
        }

@dataclass
class DataTransaction(Transaction):
    """Special transaction type for storing data on the blockchain"""
    
    def __init__(self, sender, data_content, private_key=None):
        super().__init__(
            sender=sender,
            inputs=[],  # No inputs for data transactions
            outputs=[],  # No outputs for data transactions
            tx_type="data",
            data={"content": data_content}
        )
        
        # Pre-calculate the TX ID
        self.calculate_tx_id()
        
        # Sign the transaction if private key is provided
        if private_key:
            self.sign(private_key)

@dataclass
class DSAVerificationTransaction(Transaction):
    """Special transaction for DSA verification records"""
    
    def __init__(self, sender, document_hash, verification_result, verifier_notes="", private_key=None):
        super().__init__(
            sender=sender,
            inputs=[],  # Optional: can require a small fee
            outputs=[],  # No outputs typically needed
            tx_type="dsa_verification",
            data={
                "document_hash": document_hash,
                "verification_result": verification_result,
                "verifier_notes": verifier_notes,
                "verification_timestamp": time.time()
            }
        )
        
        # Pre-calculate the TX ID
        self.calculate_tx_id()
        
        # Sign the transaction if private key is provided
        if private_key:
            self.sign(private_key)

# --------------------------------
# Block Classes
# --------------------------------

@dataclass
class Block:
    """Represents a block in the PythonCoin blockchain"""
    index: int  # Block height
    timestamp: float  # Block creation time
    transactions: List[Transaction]  # List of transactions in the block
    previous_hash: str  # Hash of the previous block
    nonce: int = 0  # Nonce for proof of work
    difficulty: int = 4  # Mining difficulty (number of leading zeros required)
    merkle_root: str = ""  # Merkle root of transactions
    hash: str = ""  # Block hash
    
    def __post_init__(self):
        """Calculate merkle root and block hash after initialization"""
        self.calculate_merkle_root()
        if not self.hash:
            self.calculate_hash()
    
    def calculate_merkle_root(self):
        """Calculate the Merkle root of the transactions"""
        tx_hashes = [tx.tx_id for tx in self.transactions]
        self.merkle_root = CryptoUtils.compute_merkle_root(tx_hashes)
        return self.merkle_root
    
    def calculate_hash(self):
        """Calculate the hash of the block"""
        # Include key block data in the hash calculation
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty
        }
        
        block_string = json.dumps(block_data, sort_keys=True)
        self.hash = hashlib.sha256(block_string.encode()).hexdigest()
        return self.hash
    
    def mine_block(self, mining_reward_address):
        """Mine the block by finding a valid nonce (proof of work)"""
        # Don't add coinbase for genesis block (it already has distribution transactions)
        if self.index > 0:
            # Add coinbase transaction (mining reward) as the first transaction
            coinbase_tx = Transaction(
                sender="coinbase",
                inputs=[],
                outputs=[TransactionOutput(address=mining_reward_address, amount=50.0)],  # 50 PythonCoins reward
                tx_type="coinbase"
            )
            coinbase_tx.calculate_tx_id()
            
            # Insert coinbase as the first transaction
            self.transactions.insert(0, coinbase_tx)
        
        # Recalculate merkle root with the coinbase transaction (or original transactions for genesis)
        self.calculate_merkle_root()
        
        # Mine the block (find a valid hash)
        target = "0" * self.difficulty
        
        logger.info(f"Starting mining for block {self.index}...")
        start_time = time.time()
        
        while True:
            self.calculate_hash()
            if self.hash.startswith(target):
                # Found a valid hash
                end_time = time.time()
                mining_time = end_time - start_time
                logger.info(f"Block {self.index} mined in {mining_time:.2f} seconds with nonce {self.nonce}")
                return True
            
            self.nonce += 1
            
            # Log progress every 100,000 attempts
            if self.nonce % 100000 == 0:
                logger.info(f"Mining block {self.index}, tried {self.nonce} nonces...")
    
    def is_valid(self):
        """Verify that the block is valid"""
        # Check that the hash matches the block data
        calculated_hash = self.calculate_hash()
        if calculated_hash != self.hash:
            return False
        
        # Check that the hash satisfies the proof of work
        if not self.hash.startswith("0" * self.difficulty):
            return False
        
        # Verify each transaction
        for tx in self.transactions:
            if not tx.verify() and tx.tx_type not in ["coinbase", "genesis"]:
                return False
        
        # Check the merkle root
        calculated_merkle_root = self.calculate_merkle_root()
        if calculated_merkle_root != self.merkle_root:
            return False
        
        return True
    
    def to_dict(self):
        """Convert block to a dictionary"""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.hash,
            "transactions": [tx.to_dict() for tx in self.transactions]
        }

# --------------------------------
# Blockchain Class
# --------------------------------

class Blockchain:
    """Main blockchain implementation for PythonCoin"""
    
    def __init__(self, genesis_addresses=None):
        """Initialize a new blockchain"""
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()  # Set of peer nodes in the network
        self.utxo = {}  # Unspent Transaction Outputs
        self.genesis_addresses = genesis_addresses or []
        self.genesis_complete = False
        
        # Create the genesis block if we have addresses to distribute to
        if self.genesis_addresses:
            self.create_genesis_block()
    
    def set_genesis_addresses(self, addresses):
        """Set genesis addresses and create genesis block if not already done"""
        if not self.genesis_complete and not self.chain:
            self.genesis_addresses = addresses
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the genesis block with coin distribution to all connected clients"""
        if self.genesis_complete or not self.genesis_addresses:
            return
        
        logger.info(f"Creating genesis block with distribution to {len(self.genesis_addresses)} addresses")
        
        # Total initial supply
        total_supply = 1000000.0
        
        # Calculate distribution amount per address
        if len(self.genesis_addresses) > 0:
            amount_per_address = total_supply / len(self.genesis_addresses)
        else:
            # Fallback - create a single genesis transaction for later distribution
            genesis_keys = CryptoUtils.generate_keypair()
            self.genesis_addresses = [genesis_keys["address"]]
            amount_per_address = total_supply
        
        # Create distribution transactions
        genesis_transactions = []
        
        for i, address in enumerate(self.genesis_addresses):
            genesis_tx = Transaction(
                sender="genesis",
                inputs=[],
                outputs=[TransactionOutput(address=address, amount=amount_per_address)],
                tx_type="genesis",
                data={"distribution_index": i, "total_recipients": len(self.genesis_addresses)}
            )
            genesis_tx.calculate_tx_id()
            genesis_transactions.append(genesis_tx)
        
        # Create the genesis block
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=genesis_transactions,
            previous_hash="0" * 64,
            difficulty=2  # Start with a low difficulty for genesis
        )
        
        # Mine the genesis block
        target = "0" * genesis_block.difficulty
        logger.info("Mining genesis block...")
        
        while True:
            genesis_block.calculate_hash()
            if genesis_block.hash.startswith(target):
                break
            genesis_block.nonce += 1
            
            if genesis_block.nonce % 50000 == 0:
                logger.info(f"Genesis mining progress: {genesis_block.nonce} nonces tried...")
        
        # Add genesis block to the chain
        self.chain.append(genesis_block)
        
        # Update UTXO set
        self.update_utxo(genesis_block)
        
        self.genesis_complete = True
        logger.info(f"Genesis block created with {len(genesis_transactions)} distribution transactions")
        logger.info(f"Each address received: {amount_per_address:.8f} PYC")
    
    def create_distribution_transactions(self, new_peer_addresses):
        """Create transactions to distribute coins to newly connected peers"""
        if not self.genesis_complete:
            logger.warning("Cannot create distribution transactions before genesis block")
            return []
        
        # Find addresses with the most coins for redistribution
        address_balances = {}
        for address in self.genesis_addresses:
            balance = self.get_balance(address)
            if balance > 1000:  # Only redistribute from addresses with substantial balance
                address_balances[address] = balance
        
        if not address_balances:
            logger.warning("No addresses available for redistribution")
            return []
        
        # Calculate distribution amount (e.g., 1000 PYC per new peer)
        distribution_amount = 1000.0
        redistribution_txs = []
        
        # Find the richest address for redistribution
        richest_address = max(address_balances.keys(), key=lambda addr: address_balances[addr])
        richest_balance = address_balances[richest_address]
        
        # Check if we have enough for distribution
        total_needed = distribution_amount * len(new_peer_addresses)
        if richest_balance >= total_needed:
            # Create redistribution transactions
            for new_address in new_peer_addresses:
                # This would need to be signed by the holder of the richest address
                # For now, we'll create the transaction structure
                logger.info(f"Would distribute {distribution_amount} PYC to {new_address}")
                # In a real implementation, this would require the private key of the distributing address
        
        return redistribution_txs
    
    def add_transaction(self, transaction):
        """Add a transaction to the pending transactions pool"""
        # Verify transaction
        if not transaction.verify() and transaction.tx_type not in ["coinbase", "genesis"]:
            logger.warning(f"Invalid transaction: {transaction.tx_id}")
            return False
        
        # Check if inputs are available (UTXO)
        if not self.validate_transaction_inputs(transaction) and transaction.tx_type not in ["coinbase", "genesis", "data", "dsa_verification"]:
            logger.warning(f"Transaction inputs not valid: {transaction.tx_id}")
            return False
        
        # Add transaction to pending pool
        self.pending_transactions.append(transaction)
        logger.info(f"Transaction {transaction.tx_id} added to pending pool")
        return True
    
    def validate_transaction_inputs(self, transaction):
        """Validate that the transaction inputs are available in the UTXO set"""
        # Skip validation for special transaction types
        if transaction.tx_type in ["coinbase", "genesis", "data", "dsa_verification"]:
            return True
        
        input_sum = 0.0
        output_sum = 0.0
        
        # Check each input
        for tx_input in transaction.inputs:
            utxo_key = f"{tx_input.tx_id}:{tx_input.output_index}"
            
            # Check if the UTXO exists
            if utxo_key not in self.utxo:
                logger.warning(f"UTXO not found: {utxo_key}")
                return False
            
            # Get the public key from the sender and convert to address
            sender_address = CryptoUtils.pubkey_to_address(transaction.sender)
            
            # Check that the sender owns the UTXO
            utxo_data = self.utxo[utxo_key]
            if sender_address != utxo_data["recipient"]:
                logger.warning(f"Sender {sender_address} does not own the UTXO: {utxo_key} (owned by {utxo_data['recipient']})")
                return False
            
            # Add input amount
            input_sum += utxo_data["amount"]
        
        # Calculate output sum
        for tx_output in transaction.outputs:
            output_sum += tx_output.amount
        
        # Check that inputs >= outputs (allowing for small transaction fees)
        if input_sum < output_sum:
            logger.warning(f"Input sum ({input_sum}) less than output sum ({output_sum})")
            return False
        
        return True
    
    def mine_pending_transactions(self, miner_address):
        """Mine pending transactions into a new block"""
        # Ensure genesis block exists
        if not self.chain:
            logger.warning("No genesis block exists")
            return False
        
        # Check if there are any pending transactions or create a dummy one
        if len(self.pending_transactions) == 0:
            # Create a dummy data transaction to mine
            dummy_tx = DataTransaction(
                sender=miner_address,
                data_content=f"Mining block at {time.time()}"
            )
            self.pending_transactions.append(dummy_tx)
            logger.info("Created dummy transaction for mining")
        
        # Get the last block
        last_block = self.chain[-1]
        
        # Create a new block
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.pending_transactions[:],  # Create a copy
            previous_hash=last_block.hash,
            difficulty=self.get_difficulty()  # Adjust difficulty dynamically
        )
        
        # Mine the block
        if new_block.mine_block(miner_address):
            # Add the block to the chain
            self.chain.append(new_block)
            
            # Update UTXO set
            self.update_utxo(new_block)
            
            # Clear pending transactions
            self.pending_transactions = []
            
            logger.info(f"Block {new_block.index} added to the chain")
            return new_block
        
        return False
    
    def update_utxo(self, block):
        """Update the UTXO set with transactions from a block"""
        for tx in block.transactions:
            # Remove spent outputs from UTXO
            for tx_input in tx.inputs:
                utxo_key = f"{tx_input.tx_id}:{tx_input.output_index}"
                if utxo_key in self.utxo:
                    del self.utxo[utxo_key]
            
            # Add new outputs to UTXO
            for i, tx_output in enumerate(tx.outputs):
                utxo_key = f"{tx.tx_id}:{i}"
                
                # For genesis and coinbase transactions, the sender is not a real public key
                if tx.tx_type in ["genesis", "coinbase"]:
                    owner_pubkey = "system"
                else:
                    owner_pubkey = tx.sender
                
                self.utxo[utxo_key] = {
                    "owner": owner_pubkey,
                    "recipient": tx_output.address,
                    "amount": tx_output.amount,
                    "tx_id": tx.tx_id,
                    "output_index": i
                }
    
    def get_difficulty(self):
        """Dynamically calculate the mining difficulty"""
        # Start with the current difficulty
        current_difficulty = self.chain[-1].difficulty if self.chain else 2
        
        # For the first few blocks, keep difficulty low
        if len(self.chain) < 10:
            return max(1, current_difficulty - 1)
        
        # Adjust difficulty every 10 blocks
        if len(self.chain) % 10 != 0:
            return current_difficulty
        
        # Calculate the average block time for the last 10 blocks
        last_10_blocks = self.chain[-10:]
        avg_block_time = 0
        
        for i in range(1, len(last_10_blocks)):
            block_time = last_10_blocks[i].timestamp - last_10_blocks[i-1].timestamp
            avg_block_time += block_time
        
        avg_block_time /= 9  # 9 intervals for 10 blocks
        
        # Target block time is 60 seconds
        target_time = 60
        
        # Adjust difficulty based on average block time
        if avg_block_time < target_time / 2:
            # Blocks are being mined too quickly, increase difficulty
            return min(6, current_difficulty + 1)  # Cap at difficulty 6
        elif avg_block_time > target_time * 2:
            # Blocks are being mined too slowly, decrease difficulty
            return max(1, current_difficulty - 1)  # Minimum difficulty 1
        
        return current_difficulty
    
    def is_chain_valid(self):
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if the block is valid
            if not current_block.is_valid():
                return False
            
            # Check if the previous hash matches
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_balance(self, address):
        """Get the balance for an address by summing all UTXOs for that address"""
        balance = 0.0
        
        for utxo_key, utxo_data in self.utxo.items():
            if utxo_data["recipient"] == address:
                balance += utxo_data["amount"]
        
        return balance
    
    def get_address_transactions(self, address):
        """Get all transactions involving a specific address"""
        address_txs = []
        
        for block in self.chain:
            for tx in block.transactions:
                # Convert sender public key to address for comparison
                if tx.tx_type not in ["genesis", "coinbase"]:
                    sender_addr = CryptoUtils.pubkey_to_address(tx.sender)
                    if sender_addr == address:
                        address_txs.append(tx)
                        continue
                
                # Check if the address is a recipient
                for output in tx.outputs:
                    if output.address == address:
                        address_txs.append(tx)
                        break
        
        return address_txs
    
    def get_transaction(self, tx_id):
        """Find a transaction by its ID"""
        for block in self.chain:
            for tx in block.transactions:
                if tx.tx_id == tx_id:
                    return tx
        
        # Check pending transactions
        for tx in self.pending_transactions:
            if tx.tx_id == tx_id:
                return tx
        
        return None
    
    def create_transaction(self, sender_private_key, sender_public_key, recipient_address, amount):
        """Create a new transaction"""
        # Get sender's address
        sender_address = CryptoUtils.pubkey_to_address(sender_public_key)
        
        # Find UTXOs for the sender
        sender_utxos = []
        for utxo_key, utxo_data in self.utxo.items():
            if utxo_data["recipient"] == sender_address:
                tx_id, output_index = utxo_key.split(":")
                sender_utxos.append({
                    "tx_id": tx_id,
                    "output_index": int(output_index),
                    "amount": utxo_data["amount"]
                })
        
        # Check if sender has enough funds
        total_available = sum(utxo["amount"] for utxo in sender_utxos)
        if total_available < amount:
            logger.warning(f"Insufficient funds: {total_available} < {amount}")
            return None
        
        # Create inputs (consume UTXOs)
        inputs = []
        total_input_amount = 0
        
        for utxo in sender_utxos:
            if total_input_amount >= amount:
                break
            
            inputs.append(TransactionInput(
                tx_id=utxo["tx_id"],
                output_index=utxo["output_index"]
            ))
            
            total_input_amount += utxo["amount"]
        
        # Create outputs
        outputs = [
            # Output to recipient
            TransactionOutput(address=recipient_address, amount=amount)
        ]
        
        # Add change output if necessary
        if total_input_amount > amount:
            change_amount = total_input_amount - amount
            outputs.append(
                TransactionOutput(address=sender_address, amount=change_amount)
            )
        
        # Create transaction
        tx = Transaction(
            sender=sender_public_key,
            inputs=inputs,
            outputs=outputs
        )
        
        # Sign the transaction
        tx.sign(sender_private_key)
        
        return tx
    
    def to_dict(self):
        """Convert blockchain to a dictionary"""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "utxo_count": len(self.utxo),
            "genesis_complete": self.genesis_complete
        }

# --------------------------------
# Wallet Class
# --------------------------------

class Wallet:
    """PythonCoin wallet implementation"""
    
    def __init__(self, blockchain, private_key=None, public_key=None):
        """Initialize a wallet"""
        self.blockchain = blockchain
        
        if private_key and public_key:
            # Use existing keys
            self.private_key = private_key
            self.public_key = public_key
            self.address = CryptoUtils.pubkey_to_address(public_key)
        else:
            # Generate new keys
            keys = CryptoUtils.generate_keypair()
            self.private_key = keys["private_key"]
            self.public_key = keys["public_key"]
            self.address = keys["address"]
        
        logger.info(f"Wallet initialized with address: {self.address}")
    
    def get_balance(self):
        """Get the current balance for this wallet"""
        return self.blockchain.get_balance(self.address)
    
    def send(self, recipient_address, amount):
        """Send coins to another address"""
        # Create a new transaction
        tx = self.blockchain.create_transaction(
            sender_private_key=self.private_key,
            sender_public_key=self.public_key,
            recipient_address=recipient_address,
            amount=amount
        )
        
        if tx:
            # Add the transaction to the blockchain
            if self.blockchain.add_transaction(tx):
                logger.info(f"Transaction created: {tx.tx_id}")
                return tx
        
        return None
    
    def create_data_transaction(self, data_content):
        """Create a transaction to store data on the blockchain"""
        # Create a data transaction
        tx = DataTransaction(
            sender=self.public_key,
            data_content=data_content,
            private_key=self.private_key
        )
        
        # Add the transaction to the blockchain
        if self.blockchain.add_transaction(tx):
            logger.info(f"Data transaction created: {tx.tx_id}")
            return tx
        
        return None
    
    def create_dsa_verification(self, document_hash, verification_result, notes=""):
        """Create a DSA verification transaction"""
        # Create a DSA verification transaction
        tx = DSAVerificationTransaction(
            sender=self.public_key,
            document_hash=document_hash,
            verification_result=verification_result,
            verifier_notes=notes,
            private_key=self.private_key
        )
        
        # Add the transaction to the blockchain
        if self.blockchain.add_transaction(tx):
            logger.info(f"DSA verification transaction created: {tx.tx_id}")
            return tx
        
        return None
    
    def get_transaction_history(self):
        """Get the transaction history for this wallet"""
        return self.blockchain.get_address_transactions(self.address)

# --------------------------------
# Node Network Classes
# --------------------------------

class Node:
    """P2P node implementation for PythonCoin network"""
    
    def __init__(self, host="0.0.0.0", port=5000):
        """Initialize a new node"""
        self.host = host
        self.port = port
        self.blockchain = None  # Will be set by the main application
        self.peers = set()
        self.message_queue = Queue()
        
        # Generate a node ID
        self.node_id = str(uuid.uuid4())
        
        # Initialize wallet (will be set by main application)
        self.wallet = None
        
        # Create server socket
        self.server_socket = None
        self.running = False
        
        logger.info(f"Node initialized with ID: {self.node_id}")
    
    def start(self):
        """Start the node server"""
        self.running = True
        
        # Start the server thread
        server_thread = threading.Thread(target=self.run_server, daemon=True)
        server_thread.start()
        
        # Start message processing thread
        message_thread = threading.Thread(target=self.process_messages, daemon=True)
        message_thread.start()
        
        logger.info(f"Node started on {self.host}:{self.port}")
    
    def run_server(self):
        """Run the node server to accept connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1.0)
            
            logger.info(f"Node server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Server error: {e}")
        
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket, address):
        """Handle a client connection"""
        try:
            client_socket.settimeout(30)
            
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode())
                    self.message_queue.put((message, client_socket))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {address}")
        
        except Exception as e:
            logger.debug(f"Client {address} disconnected: {e}")
        finally:
            client_socket.close()
    
    def process_messages(self):
        """Process incoming messages"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    message, client_socket = self.message_queue.get(timeout=1)
                    self.handle_message(message, client_socket)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Message processing error: {e}")
    
    def handle_message(self, message, client_socket):
        """Handle a specific message"""
        msg_type = message.get('type')
        
        if msg_type == 'get_blockchain':
            self.send_blockchain(client_socket)
        elif msg_type == 'get_peers':
            self.send_peers(client_socket)
        elif msg_type == 'new_transaction':
            self.handle_new_transaction(message.get('transaction'))
        elif msg_type == 'new_block':
            self.handle_new_block(message.get('block'))
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    def send_blockchain(self, client_socket):
        """Send the blockchain to a client"""
        if self.blockchain:
            response = {
                'type': 'blockchain',
                'data': self.blockchain.to_dict()
            }
            try:
                client_socket.send(json.dumps(response).encode())
            except Exception as e:
                logger.error(f"Failed to send blockchain: {e}")
    
    def send_peers(self, client_socket):
        """Send peer list to a client"""
        response = {
            'type': 'peers',
            'data': list(self.peers)
        }
        try:
            client_socket.send(json.dumps(response).encode())
        except Exception as e:
            logger.error(f"Failed to send peers: {e}")
    
    def handle_new_transaction(self, transaction_data):
        """Handle a new transaction from a peer"""
        if self.blockchain and transaction_data:
            # Reconstruct transaction object
            # This is a simplified version - in practice you'd need more robust serialization
            logger.info(f"Received new transaction from peer")
    
    def handle_new_block(self, block_data):
        """Handle a new block from a peer"""
        if self.blockchain and block_data:
            # Reconstruct block object and validate
            # This is a simplified version - in practice you'd need more robust serialization
            logger.info(f"Received new block from peer")
    
    def stop(self):
        """Stop the node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Node stopped")
