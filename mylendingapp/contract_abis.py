# mylendingapp_backend/contract_abis.py

# This is the ABI for the P2PLoan smart contract, derived from the provided source code.
# Ensure this ABI matches your deployed contract for correct interaction.
P2P_LOAN_ABI = [
    {
        "inputs": [
            {"internalType": "address payable", "name": "_lender", "type": "address"},
            {"internalType": "address payable", "name": "_borrower", "type": "address"},
            {"internalType": "uint256", "name": "_loanAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "_collateralAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "_interestRate", "type": "uint256"},
            {"internalType": "uint256", "name": "_loanDuration", "type": "uint256"},
            {"internalType": "address payable", "name": "_loanAssetAddress", "type": "address"},
            {"internalType": "address payable", "name": "_collateralAssetAddress", "type": "address"}
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_borrower", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_collateralAmount", "type": "uint256"}
        ],
        "name": "CollateralLiquidated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_borrower", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_collateralAmount", "type": "uint256"}
        ],
        "name": "CollateralReleased",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_borrower", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_lender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_disbursementTime", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_endTime", "type": "uint256"}
        ],
        "name": "LoanDisbursed",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_borrower", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_loanAmount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_collateralAmount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_duration", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_interestRate", "type": "uint256"}
        ],
        "name": "LoanRequested",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_borrower", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amountPaid", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_remainingDue", "type": "uint256"}
        ],
        "name": "RepaymentMade",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "borrower",
        "outputs": [{"internalType": "address payable", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "calculateAmountDue",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "collateralAmount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "collateralAssetAddress",
        "outputs": [{"internalType": "address payable", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "collateralProvided",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "fundLoan",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "interestRate",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isDisbursed",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isLiquidated",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isRepaid",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "lender",
        "outputs": [{"internalType": "address payable", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "liquidateCollateral",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "loanAmount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "loanAssetAddress",
        "outputs": [{"internalType": "address payable", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "loanDuration",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "loanEndTime",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "loanStartTime",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "provideCollateral",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "repayLoan",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "withdrawAccidentalEth",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "stateMutability": "payable",
        "type": "receive"
    }
]

# ERC-20 Token ABI (Common functions for balance, approve, transferFrom)
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]