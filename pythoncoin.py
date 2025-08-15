import hashlib
import time
import json
import ecdsa
import base64
import threading
import socket
import uuid
import logging
import sqlite3
import os
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from queue import Queue
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PythonCoin")

# Try to import MySQL connector
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("MySQL connector not available, using SQLite fallback")

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

# --------------------------------
# Enhanced Classes from PyQt5 Implementation
# --------------------------------

class CryptoMiningThread(threading.Thread):
    """Enhanced cryptocurrency mining thread"""
    
    def __init__(self, blockchain, wallet, threads=1):
        super().__init__()
        self.blockchain = blockchain
        self.wallet = wallet
        self.threads = threads
        self.running = False
        self.blocks_mined = 0
        self.start_time = 0
        self.hash_count = 0
        self.daemon = True
        
        # Callbacks for status updates
        self.status_callback = None
        self.hashrate_callback = None
        self.new_block_callback = None
        self.payment_callback = None
    
    def set_callbacks(self, status_cb=None, hashrate_cb=None, block_cb=None, payment_cb=None):
        """Set callback functions for events"""
        self.status_callback = status_cb
        self.hashrate_callback = hashrate_cb
        self.new_block_callback = block_cb
        self.payment_callback = payment_cb
    
    def run(self):
        """Main mining loop"""
        self.running = True
        self._emit_status("⛏️ Mining thread started")
        
        if not self.blockchain or not self.wallet:
            self._emit_status("❌ Error: Missing blockchain or wallet")
            return
        
        self.start_time = time.time()
        
        # Wait for genesis block
        if not self.blockchain.genesis_complete:
            self._emit_status("⏳ Waiting for genesis block...")
            while not self.blockchain.genesis_complete and self.running:
                time.sleep(1)
        
        self._emit_status("⛏️ Starting mining operations...")
        
        while self.running:
            try:
                # Ensure we have transactions to mine
                if len(self.blockchain.pending_transactions) == 0:
                    self._create_dummy_transaction()
                
                # Mine block
                new_block = self.blockchain.mine_pending_transactions(self.wallet.address)
                
                if new_block and self.running:
                    self.blocks_mined += 1
                    self._emit_status(
                        f"🎉 Block mined! Height: {new_block.index}, "
                        f"Hash: {new_block.hash[:16]}..."
                    )
                    
                    if self.new_block_callback:
                        self.new_block_callback(new_block)
                    
                    # Calculate hashrate
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time > 0:
                        hashrate = new_block.nonce / elapsed_time
                        if self.hashrate_callback:
                            self.hashrate_callback(hashrate)
                    
                    self.start_time = time.time()
                    time.sleep(2)  # Brief pause between blocks
                else:
                    self._emit_status("⚠️ Mining failed, retrying...")
                    time.sleep(5)
                    
            except Exception as e:
                self._emit_status(f"❌ Mining error: {str(e)}")
                logger.error(f"Mining error: {str(e)}")
                time.sleep(5)
    
    def _create_dummy_transaction(self):
        """Create a dummy transaction if none exist"""
        try:
            dummy_tx = DataTransaction(
                sender=self.wallet.public_key,
                data_content=f"Mining block at {time.time()}",
                private_key=self.wallet.private_key
            )
            
            if self.blockchain.add_transaction(dummy_tx):
                self._emit_status("📝 Created data transaction for mining")
            else:
                self._emit_status("❌ Failed to add data transaction")
        except Exception as e:
            self._emit_status(f"❌ Error creating transaction: {str(e)}")
    
    def _emit_status(self, message):
        """Emit status update"""
        logger.info(message)
        if self.status_callback:
            self.status_callback(message)
    
    def stop(self):
        """Stop mining"""
        self.running = False
        self._emit_status("🛑 Mining stopped")

class CryptoP2PManager(threading.Thread):
    """Enhanced P2P Manager with cryptocurrency payment processing"""
    
    def __init__(self, client_id: str, port: int, blockchain: Blockchain, wallet: Wallet):
        super().__init__()
        self.client_id = client_id
        self.port = port
        self.blockchain = blockchain
        self.wallet = wallet
        self.peers = {}
        self.peer_sockets = {}
        self.server_socket = None
        self.running = False
        self.pending_clicks = []
        self.genesis_coordination_complete = False
        self.discovery_timeout = 30
        self.daemon = True
        
        # Callbacks
        self.peer_discovered_callback = None
        self.peer_connected_callback = None
        self.peer_disconnected_callback = None
        self.ads_received_callback = None
        self.status_update_callback = None
        self.click_received_callback = None
        self.payment_sent_callback = None
        self.genesis_ready_callback = None
    
    def set_callbacks(self, **callbacks):
        """Set callback functions"""
        for name, callback in callbacks.items():
            setattr(f"{name}_callback", callback)
    
    def run(self):
        """Main P2P manager thread"""
        self.running = True
        self._emit_status("🌐 Starting crypto P2P discovery...")
        
        # Start discovery threads
        threading.Thread(target=self._discovery_server, daemon=True).start()
        threading.Thread(target=self._discovery_broadcast, daemon=True).start()
        threading.Thread(target=self._peer_handler, daemon=True).start()
        threading.Thread(target=self._process_clicks, daemon=True).start()
        threading.Thread(target=self._coordinate_genesis, daemon=True).start()
        
        self._emit_status("✅ Crypto P2P Manager started")
        
        # Keep thread alive
        while self.running:
            time.sleep(1)
    
    def _coordinate_genesis(self):
        """Coordinate genesis block creation"""
        if self.blockchain.genesis_complete:
            logger.info("Genesis block already exists")
            return
        
        logger.info(f"Starting genesis coordination - waiting {self.discovery_timeout}s for peers...")
        start_time = time.time()
        
        while time.time() - start_time < self.discovery_timeout and self.running:
            time.sleep(1)
            connected_peers = [p for p in self.peers.values() 
                             if p.get('status') == 'connected' and p.get('wallet_address')]
            if len(connected_peers) >= 2:
                logger.info(f"Found {len(connected_peers)} peers, proceeding with genesis")
                break
        
        genesis_addresses = [self.wallet.address]
        for peer in self.peers.values():
            if peer.get('status') == 'connected' and peer.get('wallet_address'):
                genesis_addresses.append(peer['wallet_address'])
        
        if len(genesis_addresses) == 1:
            logger.warning("No peers found, creating single-address genesis block")
        else:
            logger.info(f"Creating genesis block with {len(genesis_addresses)} addresses")
        
        self.blockchain.set_genesis_addresses(genesis_addresses)
        self.genesis_coordination_complete = True
        
        if self.genesis_ready_callback:
            self.genesis_ready_callback(genesis_addresses)
        
        self._emit_status(f"Genesis block created with {len(genesis_addresses)} participants")
    
    def _discovery_server(self):
        """UDP discovery server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('', self.port + 1000))
            sock.settimeout(1.0)
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._handle_discovery_message(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"Discovery server error: {e}")
        except Exception as e:
            logger.error(f"Discovery server failed: {e}")
        finally:
            sock.close()
    
    def _discovery_broadcast(self):
        """Broadcast peer announcements"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                message = {
                    'type': 'peer_announce',
                    'peer_id': self.client_id,
                    'port': self.port,
                    'timestamp': datetime.now().isoformat(),
                    'capabilities': ['ad_serving', 'p2p', 'crypto_payments'],
                    'wallet_address': self.wallet.address if self.wallet else "",
                    'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                    'genesis_complete': self.blockchain.genesis_complete if self.blockchain else False
                }
                
                data = json.dumps(message).encode()
                sock.sendto(data, ('255.255.255.255', self.port + 1000))
                time.sleep(10)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                time.sleep(5)
        
        sock.close()
    
    def _handle_discovery_message(self, data: bytes, addr):
        """Handle incoming discovery messages"""
        try:
            message = json.loads(data.decode())
            if message.get('type') == 'peer_announce':
                peer_id = message.get('peer_id')
                if peer_id != self.client_id:
                    self._add_discovered_peer(message, addr[0])
        except Exception as e:
            logger.debug(f"Discovery message error: {e}")
    
    def _add_discovered_peer(self, message: dict, host: str):
        """Add a discovered peer"""
        peer_id = message['peer_id']
        
        if peer_id not in self.peers:
            peer = {
                'peer_id': peer_id,
                'host': host,
                'port': message['port'],
                'status': 'discovered',
                'last_seen': datetime.now().isoformat(),
                'ad_count': 0,
                'capabilities': message.get('capabilities', []),
                'wallet_address': message.get('wallet_address', '')
            }
            
            self.peers[peer_id] = peer
            
            if self.peer_discovered_callback:
                self.peer_discovered_callback(peer_id, host, message['port'])
            
            threading.Thread(target=self._connect_to_peer, args=(peer,), daemon=True).start()
        else:
            self.peers[peer_id]['last_seen'] = datetime.now().isoformat()
            self.peers[peer_id]['wallet_address'] = message.get('wallet_address', '')
    
    def _connect_to_peer(self, peer: dict):
        """Connect to a discovered peer"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((peer['host'], peer['port'] + 2000))
            
            handshake = {
                'type': 'handshake',
                'peer_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'wallet_address': self.wallet.address if self.wallet else "",
                'capabilities': ['crypto_payments', 'ad_serving'],
                'genesis_complete': self.blockchain.genesis_complete if self.blockchain else False
            }
            
            self._send_message(sock, handshake)
            response = self._receive_message(sock)
            
            if response and response.get('type') == 'handshake_ack':
                self.peer_sockets[peer['peer_id']] = sock
                peer['status'] = 'connected'
                peer['wallet_address'] = response.get('wallet_address', '')
                
                if self.peer_connected_callback:
                    self.peer_connected_callback(peer['peer_id'])
                
                self._request_ads_from_peer(peer['peer_id'])
                self._handle_peer_messages(sock, peer['peer_id'])
            else:
                sock.close()
        except Exception as e:
            logger.debug(f"Failed to connect to peer {peer['peer_id']}: {e}")
    
    def _peer_handler(self):
        """Handle incoming peer connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port + 2000))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1.0)
            
            while self.running:
                try:
                    client_sock, addr = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_peer_connection,
                        args=(client_sock, addr),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
        except Exception as e:
            logger.error(f"Peer handler error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def _handle_peer_connection(self, client_sock, addr):
        """Handle individual peer connection"""
        try:
            client_sock.settimeout(30)
            message = self._receive_message(client_sock)
            
            if message and message.get('type') == 'handshake':
                peer_id = message.get('peer_id')
                ack = {
                    'type': 'handshake_ack',
                    'peer_id': self.client_id,
                    'timestamp': datetime.now().isoformat(),
                    'wallet_address': self.wallet.address if self.wallet else "",
                    'genesis_complete': self.blockchain.genesis_complete if self.blockchain else False
                }
                self._send_message(client_sock, ack)
                
                if peer_id:
                    self.peer_sockets[peer_id] = client_sock
                    if peer_id in self.peers:
                        self.peers[peer_id]['status'] = 'connected'
                        self.peers[peer_id]['wallet_address'] = message.get('wallet_address', '')
                    
                    if self.peer_connected_callback:
                        self.peer_connected_callback(peer_id)
                    
                    self._handle_peer_messages(client_sock, peer_id)
        except Exception as e:
            logger.debug(f"Peer connection error: {e}")
        finally:
            client_sock.close()
    
    def _handle_peer_messages(self, sock, peer_id):
        """Handle messages from connected peer"""
        while self.running:
            try:
                message = self._receive_message(sock)
                if not message:
                    break
                
                if message.get('type') == 'ad_response':
                    ads = message.get('ads', [])
                    if self.ads_received_callback:
                        self.ads_received_callback(ads)
                elif message.get('type') == 'click_notification':
                    self._handle_click_notification(message)
                elif message.get('type') == 'payment_request':
                    self._handle_payment_request(message)
            except Exception:
                break
        
        # Cleanup
        if peer_id in self.peer_sockets:
            del self.peer_sockets[peer_id]
        if peer_id in self.peers:
            self.peers[peer_id]['status'] = 'disconnected'
        
        if self.peer_disconnected_callback:
            self.peer_disconnected_callback(peer_id)
    
    def _handle_click_notification(self, message):
        """Handle click notification from peer"""
        try:
            click_data = message.get('click_data', {})
            click_event = {
                'ad_id': click_data.get('ad_id', ''),
                'user_id': click_data.get('user_id', ''),
                'developer_address': click_data.get('developer_address', ''),
                'advertiser_address': click_data.get('advertiser_address', ''),
                'payout_amount': click_data.get('payout_amount', 0.001),
                'timestamp': click_data.get('timestamp', datetime.now().isoformat())
            }
            self.pending_clicks.append(click_event)
            
            if self.click_received_callback:
                self.click_received_callback(click_event)
        except Exception as e:
            logger.error(f"Error handling click notification: {e}")
    
    def _handle_payment_request(self, message):
        """Handle payment request from peer"""
        try:
            payment_data = message.get('payment_data', {})
            recipient = payment_data.get('recipient_address', '')
            amount = payment_data.get('amount', 0)
            
            if recipient and amount > 0 and self.wallet:
                balance = self._get_wallet_balance()
                if balance >= amount:
                    tx = self.wallet.send(recipient, amount)
                    if tx:
                        if self.payment_sent_callback:
                            self.payment_sent_callback(recipient, amount)
                        logger.info(f"💰 Payment sent: {amount} PYC to {recipient}")
        except Exception as e:
            logger.error(f"Error handling payment request: {e}")
    
    def _process_clicks(self):
        """Process pending click events and send payments"""
        while self.running:
            try:
                if self.pending_clicks and self.wallet:
                    click = self.pending_clicks.pop(0)
                    
                    if not click.get('processed') and click.get('developer_address'):
                        balance = self._get_wallet_balance()
                        if balance >= click['payout_amount']:
                            tx = self.wallet.send(click['developer_address'], click['payout_amount'])
                            if tx:
                                click['processed'] = True
                                click['transaction_id'] = tx.tx_id
                                
                                if self.payment_sent_callback:
                                    self.payment_sent_callback(click['developer_address'], click['payout_amount'])
                                
                                logger.info(f"💰 Click payment: {click['payout_amount']} PYC to {click['developer_address']}")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error processing clicks: {e}")
                time.sleep(5)
    
    def _get_wallet_balance(self):
        """Get wallet balance safely"""
        try:
            if hasattr(self.wallet, 'get_balance'):
                return self.wallet.get_balance()
            return 0.0
        except:
            return 0.0
    
    def _send_message(self, sock, message):
        """Send JSON message over socket"""
        import struct
        data = json.dumps(message).encode()
        length = struct.pack('!I', len(data))
        sock.sendall(length + data)
    
    def _receive_message(self, sock):
        """Receive JSON message from socket"""
        import struct
        try:
            length_data = sock.recv(4)
            if len(length_data) < 4:
                return None
            
            length = struct.unpack('!I', length_data)[0]
            data = b''
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            
            return json.loads(data.decode())
        except Exception:
            return None
    
    def _request_ads_from_peer(self, peer_id):
        """Request ads from connected peer"""
        if peer_id not in self.peer_sockets:
            return
        
        request = {
            'type': 'ad_request',
            'requesting_peer': self.client_id,
            'categories': ['all'],
            'max_ads': 10,
            'timestamp': datetime.now().isoformat(),
            'payment_capable': True
        }
        
        try:
            self._send_message(self.peer_sockets[peer_id], request)
        except Exception as e:
            logger.error(f"Failed to request ads from {peer_id}: {e}")
    
    def _emit_status(self, message):
        """Emit status update"""
        logger.info(message)
        if self.status_update_callback:
            self.status_update_callback(message)
    
    def stop(self):
        """Stop the P2P manager"""
        self.running = False
        self._emit_status("🛑 Crypto P2P Manager stopped")

class DatabaseManager:
    """Basic database manager using SQLite as fallback"""
    
    def __init__(self, db_path="pythoncoin.db"):
        self.db_path = db_path
        self.connection = None
        self.is_connected = False
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.is_connected = True
            self._create_tables()
            logger.info("✅ SQLite database connected")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self.is_connected = False
    
    def _create_tables(self):
        """Create necessary tables"""
        cursor = self.connection.cursor()
        
        # Create developers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS developers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                pythoncoin_address TEXT NOT NULL,
                email TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_clicks INTEGER DEFAULT 0,
                total_earnings REAL DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # Create ad_clicks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ad_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_id TEXT NOT NULL,
                client_id TEXT,
                developer_address TEXT NOT NULL,
                developer_name TEXT,
                zone TEXT DEFAULT 'default',
                payout_amount REAL NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0,
                processed_time TIMESTAMP,
                payment_status TEXT DEFAULT 'pending',
                transaction_id TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Create p2p_clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS p2p_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT,
                wallet_address TEXT,
                status TEXT DEFAULT 'offline',
                version TEXT,
                capabilities TEXT,
                metadata TEXT,
                ad_count INTEGER DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
        logger.info("✅ Database tables created/verified")
    
    def connect(self):
        """Connect to database"""
        return self.is_connected
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a database query"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                return [dict(row) for row in result]
            else:
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
            return None
    
    def register_client(self, client_data):
        """Register a P2P client"""
        try:
            query = """
                INSERT OR REPLACE INTO p2p_clients 
                (client_id, name, host, port, wallet_address, version, capabilities, metadata, ad_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                client_data.get('client_id'),
                client_data.get('name'),
                client_data.get('host'),
                client_data.get('port'),
                client_data.get('wallet_address'),
                client_data.get('version'),
                json.dumps(client_data.get('capabilities', [])),
                json.dumps(client_data.get('metadata', {})),
                client_data.get('ad_count', 0)
            )
            return self.execute_query(query, params)
        except Exception as e:
            logger.error(f"❌ Error registering client: {e}")
            return False

class EnhancedDatabaseManager(DatabaseManager):
    """Enhanced database manager with MySQL support"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'adnetwrk',
            'user': 'root',
            'password': '',
            'autocommit': True,
            'charset': 'utf8mb4'
        }
        
        if MYSQL_AVAILABLE:
            self._init_mysql()
        else:
            super().__init__()
    
    def _init_mysql(self):
        """Initialize MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.is_connected = True
            self._create_mysql_tables()
            logger.info("✅ MySQL database connected")
        except Exception as e:
            logger.error(f"❌ MySQL connection failed: {e}")
            # Fallback to SQLite
            super().__init__()
    
    def _create_mysql_tables(self):
        """Create MySQL tables with enhanced schema"""
        # Implementation would be similar to DatabaseManager but with MySQL syntax
        pass

class DatabaseAutoRegistration:
    """Automatic database registration helper"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def auto_register_client(self, client_data):
        """Automatically register client with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.db_manager.register_client(client_data):
                    logger.info(f"✅ Client auto-registered: {client_data.get('client_id')}")
                    return True
                else:
                    logger.warning(f"⚠️ Registration attempt {attempt + 1} failed")
            except Exception as e:
                logger.error(f"❌ Auto-registration error: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False

class AdStorageManager:
    """Manages advertisement storage and file operations"""
    
    def __init__(self, base_dir="ads_storage"):
        self.base_dir = Path(base_dir)
        self.setup_directory_structure()
    
    def setup_directory_structure(self):
        """Create directory structure for ad storage"""
        directories = [
            self.base_dir,
            self.base_dir / "active",
            self.base_dir / "inactive",
            self.base_dir / "templates",
            self.base_dir / "assets",
            self.base_dir / "exports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.create_default_templates()
    
    def create_default_templates(self):
        """Create default ad templates"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{AD_TITLE}} - PythonCoin Ad</title>
    <style>
        .pyc-ad {
            border: 2px solid #0066cc;
            border-radius: 12px;
            padding: 20px;
            background: linear-gradient(135deg, #fff 0%, #f0f9ff 100%);
            margin: 15px 0;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-image: url('{{AD_IMAGE_URL}}');
            background-size: cover;
            background-position: center;
        }
        .pyc-ad:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,102,204,0.2);
        }
        .pyc-ad-title {
            color: #0066cc;
            font-size: 20px;
            font-weight: bold;
            margin: 0 0 10px 0;
            text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
        }
        .pyc-ad-description {
            color: #555;
            margin: 0 0 15px 0;
            line-height: 1.6;
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 6px;
        }
        .pyc-ad-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pyc-ad-payout {
            background: #28a745;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="pyc-ad" onclick="handleAdClick('{{AD_ID}}')">
        <h3 class="pyc-ad-title">{{AD_TITLE}}</h3>
        <p class="pyc-ad-description">{{AD_DESCRIPTION}}</p>
        <div class="pyc-ad-footer">
            <span>{{AD_CATEGORY}}</span>
            <span class="pyc-ad-payout">+{{AD_PAYOUT}} PYC</span>
        </div>
    </div>
    
    <script>
        function handleAdClick(adId) {
            console.log('PythonCoin ad clicked:', adId);
            if (window.pythonCoinWallet) {
                window.pythonCoinWallet.recordClick(adId);
            }
            
            const clickUrl = '{{AD_CLICK_URL}}';
            if (clickUrl && clickUrl !== '#') {
                window.open(clickUrl, '_blank');
            }
        }
    </script>
</body>
</html>"""
        
        template_path = self.base_dir / "templates" / "default.html"
        if not template_path.exists():
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
    
    def save_ad(self, ad_data, format_type='html'):
        """Save advertisement as file trio (JSON, HTML, JS)"""
        try:
            ad_id = ad_data.get('id', str(uuid.uuid4()))
            
            metadata = {
                'id': ad_id,
                'title': ad_data.get('title', ''),
                'description': ad_data.get('description', ''),
                'category': ad_data.get('category', 'general'),
                'click_url': ad_data.get('click_url', '#'),
                'image_url': ad_data.get('image_url', ''),
                'payout_rate': ad_data.get('payout_rate', 0.001),
                'advertiser_address': ad_data.get('advertiser_address', ''),
                'created_at': datetime.now().isoformat(),
                'status': 'active',
                'format': format_type,
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            # Generate HTML content
            html_content = self.generate_html_ad(metadata)
            
            # Generate JS adblock
            js_content = self.generate_js_adblock(metadata)
            
            # Save all three files
            base_filename = f"{ad_id}"
            
            # Save JSON metadata
            json_path = self.base_dir / "active" / f"{base_filename}_meta.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Save HTML
            html_path = self.base_dir / "active" / f"{base_filename}_html.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save JS adblock
            js_path = self.base_dir / "active" / f"{metadata['advertiser_address']}_adblock.js"
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            return {
                'success': True,
                'ad_id': ad_id,
                'files': {
                    'json': str(json_path),
                    'html': str(html_path),
                    'js': str(js_path)
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_html_ad(self, metadata):
        """Generate HTML ad from template"""
        template_path = self.base_dir / "templates" / "default.html"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except:
            template = "<div><h3>{{AD_TITLE}}</h3><p>{{AD_DESCRIPTION}}</p></div>"
        
        replacements = {
            '{{AD_ID}}': metadata['id'],
            '{{AD_TITLE}}': metadata['title'],
            '{{AD_DESCRIPTION}}': metadata['description'],
            '{{AD_CATEGORY}}': metadata['category'].title(),
            '{{AD_CLICK_URL}}': metadata['click_url'],
            '{{AD_IMAGE_URL}}': metadata.get('image_url', ''),
            '{{AD_PAYOUT}}': f"{metadata['payout_rate']:.6f}"
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))
        
        return template
    
    def generate_js_adblock(self, metadata):
        """Generate JavaScript adblock for the advertiser"""
        js_template = f"""
// PythonCoin P2P Ad Block for {metadata['advertiser_address']}
// Generated: {metadata['created_at']}
// Ad ID: {metadata['id']}

(function() {{
    'use strict';
    
    const PYTHONCOIN_AD_CONFIG = {{
        adId: '{metadata['id']}',
        advertiserAddress: '{metadata['advertiser_address']}',
        payoutRate: {metadata['payout_rate']},
        clickUrl: '{metadata['click_url']}',
        title: '{metadata['title']}',
        description: '{metadata['description']}',
        category: '{metadata['category']}'
    }};
    
    function loadPythonCoinAd() {{
        const adZones = document.querySelectorAll('[data-pyc-zone]');
        
        adZones.forEach(zone => {{
            const adContainer = document.createElement('div');
            adContainer.innerHTML = `
                <div class="pythoncoin-ad" style="
                    border: 2px solid #0066cc;
                    border-radius: 12px;
                    padding: 20px;
                    background: linear-gradient(135deg, #fff 0%, #f0f9ff 100%);
                    margin: 15px 0;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    {metadata.get('image_url') and f"background-image: url('{metadata['image_url']}'); background-size: cover; background-position: center;" or ''}
                " onclick="handlePythonCoinAdClick()">
                    <h3 style="color: #0066cc; margin: 0 0 10px 0;">${{PYTHONCOIN_AD_CONFIG.title}}</h3>
                    <p style="margin: 0 0 15px 0; background: rgba(255,255,255,0.9); padding: 10px; border-radius: 6px;">${{PYTHONCOIN_AD_CONFIG.description}}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>${{PYTHONCOIN_AD_CONFIG.category}}</span>
                        <span style="background: #28a745; color: white; padding: 8px 16px; border-radius: 20px; font-size: 12px;">
                            +${{PYTHONCOIN_AD_CONFIG.payoutRate.toFixed(6)}} PYC
                        </span>
                    </div>
                </div>
            `;
            
            zone.appendChild(adContainer);
        }});
    }}
    
    window.handlePythonCoinAdClick = function() {{
        console.log('PythonCoin ad clicked:', PYTHONCOIN_AD_CONFIG.adId);
        
        // Record click
        fetch('/click', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                ad_id: PYTHONCOIN_AD_CONFIG.adId,
                advertiser_address: PYTHONCOIN_AD_CONFIG.advertiserAddress,
                payout_amount: PYTHONCOIN_AD_CONFIG.payoutRate
            }})
        }}).then(response => response.json())
        .then(data => console.log('Click recorded:', data))
        .catch(error => console.error('Click recording failed:', error));
        
        // Open click URL
        if (PYTHONCOIN_AD_CONFIG.clickUrl && PYTHONCOIN_AD_CONFIG.clickUrl !== '#') {{
            window.open(PYTHONCOIN_AD_CONFIG.clickUrl, '_blank');
        }}
    }};
    
    // Load ads when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', loadPythonCoinAd);
    }} else {{
        loadPythonCoinAd();
    }}
}})();
"""
        return js_template
    
    def load_all_ads(self):
        """Load all active advertisements"""
        ads = []
        active_dir = self.base_dir / "active"
        
        try:
            for metadata_file in active_dir.glob("*_meta.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                ads.append(metadata)
        except Exception as e:
            logger.error(f"Error loading ads: {e}")
        
        return ads

class EnhancedAdFetcher:
    """Fetches real ads from multiple sources"""
    
    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.cached_ads = []
        self.cache_timestamp = 0
        self.cache_duration = 30
    
    def get_real_ads(self, category_filter=None, limit=10):
        """Get real advertisements from all sources"""
        try:
            current_time = time.time()
            if (current_time - self.cache_timestamp < self.cache_duration and self.cached_ads):
                return self._filter_ads(self.cached_ads, category_filter, limit)
            
            all_ads = []
            all_ads.extend(self._load_from_storage())
            all_ads.extend(self._load_from_p2p_network())
            
            if not all_ads:
                all_ads = self._generate_fallback_ads()
            
            unique_ads = self._remove_duplicates(all_ads)
            self.cached_ads = unique_ads
            self.cache_timestamp = current_time
            
            return self._filter_ads(unique_ads, category_filter, limit)
        except Exception as e:
            logger.error(f"Error fetching ads: {e}")
            return self._generate_fallback_ads()
    
    def _load_from_storage(self):
        """Load ads from storage"""
        try:
            storage_manager = AdStorageManager()
            stored_ads = storage_manager.load_all_ads()
            return self._format_ads(stored_ads, 'storage')
        except Exception as e:
            logger.warning(f"Storage load error: {e}")
        return []
    
    def _load_from_p2p_network(self):
        """Load ads from P2P network"""
        # This would integrate with the P2P manager
        return []
    
    def _format_ads(self, ads, source):
        """Format ads to standard structure"""
        formatted_ads = []
        for ad in ads:
            if isinstance(ad, dict):
                ad_dict = ad
            else:
                ad_dict = ad.__dict__
            
            formatted_ad = {
                'id': ad_dict.get('id', ''),
                'title': ad_dict.get('title', 'Advertisement'),
                'description': ad_dict.get('description', ''),
                'category': ad_dict.get('category', 'general'),
                'payout_rate': float(ad_dict.get('payout_rate', 0.001)),
                'click_url': ad_dict.get('click_url', '#'),
                'image_url': ad_dict.get('image_url', ''),
                'advertiser_address': ad_dict.get('advertiser_address', ''),
                'created_at': ad_dict.get('created_at', ''),
                'source': source
            }
            formatted_ads.append(formatted_ad)
        
        return formatted_ads
    
    def _generate_fallback_ads(self):
        """Generate fallback demo ads"""
        current_time = int(time.time())
        
        return [{
            'id': f'demo_ad_{current_time}',
            'title': 'Learn Cryptocurrency Basics',
            'description': 'Educational content about blockchain and cryptocurrency technology.',
            'category': 'education',
            'payout_rate': 0.001,
            'click_url': 'https://example.com/learn-crypto',
            'image_url': '',
            'advertiser_address': 'demo_address',
            'created_at': datetime.now().isoformat(),
            'source': 'fallback'
        }]
    
    def _remove_duplicates(self, ads):
        """Remove duplicate ads"""
        seen_ids = set()
        unique_ads = []
        for ad in ads:
            ad_id = ad.get('id', '')
            if ad_id and ad_id not in seen_ids:
                seen_ids.add(ad_id)
                unique_ads.append(ad)
        return unique_ads
    
    def _filter_ads(self, ads, category_filter=None, limit=10):
        """Filter and limit ads"""
        filtered_ads = ads
        if category_filter and category_filter != 'all':
            filtered_ads = [ad for ad in ads 
                          if ad.get('category', '').lower() == category_filter.lower()]
        
        # Sort by creation date
        try:
            filtered_ads.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except:
            pass
        
        return filtered_ads[:limit]

class EnhancedDeveloperRegistration:
    """Manages developer registration and tracking"""
    
    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.registered_developers = {}
        self.online_developers = {}
        self.last_activity = {}
    
    def register_developer(self, developer_name, wallet_address, session_info=None):
        """Register a developer"""
        try:
            self.registered_developers[developer_name] = {
                'wallet_address': wallet_address,
                'registered_at': datetime.now().isoformat(),
                'total_clicks': 0,
                'total_earnings': 0.0,
                'last_seen': datetime.now().isoformat(),
                'session_info': session_info or {}
            }
            
            self.mark_developer_online(developer_name, session_info)
            logger.info(f"👤 Developer registered: {developer_name}")
            return True
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def mark_developer_online(self, developer_name, session_info=None):
        """Mark developer as online"""
        try:
            self.online_developers[developer_name] = {
                'online_since': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'session_info': session_info or {}
            }
            self.last_activity[developer_name] = datetime.now().timestamp()
        except Exception as e:
            logger.error(f"Online marking error: {e}")
    
    def update_developer_activity(self, developer_name):
        """Update developer activity"""
        try:
            self.last_activity[developer_name] = datetime.now().timestamp()
            if developer_name in self.online_developers:
                self.online_developers[developer_name]['last_activity'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Activity update error: {e}")
    
    def record_developer_click(self, developer_name, amount):
        """Record click for developer"""
        try:
            if developer_name in self.registered_developers:
                self.registered_developers[developer_name]['total_clicks'] += 1
                self.registered_developers[developer_name]['total_earnings'] += amount
                self.registered_developers[developer_name]['last_seen'] = datetime.now().isoformat()
                self.update_developer_activity(developer_name)
        except Exception as e:
            logger.error(f"Click recording error: {e}")
    
    def cleanup_offline_developers(self):
        """Clean up offline developers"""
        try:
            current_time = datetime.now().timestamp()
            offline_threshold = 300  # 5 minutes
            
            offline_devs = [
                dev_name for dev_name, last_time in self.last_activity.items()
                if current_time - last_time > offline_threshold
            ]
            
            for dev_name in offline_devs:
                if dev_name in self.online_developers:
                    del self.online_developers[dev_name]
                if dev_name in self.registered_developers:
                    self.registered_developers[dev_name]['last_seen'] = datetime.now().isoformat()
            
            if offline_devs:
                logger.info(f"🔄 Marked {len(offline_devs)} developers as offline")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# --------------------------------
# Advanced Node Discovery System
# --------------------------------

class NodeDiscovery:
    """Advanced P2P node discovery system for PythonCoin network"""
    
    def __init__(self, node_instance):
        self.node = node_instance
        self.known_peers = set()
        self.active_peers = set()
        self.peer_info = {}
        self.discovery_thread = None
        self.running = False
        
        # Bootstrap nodes (seed nodes for initial discovery)
        self.bootstrap_nodes = [
            ("secupgrade.com", 5000),
            ("127.0.0.1", 5001),
            ("127.0.0.1", 5002)
        ]
        
        logger.info("Node discovery system initialized")
    
    def start_discovery(self):
        """Start the node discovery process"""
        if self.running:
            return
            
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        logger.info("🔍 Node discovery started")
    
    def stop_discovery(self):
        """Stop the node discovery process"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=2)
        logger.info("🔍 Node discovery stopped")
    
    def _discovery_loop(self):
        """Main discovery loop"""
        while self.running:
            try:
                # 1. Bootstrap discovery from known seed nodes
                self._bootstrap_discovery()
                
                # 2. Query known peers for more peers
                self._peer_to_peer_discovery()
                
                # 3. Health check existing connections
                self._health_check_peers()
                
                # 4. Clean up inactive peers
                self._cleanup_inactive_peers()
                
                # Sleep before next discovery cycle
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")
                time.sleep(10)
    
    def _bootstrap_discovery(self):
        """Bootstrap discovery from seed nodes"""
        for host, port in self.bootstrap_nodes:
            if not self.running:
                break
                
            try:
                if (host, port) == (self.node.host, self.node.port):
                    continue  # Skip self
                
                peer_info = self._query_peer(host, port)
                if peer_info:
                    self._add_peer(host, port, peer_info)
                    
            except Exception as e:
                logger.debug(f"Bootstrap query failed for {host}:{port} - {e}")
    
    def _peer_to_peer_discovery(self):
        """Query existing peers for more peers"""
        for peer_addr in list(self.active_peers):
            if not self.running:
                break
                
            try:
                host, port = peer_addr
                peer_list = self._request_peer_list(host, port)
                
                for peer_data in peer_list:
                    peer_host = peer_data.get('host')
                    peer_port = peer_data.get('port')
                    
                    if peer_host and peer_port:
                        if (peer_host, peer_port) not in self.known_peers:
                            peer_info = self._query_peer(peer_host, peer_port)
                            if peer_info:
                                self._add_peer(peer_host, peer_port, peer_info)
                                
            except Exception as e:
                logger.debug(f"P2P discovery error with {peer_addr}: {e}")
    
    def _query_peer(self, host, port, timeout=5):
        """Query a peer for basic information"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
                
                # Send peer info request
                request = {
                    "type": "peer_info_request",
                    "node_id": self.node.node_id,
                    "timestamp": time.time()
                }
                
                message = json.dumps(request).encode() + b'\n'
                sock.send(message)
                
                # Receive response
                response_data = sock.recv(4096).decode().strip()
                if response_data:
                    response = json.loads(response_data)
                    if response.get("type") == "peer_info_response":
                        return response.get("data", {})
                        
        except Exception as e:
            logger.debug(f"Peer query failed for {host}:{port}: {e}")
            
        return None
    
    def _request_peer_list(self, host, port, timeout=5):
        """Request list of known peers from a peer"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
                
                request = {
                    "type": "peer_list_request",
                    "node_id": self.node.node_id,
                    "timestamp": time.time()
                }
                
                message = json.dumps(request).encode() + b'\n'
                sock.send(message)
                
                response_data = sock.recv(8192).decode().strip()
                if response_data:
                    response = json.loads(response_data)
                    if response.get("type") == "peer_list_response":
                        return response.get("peers", [])
                        
        except Exception as e:
            logger.debug(f"Peer list request failed for {host}:{port}: {e}")
            
        return []
    
    def _add_peer(self, host, port, peer_info):
        """Add a peer to our known peers"""
        peer_addr = (host, port)
        self.known_peers.add(peer_addr)
        self.active_peers.add(peer_addr)
        self.peer_info[peer_addr] = {
            **peer_info,
            'discovered_at': time.time(),
            'last_seen': time.time(),
            'connection_count': 0,
            'successful_connections': 0
        }
        
        logger.info(f"🔗 Discovered peer: {host}:{port}")
    
    def _health_check_peers(self):
        """Health check existing peers"""
        for peer_addr in list(self.active_peers):
            try:
                host, port = peer_addr
                peer_info = self._query_peer(host, port, timeout=3)
                
                if peer_info:
                    self.peer_info[peer_addr]['last_seen'] = time.time()
                    self.peer_info[peer_addr]['successful_connections'] += 1
                else:
                    # Peer is not responding
                    if peer_addr in self.active_peers:
                        self.active_peers.remove(peer_addr)
                        logger.debug(f"🔴 Peer inactive: {host}:{port}")
                        
            except Exception as e:
                logger.debug(f"Health check error for {peer_addr}: {e}")
    
    def _cleanup_inactive_peers(self):
        """Clean up peers that haven't been seen for a while"""
        current_time = time.time()
        inactive_timeout = 300  # 5 minutes
        
        for peer_addr in list(self.known_peers):
            peer_data = self.peer_info.get(peer_addr, {})
            last_seen = peer_data.get('last_seen', 0)
            
            if current_time - last_seen > inactive_timeout:
                self.known_peers.discard(peer_addr)
                self.active_peers.discard(peer_addr)
                if peer_addr in self.peer_info:
                    del self.peer_info[peer_addr]
                logger.debug(f"🗑️ Cleaned up inactive peer: {peer_addr}")
    
    def get_active_peers(self):
        """Get list of currently active peers"""
        return list(self.active_peers)
    
    def get_peer_count(self):
        """Get count of active peers"""
        return len(self.active_peers)
    
    def broadcast_to_peers(self, message_data):
        """Broadcast a message to all active peers"""
        successful_sends = 0
        
        for peer_addr in list(self.active_peers):
            try:
                host, port = peer_addr
                success = self._send_message_to_peer(host, port, message_data)
                if success:
                    successful_sends += 1
                    
            except Exception as e:
                logger.debug(f"Broadcast error to {peer_addr}: {e}")
        
        return successful_sends
    
    def _send_message_to_peer(self, host, port, message_data, timeout=5):
        """Send a message to a specific peer"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
                
                message = json.dumps(message_data).encode() + b'\n'
                sock.send(message)
                
                return True
                
        except Exception as e:
            logger.debug(f"Message send failed to {host}:{port}: {e}")
            return False

# --------------------------------
# Advanced Difficulty Adjustment
# --------------------------------

class DifficultyAdjustment:
    """Advanced difficulty adjustment algorithm for PythonCoin"""
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.target_block_time = 60  # 1 minute per block
        self.adjustment_interval = 10  # Adjust every 10 blocks
        self.max_adjustment_factor = 4  # Maximum 4x adjustment per period
        
    def calculate_next_difficulty(self):
        """Calculate the difficulty for the next block"""
        chain_length = len(self.blockchain.chain)
        
        # Use default difficulty for first few blocks
        if chain_length < self.adjustment_interval:
            return 4  # Starting difficulty
        
        # Get the last adjustment_interval blocks
        recent_blocks = self.blockchain.chain[-self.adjustment_interval:]
        
        # Calculate actual time taken for these blocks
        time_taken = recent_blocks[-1].timestamp - recent_blocks[0].timestamp
        expected_time = self.target_block_time * (self.adjustment_interval - 1)
        
        # Calculate current difficulty
        current_difficulty = recent_blocks[-1].difficulty
        
        # Calculate adjustment ratio
        adjustment_ratio = expected_time / time_taken
        
        # Limit the adjustment to prevent wild swings
        adjustment_ratio = max(1/self.max_adjustment_factor, 
                             min(self.max_adjustment_factor, adjustment_ratio))
        
        # Calculate new difficulty
        new_difficulty = max(1, int(current_difficulty * adjustment_ratio))
        
        logger.info(f"⚖️ Difficulty adjustment: {current_difficulty} → {new_difficulty} "
                   f"(blocks took {time_taken:.1f}s, expected {expected_time:.1f}s)")
        
        return new_difficulty

# --------------------------------
# Network Synchronization System
# --------------------------------

class NetworkSynchronizer:
    """Handles blockchain synchronization between peers"""
    
    def __init__(self, node_instance):
        self.node = node_instance
        self.blockchain = node_instance.blockchain
        self.syncing = False
        self.sync_thread = None
        
    def start_sync(self):
        """Start blockchain synchronization"""
        if self.syncing:
            return
            
        self.syncing = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("🔄 Blockchain sync started")
    
    def stop_sync(self):
        """Stop blockchain synchronization"""
        self.syncing = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
        logger.info("🔄 Blockchain sync stopped")
    
    def _sync_loop(self):
        """Main synchronization loop"""
        while self.syncing:
            try:
                if hasattr(self.node, 'discovery') and self.node.discovery:
                    active_peers = self.node.discovery.get_active_peers()
                    
                    if active_peers:
                        # Request blockchain info from peers
                        peer_chains = self._query_peer_blockchains(active_peers)
                        
                        # Find the longest valid chain
                        best_chain = self._find_best_chain(peer_chains)
                        
                        if best_chain and len(best_chain) > len(self.blockchain.chain):
                            # Sync to the longer chain
                            self._sync_to_chain(best_chain)
                
                # Sleep before next sync cycle
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                time.sleep(30)
    
    def _query_peer_blockchains(self, peers):
        """Query peers for their blockchain information"""
        peer_chains = []
        
        for peer_addr in peers[:5]:  # Limit to 5 peers to avoid spam
            try:
                host, port = peer_addr
                chain_data = self._request_blockchain_info(host, port)
                
                if chain_data:
                    peer_chains.append({
                        'peer': peer_addr,
                        'chain_length': chain_data.get('length', 0),
                        'latest_hash': chain_data.get('latest_hash', ''),
                        'blocks': chain_data.get('blocks', [])
                    })
                    
            except Exception as e:
                logger.debug(f"Blockchain query failed for {peer_addr}: {e}")
        
        return peer_chains
    
    def _request_blockchain_info(self, host, port, timeout=10):
        """Request blockchain information from a peer"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
                
                request = {
                    "type": "blockchain_info_request",
                    "node_id": self.node.node_id,
                    "current_length": len(self.blockchain.chain),
                    "timestamp": time.time()
                }
                
                message = json.dumps(request).encode() + b'\n'
                sock.send(message)
                
                # Receive potentially large response
                response_data = b''
                while True:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    response_data += chunk
                    if b'\n' in chunk:
                        break
                
                if response_data:
                    response = json.loads(response_data.decode().strip())
                    if response.get("type") == "blockchain_info_response":
                        return response.get("data", {})
                        
        except Exception as e:
            logger.debug(f"Blockchain info request failed for {host}:{port}: {e}")
            
        return None
    
    def _find_best_chain(self, peer_chains):
        """Find the best (longest valid) chain among peers"""
        if not peer_chains:
            return None
        
        # Sort by chain length
        peer_chains.sort(key=lambda x: x['chain_length'], reverse=True)
        
        # Return the longest chain for now (in production, would validate)
        best_peer_chain = peer_chains[0]
        
        if best_peer_chain['chain_length'] > len(self.blockchain.chain):
            logger.info(f"📈 Found longer chain: {best_peer_chain['chain_length']} blocks "
                       f"vs our {len(self.blockchain.chain)} blocks")
            return best_peer_chain['blocks']
        
        return None
    
    def _sync_to_chain(self, new_chain_blocks):
        """Synchronize our blockchain to a new chain"""
        try:
            logger.info(f"🔄 Syncing to new chain with {len(new_chain_blocks)} blocks")
            
            # Validate the new chain (simplified validation)
            if self._validate_chain(new_chain_blocks):
                # Replace our chain
                self.blockchain.chain = []
                
                # Add blocks one by one
                for block_data in new_chain_blocks:
                    block = Block(
                        index=block_data['index'],
                        transactions=block_data['transactions'],
                        timestamp=block_data['timestamp'],
                        previous_hash=block_data['previous_hash'],
                        nonce=block_data.get('nonce', 0),
                        difficulty=block_data.get('difficulty', 4)
                    )
                    block.hash = block_data['hash']
                    self.blockchain.chain.append(block)
                
                # Rebuild UTXO set
                self.blockchain._rebuild_utxo()
                
                logger.info(f"✅ Successfully synced to new chain")
                
            else:
                logger.warning("❌ New chain validation failed")
                
        except Exception as e:
            logger.error(f"Chain sync error: {e}")
    
    def _validate_chain(self, chain_blocks):
        """Validate a blockchain (simplified validation)"""
        try:
            # Basic validation - check hashes and structure
            for i, block_data in enumerate(chain_blocks):
                if i > 0:
                    previous_block = chain_blocks[i-1]
                    if block_data['previous_hash'] != previous_block['hash']:
                        return False
                
                # Validate block hash (simplified)
                if not block_data.get('hash'):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Chain validation error: {e}")
            return False

# Export all classes for use in other modules
__all__ = [
    'CryptoUtils', 'TransactionInput', 'TransactionOutput', 'Transaction',
    'DataTransaction', 'DSAVerificationTransaction', 'Block', 'Blockchain',
    'Wallet', 'Node', 'CryptoMiningThread', 'CryptoP2PManager',
    'DatabaseManager', 'EnhancedDatabaseManager', 'DatabaseAutoRegistration',
    'NodeDiscovery', 'DifficultyAdjustment', 'NetworkSynchronizer',
    'EnhancedDeveloperRegistration',
    'logger'
]