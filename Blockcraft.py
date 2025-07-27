import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import hashlib
import json
import time
from datetime import datetime
import threading

class Block:
    """
    Represents a single block in the blockchain
    Each block contains data, timestamp, hash, and reference to previous block
    """
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index                    # Position of block in chain
        self.transactions = transactions      # List of transactions in this block
        self.timestamp = timestamp           # When block was created
        self.previous_hash = previous_hash   # Hash of previous block (creates the chain)
        self.nonce = nonce                   # Number used once for proof of work
        self.hash = self.calculate_hash()    # This block's unique hash

    def calculate_hash(self):
        """
        Creates a unique hash for this block using SHA-256
        Combines all block data into a string and hashes it
        """
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        """
        Proof of Work algorithm - finds a hash starting with required zeros
        Difficulty determines how many leading zeros are required
        """
        target = "0" * difficulty            # Target pattern (e.g., "00" for difficulty 2)
        while self.hash[:difficulty] != target:
            self.nonce += 1                  # Try different nonce values
            self.hash = self.calculate_hash()  # Recalculate hash
        print(f"Block mined: {self.hash}")

class Blockchain:
    """
    Main blockchain class that manages the chain of blocks
    Handles adding transactions, mining blocks, and validation
    """
    def __init__(self):
        self.chain = [self.create_genesis_block()]  # Start with genesis block
        self.difficulty = 2                         # Mining difficulty (2 leading zeros)
        self.pending_transactions = []              # Transactions waiting to be mined
        self.mining_reward = 100                    # Reward for mining a block

    def create_genesis_block(self):
        """
        Creates the first block in the blockchain
        Genesis block has no previous hash and contains initial data
        """
        return Block(0, [], time.time(), "0")

    def get_latest_block(self):
        """Returns the most recent block in the chain"""
        return self.chain[-1]

    def add_transaction(self, transaction):
        """
        Adds a new transaction to the pending transactions list
        Transactions are not added to blockchain until a block is mined
        """
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, mining_reward_address):
        """
        Creates a new block with all pending transactions
        Always adds mining reward transaction and mines the block
        """
        # Create a copy of pending transactions
        transactions_to_mine = self.pending_transactions.copy()
        
        # Add mining reward transaction
        reward_transaction = {
            'from': 'SYSTEM',                # Mining rewards come from system
            'to': mining_reward_address,     # Miner gets the reward
            'amount': self.mining_reward,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'mining_reward'
        }
        transactions_to_mine.append(reward_transaction)

        # Create new block with transactions
        block = Block(
            len(self.chain),                 # Block index
            transactions_to_mine,            # All transactions including reward
            time.time(),                     # Current timestamp
            self.get_latest_block().hash     # Previous block's hash
        )
        
        # Mine the block (proof of work)
        block.mine_block(self.difficulty)
        
        # Add mined block to chain and clear pending transactions
        self.chain.append(block)
        self.pending_transactions = []
        
        return block

    def get_balance(self, address):
        """
        Calculates balance for a given address
        Goes through all transactions in all blocks
        """
        balance = 0
        
        # Check all blocks in the chain
        for block in self.chain:
            # Check all transactions in each block
            for transaction in block.transactions:
                if transaction['from'] == address:
                    balance -= transaction['amount']  # Subtract sent amount
                if transaction['to'] == address:
                    balance += transaction['amount']  # Add received amount
        
        return balance

    def is_chain_valid(self):
        """
        Validates the entire blockchain
        Checks if all blocks are properly linked and not tampered with
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if current block properly references previous block
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True

class BlockchainGUI:
    """
    Graphical User Interface for the blockchain
    Provides an attractive dark-themed interface with vibrant colors
    """
    def __init__(self, root):
        self.root = root
        self.blockchain = Blockchain()  # Create new blockchain instance
        
        # Configure main window
        self.root.title("🔗 Simple Blockchain Explorer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')  # Dark background
        
        # Configure custom styles for dark theme
        self.setup_styles()
        
        # Create the user interface
        self.create_widgets()
        
        # Update display initially
        self.update_display()

    def setup_styles(self):
        """
        Configures custom styles for dark theme with vibrant colors
        Uses ttk.Style to customize widget appearances
        """
        style = ttk.Style()
        
        # Configure notebook (tab) style
        style.configure('Custom.TNotebook', 
                       background='#1a1a1a',
                       borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                       background='#2d2d2d',
                       foreground='#00ff88',  # Vibrant green
                       padding=[20, 10],
                       font=('Arial', 10, 'bold'))
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', '#00ff88')],  # Active tab in green
                 foreground=[('selected', '#1a1a1a')])

    def create_widgets(self):
        """
        Creates all GUI widgets organized in tabs
        Main interface has three tabs: Transactions, Blockchain, Mining
        """
        # Create main container with notebook (tabbed interface)
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create title label
        title_label = tk.Label(main_frame, 
                              text="🔗 BLOCKCHAIN EXPLORER", 
                              font=('Arial', 24, 'bold'),
                              bg='#1a1a1a', 
                              fg='#00ff88')  # Vibrant green
        title_label.pack(pady=(0, 20))
        
        # Create tabbed interface
        self.notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)
        
        # Create individual tabs
        self.create_transaction_tab()
        self.create_blockchain_tab()
        self.create_mining_tab()

    def create_transaction_tab(self):
        """
        Creates the transaction tab where users can send transactions
        Includes input fields and balance display
        """
        # Create tab frame
        transaction_frame = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(transaction_frame, text='💸 Transactions')
        
        # Transaction form section
        form_frame = tk.Frame(transaction_frame, bg='#2d2d2d', relief='raised', bd=2)
        form_frame.pack(fill='x', padx=20, pady=20)
        
        # Form title
        tk.Label(form_frame, text="Send Transaction", 
                font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#ff6b35').pack(pady=10)  # Orange
        
        # Input fields with labels
        input_frame = tk.Frame(form_frame, bg='#2d2d2d')
        input_frame.pack(pady=10)
        
        # From address input
        tk.Label(input_frame, text="From Address:", 
                font=('Arial', 12), bg='#2d2d2d', fg='#ffffff').grid(row=0, column=0, sticky='w', pady=5)
        self.from_entry = tk.Entry(input_frame, font=('Arial', 12), width=30, 
                                  bg='#404040', fg='#ffffff', insertbackground='#ffffff')
        self.from_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # To address input
        tk.Label(input_frame, text="To Address:", 
                font=('Arial', 12), bg='#2d2d2d', fg='#ffffff').grid(row=1, column=0, sticky='w', pady=5)
        self.to_entry = tk.Entry(input_frame, font=('Arial', 12), width=30,
                                bg='#404040', fg='#ffffff', insertbackground='#ffffff')
        self.to_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Amount input
        tk.Label(input_frame, text="Amount:", 
                font=('Arial', 12), bg='#2d2d2d', fg='#ffffff').grid(row=2, column=0, sticky='w', pady=5)
        self.amount_entry = tk.Entry(input_frame, font=('Arial', 12), width=30,
                                    bg='#404040', fg='#ffffff', insertbackground='#ffffff')
        self.amount_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Send transaction button
        send_button = tk.Button(form_frame, text="Send Transaction", 
                               font=('Arial', 12, 'bold'),
                               bg='#ff6b35', fg='#ffffff',  # Orange button
                               command=self.send_transaction,
                               relief='flat', padx=20, pady=10)
        send_button.pack(pady=15)
        
        # Balance display section
        balance_frame = tk.Frame(transaction_frame, bg='#2d2d2d', relief='raised', bd=2)
        balance_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Label(balance_frame, text="Check Balance", 
                font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#4ecdc4').pack(pady=10)  # Cyan
        
        # Balance check inputs
        balance_input_frame = tk.Frame(balance_frame, bg='#2d2d2d')
        balance_input_frame.pack(pady=10)
        
        tk.Label(balance_input_frame, text="Address:", 
                font=('Arial', 12), bg='#2d2d2d', fg='#ffffff').pack(side='left', padx=5)
        self.balance_entry = tk.Entry(balance_input_frame, font=('Arial', 12), width=25,
                                     bg='#404040', fg='#ffffff', insertbackground='#ffffff')
        self.balance_entry.pack(side='left', padx=5)
        
        check_button = tk.Button(balance_input_frame, text="Check Balance", 
                                font=('Arial', 10, 'bold'),
                                bg='#4ecdc4', fg='#1a1a1a',  # Cyan button
                                command=self.check_balance,
                                relief='flat', padx=15, pady=5)
        check_button.pack(side='left', padx=10)
        
        # Balance result display
        self.balance_label = tk.Label(balance_frame, text="Balance: -", 
                                     font=('Arial', 14, 'bold'), 
                                     bg='#2d2d2d', fg='#00ff88')  # Green text
        self.balance_label.pack(pady=10)

    def create_blockchain_tab(self):
        """
        Creates the blockchain tab showing all blocks and their contents
        Displays the entire blockchain in a scrollable text area
        """
        blockchain_frame = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(blockchain_frame, text='⛓️ Blockchain')
        
        # Title and refresh button
        top_frame = tk.Frame(blockchain_frame, bg='#1a1a1a')
        top_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(top_frame, text="Blockchain Explorer", 
                font=('Arial', 18, 'bold'), bg='#1a1a1a', fg='#9b59b6').pack(side='left')  # Purple
        
        refresh_button = tk.Button(top_frame, text="🔄 Refresh", 
                                  font=('Arial', 10, 'bold'),
                                  bg='#9b59b6', fg='#ffffff',  # Purple button
                                  command=self.update_display,
                                  relief='flat', padx=15, pady=5)
        refresh_button.pack(side='right')
        
        # Scrollable text area for blockchain display
        self.blockchain_text = scrolledtext.ScrolledText(
            blockchain_frame,
            font=('Consolas', 10),  # Monospace font for better formatting
            bg='#2d2d2d',
            fg='#ffffff',
            insertbackground='#ffffff',
            height=25
        )
        self.blockchain_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))

    def create_mining_tab(self):
        """
        Creates the mining tab where users can mine new blocks
        Includes mining controls and status display
        """
        mining_frame = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(mining_frame, text='⛏️ Mining')
        
        # Quick start instructions
        instruction_frame = tk.Frame(mining_frame, bg='#2d2d2d', relief='raised', bd=2)
        instruction_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(instruction_frame, text="🚀 Quick Start Guide", 
                font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#00ff88').pack(pady=10)
        
        instructions = """1. Enter any name as Miner Address (e.g., 'Alice')
2. Click 'Start Mining' to create your first block and earn 100 coins
3. Go to Transactions tab to send coins to others
4. Come back here to mine more blocks and process transactions"""
        
        tk.Label(instruction_frame, text=instructions, 
                font=('Arial', 11), bg='#2d2d2d', fg='#ffffff', justify='left').pack(pady=10)
        
        # Mining control section
        control_frame = tk.Frame(mining_frame, bg='#2d2d2d', relief='raised', bd=2)
        control_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Label(control_frame, text="Mine New Block", 
                font=('Arial', 18, 'bold'), bg='#2d2d2d', fg='#f39c12').pack(pady=15)  # Yellow
        
        # Miner address input
        address_frame = tk.Frame(control_frame, bg='#2d2d2d')
        address_frame.pack(pady=10)
        
        tk.Label(address_frame, text="Miner Address:", 
                font=('Arial', 12), bg='#2d2d2d', fg='#ffffff').pack(side='left', padx=5)
        self.miner_entry = tk.Entry(address_frame, font=('Arial', 12), width=30,
                                   bg='#404040', fg='#ffffff', insertbackground='#ffffff')
        self.miner_entry.pack(side='left', padx=5)
        
        # Set default miner name
        self.miner_entry.insert(0, "Alice")
        
        # Mine button
        self.mine_button = tk.Button(control_frame, text="⛏️ Start Mining", 
                                    font=('Arial', 14, 'bold'),
                                    bg='#f39c12', fg='#1a1a1a',  # Yellow button
                                    command=self.mine_block,
                                    relief='flat', padx=25, pady=12)
        self.mine_button.pack(pady=15)
        
        # Mining status display
        status_frame = tk.Frame(mining_frame, bg='#2d2d2d', relief='raised', bd=2)
        status_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Label(status_frame, text="Mining Status", 
                font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#e74c3c').pack(pady=10)  # Red
        
        self.mining_status = tk.Label(status_frame, text="Ready to mine your first block!", 
                                     font=('Arial', 12), bg='#2d2d2d', fg='#ffffff')
        self.mining_status.pack(pady=10)
        
        # Blockchain stats
        stats_frame = tk.Frame(mining_frame, bg='#2d2d2d', relief='raised', bd=2)
        stats_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        tk.Label(stats_frame, text="Blockchain Statistics", 
                font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#00ff88').pack(pady=10)  # Green
        
        self.stats_text = tk.Text(stats_frame, font=('Arial', 11), height=10,
                                 bg='#404040', fg='#ffffff', state='disabled')
        self.stats_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))

    def send_transaction(self):
        """
        Handles sending a new transaction
        Validates input and adds transaction to pending list
        """
        try:
            # Get input values
            from_addr = self.from_entry.get().strip()
            to_addr = self.to_entry.get().strip()
            amount = float(self.amount_entry.get())
            
            # Validate inputs
            if not from_addr or not to_addr:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            
            # Check if sender has sufficient balance (skip for first transactions)
            balance = self.blockchain.get_balance(from_addr)
            if balance < amount:
                messagebox.showerror("Error", f"Insufficient balance. Available: {balance} coins\n\nTip: Mine some blocks first to get coins!")
                return
            
            # Create and add transaction
            transaction = {
                'from': from_addr,
                'to': to_addr,
                'amount': amount,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'transfer'
            }
            
            self.blockchain.add_transaction(transaction)
            
            # Clear input fields
            self.from_entry.delete(0, 'end')
            self.to_entry.delete(0, 'end')
            self.amount_entry.delete(0, 'end')
            
            messagebox.showinfo("Success", f"Transaction added to pending list!\n\nGo to Mining tab to process this transaction.")
            self.update_display()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def check_balance(self):
        """
        Checks and displays balance for the entered address
        """
        address = self.balance_entry.get().strip()
        if not address:
            messagebox.showerror("Error", "Please enter an address")
            return
        
        balance = self.blockchain.get_balance(address)
        self.balance_label.config(text=f"Balance: {balance} coins")

    def mine_block(self):
        """
        Mines a new block with pending transactions and mining reward
        Runs in separate thread to prevent GUI freezing
        """
        miner_address = self.miner_entry.get().strip()
        if not miner_address:
            messagebox.showerror("Error", "Please enter miner address")
            return
        
        # Disable mine button and update status
        self.mine_button.config(state='disabled', text="Mining...")
        self.mining_status.config(text="Mining in progress... Finding proof of work...", fg='#f39c12')
        
        # Start mining in separate thread
        threading.Thread(target=self._mine_worker, args=(miner_address,), daemon=True).start()

    def _mine_worker(self, miner_address):
        """
        Worker thread function for mining
        Performs the actual mining work without blocking GUI
        """
        try:
            # Mine the block (this will always work now)
            block = self.blockchain.mine_pending_transactions(miner_address)
            
            # Update GUI in main thread
            self.root.after(0, lambda: self._mining_complete(block, miner_address))
            
        except Exception as e:
            self.root.after(0, lambda: self._mining_error(str(e)))

    def _mining_complete(self, block, miner_address):
        """
        Called when mining is successfully completed
        Updates GUI to reflect the new state
        """
        self.mine_button.config(state='normal', text="⛏️ Start Mining")
        
        # Count transactions (excluding mining reward)
        regular_transactions = [tx for tx in block.transactions if tx.get('type') != 'mining_reward']
        
        if regular_transactions:
            message = f"Block #{block.index} mined successfully!\n\n✅ {len(regular_transactions)} transaction(s) processed\n✅ {miner_address} earned 100 coins mining reward"
            self.mining_status.config(text=f"Block mined! Processed {len(regular_transactions)} transactions", fg='#00ff88')
        else:
            message = f"Block #{block.index} mined successfully!\n\n✅ {miner_address} earned 100 coins mining reward\n\nTip: Add transactions and mine again to process them!"
            self.mining_status.config(text="Block mined! Miner earned 100 coins", fg='#00ff88')
        
        messagebox.showinfo("Mining Success! 🎉", message)
        self.update_display()

    def _mining_error(self, error_msg):
        """
        Called when mining encounters an error
        """
        self.mine_button.config(state='normal', text="⛏️ Start Mining")
        self.mining_status.config(text="Mining failed", fg='#e74c3c')
        messagebox.showerror("Mining Error", f"Mining failed: {error_msg}")

    def update_display(self):
        """
        Updates all displays with current blockchain data
        Refreshes blockchain view and statistics
        """
        # Update blockchain display
        self.blockchain_text.delete(1.0, 'end')
        blockchain_info = self.format_blockchain()
        self.blockchain_text.insert(1.0, blockchain_info)
        
        # Update statistics
        self.update_stats()

    def format_blockchain(self):
        """
        Formats blockchain data for display
        Creates a readable representation of all blocks
        """
        output = "🔗 BLOCKCHAIN STATUS\n"
        output += "=" * 60 + "\n\n"
        output += f"Chain Length: {len(self.blockchain.chain)} blocks\n"
        output += f"Pending Transactions: {len(self.blockchain.pending_transactions)}\n"
        output += f"Mining Difficulty: {self.blockchain.difficulty}\n"
        output += f"Chain Valid: {'✅ Yes' if self.blockchain.is_chain_valid() else '❌ No'}\n\n"
        
        # Display each block
        for i, block in enumerate(self.blockchain.chain):
            if i == 0:
                output += f"🔷 GENESIS BLOCK\n"
            else:
                output += f"📦 BLOCK #{block.index}\n"
            output += "-" * 40 + "\n"
            output += f"Hash: {block.hash[:50]}...\n"
            output += f"Previous Hash: {block.previous_hash[:50]}...\n"
            output += f"Timestamp: {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"Nonce: {block.nonce}\n"
            output += f"Transactions ({len(block.transactions)}):\n"
            
            if block.transactions:
                for j, tx in enumerate(block.transactions, 1):
                    tx_type = "💰 MINING REWARD" if tx.get('type') == 'mining_reward' else "💸 TRANSFER"
                    from_addr = tx['from'] if tx['from'] != 'SYSTEM' else "SYSTEM"
                    output += f"  {j}. {tx_type}: {from_addr} → {tx['to']}: {tx['amount']} coins\n"
            else:
                output += "  No transactions\n"
            
            output += "\n"
        
        # Display pending transactions
        if self.blockchain.pending_transactions:
            output += "⏳ PENDING TRANSACTIONS\n"
            output += "-" * 40 + "\n"
            for i, tx in enumerate(self.blockchain.pending_transactions, 1):
                output += f"{i}. {tx['from']} → {tx['to']}: {tx['amount']} coins\n"
            output += "\n💡 Mine a block to process these transactions!\n"
        else:
            output += "✅ No pending transactions\n"
        
        return output

    def update_stats(self):
        """
        Updates the statistics display in the mining tab
        Shows various blockchain metrics
        """
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, 'end')
        
        total_transactions = sum(len(block.transactions) for block in self.blockchain.chain)
        mining_rewards = sum(1 for block in self.blockchain.chain for tx in block.transactions if tx.get('type') == 'mining_reward')
        regular_transactions = total_transactions - mining_rewards
        
        stats = f"""📊 BLOCKCHAIN STATISTICS

🔗 Chain Information:
• Total Blocks: {len(self.blockchain.chain)}
• Genesis Block: {self.blockchain.chain[0].hash[:20]}...
• Latest Block: {self.blockchain.get_latest_block().hash[:20]}...
• Mining Difficulty: {self.blockchain.difficulty} leading zeros
• Mining Reward: {self.blockchain.mining_reward} coins per block

⏳ Transaction Pool:
• Pending Transactions: {len(self.blockchain.pending_transactions)}

💰 Network Activity:
• Total Transactions: {total_transactions}
• Regular Transfers: {regular_transactions}
• Mining Rewards: {mining_rewards}

🔍 Validation Status:
• Blockchain Valid: {'✅ Valid' if self.blockchain.is_chain_valid() else '❌ Invalid'}

🎯 Next Steps:
{'• Mine your first block to get coins!' if len(self.blockchain.chain) == 1 else '• Add transactions and mine blocks!'}
"""
        
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state='disabled')

def main():
    """
    Main function to start the blockchain GUI application
    Creates the root window and starts the event loop
    """
    # Create main window
    root = tk.Tk()
    
    # Create and run the application
    app = BlockchainGUI(root)
    
    # Start the GUI event loop
    root.mainloop()

# Run the application if this file is executed directly
if __name__ == "__main__":
    main()