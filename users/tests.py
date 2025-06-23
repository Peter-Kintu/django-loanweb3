import os
from django.test import TestCase
from web3 import Web3
import json
import time

# --- Configuration for your local blockchain (Ganache/Hardhat) ---
WEB3_PROVIDER_URL = 'http://127.0.0.1:8545' # Ensure your Hardhat or Ganache node is running on this port

# --- CORRECTED PATH TO YOUR CONTRACT ARTIFACT ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

CONTRACT_ARTIFACT_PATH = os.path.join(
    PROJECT_ROOT,
    'blockchain',
    'artifacts',
    'contracts',
    'p2ploan.sol',
    'P2PLoan.json' # This is the correct filename
)

# --- IMPORTANT: ACCOUNTS FROM YOUR PROVIDED GANACHE OUTPUT ---
# Lender (Account 7) - UPDATED TO ACCOUNT 7
TEST_SENDER_PRIVATE_KEY = '0x8fad1569d6f8e713ae4a54f725a1efe60d4ef04580cbf28cf975e8e3cf787ec4'.strip() # Account (7) Private Key

# Borrower (Account 6) - Keeping this distinct for P2P loan logic
TEST_BORROWER_ADDRESS = '0x2b1f64A9F4e0F9bfa644f0642F956704CB13fA2D'.strip() # Account (6) Address
TEST_BORROWER_PRIVATE_KEY = '0x8372cdc9df3bb3f96512d454d3dbc7c160155aec17cccc70365d2a84df8d41d4'.strip() # Account (6) Private Key


class BlockchainInteractionTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Sets up the Web3 connection and loads contract ABI/bytecode ONCE for all tests.
        """
        super().setUpClass() # Call parent class setUpClass
        cls.w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
        if not cls.w3.is_connected():
            raise ConnectionError(
                f"Web3 is not connected to {WEB3_PROVIDER_URL}. "
                "Please ensure your Hardhat or Ganache node is running in a separate terminal."
            )
        print(f"\nConnected to Web3 provider: {WEB3_PROVIDER_URL}")

        try:
            with open(CONTRACT_ARTIFACT_PATH, 'r') as f:
                contract_data = json.load(f)
                cls.contract_abi = contract_data['abi']
                cls.contract_bytecode = contract_data['bytecode']
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Contract artifact not found at {CONTRACT_ARTIFACT_PATH}. "
                "Did you compile your Hardhat project (`npx hardhat compile`) and set the correct path?"
            )
        except KeyError:
            raise ValueError("Contract artifact JSON is missing 'abi' or 'bytecode' keys.")

        try:
            temp_sender_account = cls.w3.eth.account.from_key(TEST_SENDER_PRIVATE_KEY)
            cls.sender_address = temp_sender_account.address
            print(f"Using sender account (Lender): {cls.sender_address}")
        except ValueError as e:
            raise ValueError(f"Error deriving sender account from TEST_SENDER_PRIVATE_KEY: {e}. "
                             "Ensure it's the full 66-character hex string from your Ganache CLI output.")
        
        try:
            cls.borrower_checksum_address = Web3.to_checksum_address(TEST_BORROWER_ADDRESS)
            print(f"Using borrower account: {cls.borrower_checksum_address}")
        except ValueError as e:
            raise ValueError(f"Error with TEST_BORROWER_ADDRESS: {e}. "
                             "Please ensure it's a valid 0x-prefixed hexadecimal address and re-copy it carefully from Ganache.")

        cls.loan_amount = cls.w3.to_wei(1, 'ether')
        cls.collateral_amount = cls.w3.to_wei(0.1, 'ether')
        cls.interest_rate = 500
        cls.loan_duration = 60 * 60 * 24 * 30
        
        # In a real app, these would be actual ERC-20 token addresses
        cls.loan_asset_address = Web3.to_checksum_address("0x0000000000000000000000000000000000000000") 
        cls.collateral_asset_address = Web3.to_checksum_address("0x0000000000000000000000000000000000000001") 

    def setUp(self):
        """
        Deploys a fresh contract instance and takes a blockchain snapshot for each test method.
        """
        # Take a snapshot of the blockchain state BEFORE deploying the contract
        # This allows us to revert to a clean state for the next test
        self.snapshot_id = self.w3.provider.make_request('evm_snapshot', []).get('result')

        print(f"\nDeploying P2PLoan contract for test {self._testMethodName}...")
        P2PLoanContract = self.w3.eth.contract(abi=self.contract_abi, bytecode=self.contract_bytecode)
        
        # Ensure sender account is derived for current test context
        self.sender_account = self.w3.eth.account.from_key(TEST_SENDER_PRIVATE_KEY)
        self.w3.eth.default_account = self.sender_account.address

        nonce = self.w3.eth.get_transaction_count(self.sender_account.address)
        gas_price = self.w3.eth.gas_price

        constructor_tx = P2PLoanContract.constructor(
            self.sender_account.address, # Use self.sender_account.address directly
            self.borrower_checksum_address,
            self.loan_amount,
            self.collateral_amount,
            self.interest_rate,
            self.loan_duration,
            self.loan_asset_address,
            self.collateral_asset_address
        ).build_transaction({
            'from': self.sender_account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 5000000
        })

        signed_tx = self.sender_account.sign_transaction(constructor_tx)
        
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
    
        self.contract_address = tx_receipt.contractAddress
        if not self.contract_address:
            raise ValueError("Contract deployment failed: No contract address returned.")
            
        print(f"P2PLoan deployed to: {self.contract_address} for test {self._testMethodName}.")
        self.p2p_loan_contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)

    def tearDown(self):
        """
        Reverts the blockchain state to the snapshot taken at the beginning of setUp.
        """
        # Revert to the snapshot, cleaning up the contract and state
        self.w3.provider.make_request('evm_revert', [self.snapshot_id])
        print(f"Blockchain reverted for test {self._testMethodName}.")

    def test_01_contract_initial_state(self):
        """
        Tests that the constructor arguments were correctly set when the contract was deployed.
        """
        print(f"\nTest 1: Verifying contract initial state for {self._testMethodName}...")
        self.assertEqual(self.p2p_loan_contract.functions.lender().call(), self.sender_account.address)
        self.assertEqual(self.p2p_loan_contract.functions.borrower().call(), self.borrower_checksum_address)
        self.assertEqual(self.p2p_loan_contract.functions.loanAmount().call(), self.loan_amount)
        self.assertEqual(self.p2p_loan_contract.functions.collateralAmount().call(), self.collateral_amount)
        self.assertEqual(self.p2p_loan_contract.functions.interestRate().call(), self.interest_rate)
        self.assertEqual(self.p2p_loan_contract.functions.loanDuration().call(), self.loan_duration)
        self.assertEqual(self.p2p_loan_contract.functions.loanAssetAddress().call(), self.loan_asset_address)
        self.assertEqual(self.p2p_loan_contract.functions.collateralAssetAddress().call(), self.collateral_asset_address)
        self.assertFalse(self.p2p_loan_contract.functions.isRepaid().call(), "isRepaid should be false initially")
        self.assertFalse(self.p2p_loan_contract.functions.isLiquidated().call(), "isLiquidated should be false initially")
        self.assertFalse(self.p2p_loan_contract.functions.isDisbursed().call(), "isDisbursed should be false initially")
        self.assertFalse(self.p2p_loan_contract.functions.collateralProvided().call(), "collateralProvided should be false initially")
            
        print(f"Test 1: Contract initial state check passed for {self._testMethodName}.")

    def test_02_provide_collateral(self):
        """
        Tests the provideCollateral functionality by the borrower.
        """
        print(f"\nTest 2: Attempting to provide collateral for {self._testMethodName}...")
        
        borrower_account = self.w3.eth.account.from_key(TEST_BORROWER_PRIVATE_KEY) 
        
        contract_initial_balance = self.w3.eth.get_balance(self.contract_address)

        nonce = self.w3.eth.get_transaction_count(borrower_account.address)
        gas_price = self.w3.eth.gas_price
        
        tx = self.p2p_loan_contract.functions.provideCollateral().build_transaction({
            'from': borrower_account.address,
            'value': self.collateral_amount, # Sending the collateralAmount as ETH
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 300000
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=TEST_BORROWER_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash) # FIX: Use tx_hash directly
        self.assertEqual(receipt.status, 1, "provideCollateral transaction should be successful")
        print(f"provideCollateral transaction successful. Tx Hash: {tx_hash.hex()}")

        contract_final_balance = self.w3.eth.get_balance(self.contract_address)
        self.assertAlmostEqual(contract_final_balance, contract_initial_balance + self.collateral_amount, delta=self.w3.to_wei(0.0001, 'ether'))
        
        self.assertTrue(self.p2p_loan_contract.functions.collateralProvided().call(), "Contract should acknowledge collateral has been provided")
        print(f"Test 2: Collateral provided check passed for {self._testMethodName}.")

    def test_03_fund_loan(self):
        """
        Tests the fundLoan functionality by the lender.
        Assumes `msg.value` is used to send the loan amount (ETH).
        """
        print(f"\nTest 3: Attempting to fund loan by lender for {self._testMethodName}...")

        # Ensure collateral is provided before funding
        borrower_account = self.w3.eth.account.from_key(TEST_BORROWER_PRIVATE_KEY)
        nonce = self.w3.eth.get_transaction_count(borrower_account.address)
        gas_price = self.w3.eth.gas_price
        collateral_tx = self.p2p_loan_contract.functions.provideCollateral().build_transaction({
            'from': borrower_account.address, 'value': self.collateral_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_collateral_tx = self.w3.eth.account.sign_transaction(collateral_tx, private_key=TEST_BORROWER_PRIVATE_KEY)
        collateral_tx_hash = self.w3.eth.send_raw_transaction(signed_collateral_tx.raw_transaction) # Store the hash
        self.w3.eth.wait_for_transaction_receipt(collateral_tx_hash) # FIX: Use collateral_tx_hash directly
        self.assertTrue(self.p2p_loan_contract.functions.collateralProvided().call(), "Collateral should be marked as provided before funding")

        borrower_initial_balance = self.w3.eth.get_balance(self.borrower_checksum_address)
        
        nonce = self.w3.eth.get_transaction_count(self.sender_account.address)
        gas_price = self.w3.eth.gas_price

        tx = self.p2p_loan_contract.functions.fundLoan().build_transaction({
            'from': self.sender_account.address,
            'value': self.loan_amount,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 300000
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=TEST_SENDER_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.assertEqual(receipt.status, 1, "fundLoan transaction should be successful")
        print(f"fundLoan transaction successful. Tx Hash: {tx_hash.hex()}")

        self.assertTrue(self.p2p_loan_contract.functions.isDisbursed().call(), "Loan should be marked as disbursed after funding")
        
        borrower_final_balance = self.w3.eth.get_balance(self.borrower_checksum_address)
        self.assertAlmostEqual(borrower_final_balance, borrower_initial_balance + self.loan_amount, delta=self.w3.to_wei(0.0001, 'ether'))

        print(f"Test 3: Loan funding check passed for {self._testMethodName}.")

    def test_04_calculate_amount_due(self):
        """
        Tests the calculateAmountDue view function.
        This test ensures the loan is funded before checking amount due with interest.
        """
        print(f"\nTest 4: Calculating amount due (before/after funding) for {self._testMethodName}...")
        
        # Ensure collateral is provided before funding
        borrower_account = self.w3.eth.account.from_key(TEST_BORROWER_PRIVATE_KEY)
        nonce = self.w3.eth.get_transaction_count(borrower_account.address)
        gas_price = self.w3.eth.gas_price
        collateral_tx = self.p2p_loan_contract.functions.provideCollateral().build_transaction({
            'from': borrower_account.address, 'value': self.collateral_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_collateral_tx = self.w3.eth.account.sign_transaction(collateral_tx, private_key=TEST_BORROWER_PRIVATE_KEY)
        collateral_tx_hash = self.w3.eth.send_raw_transaction(signed_collateral_tx.raw_transaction) # Store the hash
        self.w3.eth.wait_for_transaction_receipt(collateral_tx_hash) # FIX: Use collateral_tx_hash directly
        
        # Fund loan for the context of this test
        nonce = self.w3.eth.get_transaction_count(self.sender_account.address)
        gas_price = self.w3.eth.gas_price
        fund_tx = self.p2p_loan_contract.functions.fundLoan().build_transaction({
            'from': self.sender_account.address, 'value': self.loan_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_fund_tx = self.w3.eth.account.sign_transaction(fund_tx, private_key=TEST_SENDER_PRIVATE_KEY)
        tx_hash_for_wait = self.w3.eth.send_raw_transaction(signed_fund_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash_for_wait)
        self.assertTrue(self.p2p_loan_contract.functions.isDisbursed().call(), "Loan should be marked as disbursed after funding attempt.")


        # Immediately after funding (without advancing time), interest should be negligible/zero
        amount_due_after_fund = self.p2p_loan_contract.functions.calculateAmountDue().call()
        self.assertAlmostEqual(amount_due_after_fund, self.loan_amount, delta=self.w3.to_wei(0.00001, 'ether'))
        print(f"Amount due after funding (without time advance): {self.w3.from_wei(amount_due_after_fund, 'ether')} ETH.")
        
        print(f"Test 4: calculateAmountDue check passed for {self._testMethodName}.")

    def test_05_repay_loan(self):
        """
        Tests the repayLoan functionality by the borrower.
        Requires loan to be funded first and collateral provided.
        """
        print(f"\nTest 5: Attempting to repay loan for {self._testMethodName}...")
        
        # 1. Ensure collateral is provided
        borrower_account = self.w3.eth.account.from_key(TEST_BORROWER_PRIVATE_KEY)
        nonce = self.w3.eth.get_transaction_count(borrower_account.address)
        gas_price = self.w3.eth.gas_price
        collateral_tx = self.p2p_loan_contract.functions.provideCollateral().build_transaction({
            'from': borrower_account.address, 'value': self.collateral_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_collateral_tx = self.w3.eth.account.sign_transaction(collateral_tx, private_key=TEST_BORROWER_PRIVATE_KEY)
        collateral_tx_hash = self.w3.eth.send_raw_transaction(signed_collateral_tx.raw_transaction) # Store the hash
        self.w3.eth.wait_for_transaction_receipt(collateral_tx_hash) # FIX: Use collateral_tx_hash directly
        self.assertTrue(self.p2p_loan_contract.functions.collateralProvided().call(), "Collateral should be provided.")

        # 2. Ensure loan is funded
        nonce = self.w3.eth.get_transaction_count(self.sender_account.address)
        gas_price = self.w3.eth.gas_price
        fund_tx = self.p2p_loan_contract.functions.fundLoan().build_transaction({
            'from': self.sender_account.address, 'value': self.loan_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_fund_tx = self.w3.eth.account.sign_transaction(fund_tx, private_key=TEST_SENDER_PRIVATE_KEY)
        tx_hash_for_wait = self.w3.eth.send_raw_transaction(signed_fund_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash_for_wait)
        self.assertTrue(self.p2p_loan_contract.functions.isDisbursed().call(), "Loan should be marked as disbursed after funding attempt.")


        amount_to_repay = self.p2p_loan_contract.functions.calculateAmountDue().call()
        
        lender_initial_balance = self.w3.eth.get_balance(self.p2p_loan_contract.functions.lender().call())
        
        nonce = self.w3.eth.get_transaction_count(borrower_account.address)
        gas_price = self.w3.eth.gas_price

        # Add a small buffer to the amount sent for repayment
        amount_to_send_for_repayment = amount_to_repay + self.w3.to_wei(0.00001, 'ether') # Add a tiny buffer (e.g., 0.00001 ETH)

        tx = self.p2p_loan_contract.functions.repayLoan().build_transaction({
            'from': borrower_account.address,
            'value': amount_to_send_for_repayment, # Borrower sends total amount due + buffer
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 500000
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=TEST_BORROWER_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.assertEqual(receipt.status, 1, "repayLoan transaction should be successful")
        print(f"repayLoan transaction successful. Tx Hash: {tx_hash.hex()}")

        self.assertTrue(self.p2p_loan_contract.functions.isRepaid().call(), "Loan should be marked as repaid")
        lender_final_balance = self.w3.eth.get_balance(self.p2p_loan_contract.functions.lender().call())
        self.assertAlmostEqual(lender_final_balance, lender_initial_balance + amount_to_repay, delta=self.w3.to_wei(0.0001, 'ether'))
        print(f"Test 5: Loan repayment and collateral release check passed for {self._testMethodName}.")

    def test_06_liquidate_collateral(self):
        """
        Tests the liquidateCollateral functionality by the lender.
        Requires loan to be funded, collateral provided, and loan to be overdue.
        """
        print(f"\nTest 6: Attempting to liquidate collateral for {self._testMethodName}...")
        
        # 1. Ensure collateral is provided
        borrower_account = self.w3.eth.account.from_key(TEST_BORROWER_PRIVATE_KEY)
        nonce = self.w3.eth.get_transaction_count(borrower_account.address)
        gas_price = self.w3.eth.gas_price
        collateral_tx = self.p2p_loan_contract.functions.provideCollateral().build_transaction({
            'from': borrower_account.address, 'value': self.collateral_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_collateral_tx = self.w3.eth.account.sign_transaction(collateral_tx, private_key=TEST_BORROWER_PRIVATE_KEY)
        collateral_tx_hash = self.w3.eth.send_raw_transaction(signed_collateral_tx.raw_transaction) # Store the hash
        self.w3.eth.wait_for_transaction_receipt(collateral_tx_hash) # FIX: Use collateral_tx_hash directly
        self.assertTrue(self.p2p_loan_contract.functions.collateralProvided().call(), "Collateral should be provided.")

        # 2. Ensure loan is funded
        nonce = self.w3.eth.get_transaction_count(self.sender_account.address)
        gas_price = self.w3.eth.gas_price
        fund_tx = self.p2p_loan_contract.functions.fundLoan().build_transaction({
            'from': self.sender_account.address, 'value': self.loan_amount,
            'nonce': nonce, 'gasPrice': gas_price, 'gas': 300000
        })
        signed_fund_tx = self.w3.eth.account.sign_transaction(fund_tx, private_key=TEST_SENDER_PRIVATE_KEY)
        tx_hash_for_wait = self.w3.eth.send_raw_transaction(signed_fund_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash_for_wait)
        self.assertTrue(self.p2p_loan_contract.functions.isDisbursed().call(), "Loan should be marked as disbursed after funding attempt.")


        print("   (Advancing time to make loan overdue)")
        self.w3.provider.make_request('evm_increaseTime', [self.loan_duration + 3600]) # Loan duration + 1 hour
        self.w3.provider.make_request('evm_mine', []) # Mine a new block to apply time change

        # Verify loan is now overdue
        self.assertTrue(self.w3.eth.get_block('latest')['timestamp'] > self.p2p_loan_contract.functions.loanEndTime().call(), "Loan should be overdue")
        
        lender_initial_balance = self.w3.eth.get_balance(self.sender_account.address)
        
        nonce = self.w3.eth.get_transaction_count(self.sender_account.address)
        gas_price = self.w3.eth.gas_price

        tx = self.p2p_loan_contract.functions.liquidateCollateral().build_transaction({
            'from': self.sender_account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 300000
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=TEST_SENDER_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.assertEqual(receipt.status, 1, "liquidateCollateral transaction should be successful")
        print(f"liquidateCollateral transaction successful. Tx Hash: {tx_hash.hex()}")

        gas_used = receipt.gasUsed
        transaction_gas_cost = gas_used * gas_price
        
        self.assertTrue(self.p2p_loan_contract.functions.isLiquidated().call(), "Collateral should be marked as liquidated")
        lender_final_balance = self.w3.eth.get_balance(self.p2p_loan_contract.functions.lender().call())
        expected_lender_final_balance = lender_initial_balance + self.collateral_amount - transaction_gas_cost
        
        self.assertAlmostEqual(lender_final_balance, expected_lender_final_balance, delta=self.w3.to_wei(0.0001, 'ether'))
        print(f"Test 6: Collateral liquidation check passed for {self._testMethodName}.")