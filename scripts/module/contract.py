from brownie.network.web3 import Web3
import json
import re
import logging
from brownie import Contract
import time
from module.exceptions.local_chain_unavailable import LocalChainUnavailable


class MyContract:
    addr: str
    name: str
    source: str
    abi: object
    es_source_path: str
    unverified: bool
    implementation_unverified: bool
    is_proxy: bool
    is_contract: bool = True

    implmentation_verified_brownie_error_message = 'Contract source code not verified'
    contract_unverified = "has not been verified"
    resource_unavailable = "the resource .* is not available."
    contract_self_destructed = "invalid literal for int() with base 16"

    def __init__(self,  addr: str, name: str, source: str, abi: dict) -> None:

        self.addr = addr
        self.name = name
        self.source = source
        self.abi = abi
        self.unverified = False

    def __init__(self, contract: Contract) -> None:
        self.addr = contract.address
        self.source = ContractUtils.parse_contract_source(contract._name, contract._sources)
        self.name = contract._name
        self.abi = contract.abi
        self.unverified = False
        try:
            self.implementation = getattr(contract, "implemenetation")
        except AttributeError:
            self.implementation = None

    def __init__(self) -> None:
        pass

    def get_dict(self) -> str:
        return {"name": self.name, "addr": self.addr}

    def __repr__(self) -> str:
        return json.dumps({"name": self.name, "addr": self.addr})

    @staticmethod
    def has_function(function_def, abi):
        try:
            index = function_def.index("(")
            fn_name_only = False
        except ValueError:
            fn_name_only = True
        function_name = function_def.split("(")[0]
        functions_with_same_name = []
        for obj in abi:
            input_types = []
            if obj["type"] == "function" and function_name.lower() == obj["name"].lower():
                for input in obj["inputs"]:
                    input_types.append(input["internalType"])
                functions_with_same_name.append(f'{function_name}({",".join(input_types)})')
        found = False
        for function in functions_with_same_name:
            if fn_name_only:
                function = function.split("(")[0]
            if function_def.lower() == function.lower():
                found = True
                break
        return found

    @staticmethod
    def get_fn_ret_addr(abi):
        '''
        returns the function call in the case it returns address and has no input as parameter.
        used to potentiallly get roles
        '''
        fns = []  # list of str fn calls returning addresses
        for obj in abi:
            if "outputs" in obj:
                if len(obj['inputs']) == 0 and len(obj["outputs"]) == 1 and obj["outputs"][0]["type"] == "address":
                    fns.append(obj["name"]+"()")
        return fns

    @staticmethod
    def get_similar_view_function_call(function_name, abi):
        fn_def = None
        functions_with_same_name = []
        for obj in abi:
            if obj["type"] == "function" and function_name.lower() in obj["name"].lower():
                mutability_view = "stateMutability" in obj and obj["stateMutability"] == "view"
                if len(obj["inputs"]) == 0 and mutability_view:
                    fn_call = f'{obj["name"]}()'
                    functions_with_same_name.append(fn_call)
        return functions_with_same_name

    def get_full_name(self):
        return f'{self.name}-{self.addr}'

    def get_logic_name(self):
        return f'{self.name}-{self.addr}'

    @staticmethod
    def get_proxy_pair(addr):
        '''
            returns None if not a proxy/contract code unverified
            returns a Proxy pair if contract_addr is a proxy
                Logic contract can be None if unverfied
        '''
        contract = MyContract.from_explorer(addr)
        ContractUtils.bsc._get_implementation()

    @staticmethod
    async def from_explorer(bsc, addr, full=False):
        contract = None
        retries_max = 3
        # Check if EOA
        # if not await ContractUtils.is_contract(bsc, addr):
        # contract = MyContract()
        # contract.is_contract = False
        # return contract
        # Try to load contract
        while not contract and retries_max:
            # False and true = False
            try:
                contract = MyContract._from_explorer_with_brownie(addr, full)
                contract.unverified = False
                contract.implementation_unverified = False
            except ValueError as ex:
                # Unverified contract
                if MyContract.implmentation_verified_brownie_error_message in str(ex):
                    logging.info(f"Mycontract.from_explorer_with_brownie: implementation unverified")
                    print(f"Mycontract.from_explorer_with_brownie: implementation unverified")
                    # exception because of unverified implementation but not contract
                    # then -> get it directly with bscscan
                    contract = await MyContract._from_explorer_with_bscscan(bsc, addr)
                    contract.implementation_unverified = True
                    contract.unverified = False
                    retries_max = 0
                elif MyContract.contract_unverified in str(ex):
                    logging.info(f"Mycontract.from_explorer_with_brownie: contract unverified")
                    print(f"Mycontract.from_explorer_with_brownie: {str(ex)}")
                    contract = MyContract()
                    contract.unverified = True
                    contract.source = ""
                    contract.abi = ""
                    contract.addr = addr
                    contract.implementation_unverified = False
                # network error
                elif isinstance(ex.args, tuple) and isinstance(ex.args[0], dict) and "message" in ex.args[0]:
                    error_msg = ex.args[0]["message"]
                    if re.match(MyContract.resource_unavailable, error_msg):
                        raise LocalChainUnavailable(ex)
                else:
                    # invalid literal for int() with base 16: in case of proxy having logic
                    print(ex)
                    raise ValueError(ex)

            except AttributeError as ex:
                logging.info(f"Mycontract.from_explorer_with_brownie: Error when compiling contract")
                print(f"Mycontract.from_explorer_with_brownie: Error when compiling contract")
                # brownie failed to build the contract. try with bsc aoi
                contract = MyContract._from_explorer_with_bscscan(addr)
                contract.unverified = False
                contract.implementation_unverified = False
            except Exception as ex:
                print("Unexpected Exception")
                print(ex)
                raise Exception(ex)
            retries_max -= 1
        return contract

    @staticmethod
    async def _from_explorer_with_bscscan(bsc, addr):
        contract_name, source, abi, unverified = await MyContract.get_contract_sc_abi(bsc, addr)
        contract = MyContract()
        contract.addr = addr
        contract.name = contract_name
        contract.source = source
        contract.abi = abi
        contract.unverified = unverified
        return contract

    @staticmethod
    async def get_contract_sc_abi(bsc, sc_addr):
        contract = await bsc.get_contract_source_code(contract_address=sc_addr)
        bscscan_api_resp = contract[0]
        part_source = bscscan_api_resp['SourceCode']
        source = ""
        unverified = False
        contract_name = bscscan_api_resp['ContractName']
        part_source = part_source
        if part_source.startswith("{{"):
            contracts = json.loads(part_source[1:-1])["sources"]
            # print(contracts)
            for contract_path in contracts.keys():
                # contract_name_in_key = contract_path.split("/")[-1].split(".")[0]
                contract_def = f"contract {contract_name}"
                match = re.search(contract_def, contracts[contract_path]["content"])
                if match != None:
                    source = contracts[contract_path]["content"]
                    break
        else:
            source = part_source
        # print(result[0])
        try:
            abi = json.loads(bscscan_api_resp['ABI'])
        except:
            abi = None
            unverified = True
        if 'Contract source code not verified' in bscscan_api_resp['ABI']:
            unverified = True

        return contract_name, source, abi, unverified

    @staticmethod
    def _get_implementation(contract, caching):
        '''
            Given a proxy smart contract addr, it tries to get its implementation at different storage location

        '''
        res = []
        for implem_addr in ContractUtils.implem_stor_addrs:
            addr = ContractUtils.bsc.get_storage_at(contract.addr, implem_addr)
            if addr != None:
                addr = addr[26:]
                res.append({contract.addr: f'0x{addr}'})

        try:
            # Flow for proxies EIP-897: DelegateProxy
            if MyContract.has_function("implementation()", contract.abi):
                contract = ContractUtils.web3.eth.contract(ContractUtils.web3.toChecksumAddress(contract.addr), abi=contract.abi)
                implem_addr = contract.functions.implementation().call()
            res.append({contract.addr: f'{implem_addr}'})
        except AttributeError:
            # if implementation
            pass
        except TypeError:
            # if contract don't have implementation method
            pass
        implem_non_null = ContractUtils.get_implementation_non_null(res)

        if caching:
            for i in implem_non_null:
                ContractUtils.cache_contract((MyContract.from_explorer(i)))
        if len(implem_non_null) > 1:
            multiple_implems = ", ".join(implem_non_null)
            # raise ProxySeveralImplementations(f"Proxy found with several implementations set: {multiple_implems}")
        elif len(implem_non_null) == 1:
            return MyContract.from_explorer(implem_non_null[0])
        else:
            return None

    @ staticmethod
    def _from_explorer_with_brownie(addr, full=False):
        tmp_contract = Contract.from_explorer(addr)
        contract = MyContract()
        contract.addr = tmp_contract.address
        contract.source = ContractUtils.parse_contract_source(tmp_contract._name, tmp_contract._sources)
        contract.name = tmp_contract._name
        contract.abi = tmp_contract.abi
        contract.unverified = False
        if full:
            contract.brownie_contract = tmp_contract
        try:
            contract.implementation = getattr(contract, "implementation")
        except AttributeError:
            contract.implementation = None
        return contract


class ContractUtils:

    eoa_code = "0x"

    beacon_implem_addr = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
    ozep_implem_addr = "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"
    eip1967_implem_addr = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    proxiable_implem_addr = "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7"
    implem_stor_addrs = [beacon_implem_addr, ozep_implem_addr, eip1967_implem_addr, proxiable_implem_addr]

    @ staticmethod
    def get_regex_sol(contract_name):
        string = r'contract '+contract_name+r' is (.*?) \{'
        return string

    @staticmethod
    async def is_contract(bsc, addr):
        res = await bsc.get_proxy_code_at(addr)
        if res == "0x":
            return False
        else:
            return True

    @ staticmethod
    def _find_contract_def_str(source_code, contract_name):
        contracts_definitions = []
        match = re.search(ContractUtils.get_regex_sol(contract_name), source_code)
        if match != None:
            word = match.group(0)
            contracts_definitions.append(word)
            # rmeove
        return contracts_definitions

    @ staticmethod
    def parse_contract_def(list_defs):
        '''
            Parse the class defintiion and return list of inhereting contracts.
        '''
        interfaces = []
        for contract_def in list_defs:
            inherited = contract_def.replace("\\n", " ").replace("\\r", "")
            inherited = inherited.split(" is ")[1]
            last_index = inherited.find("{")
            inherited = inherited[:last_index]
            inherited = inherited.split(",")
            for val in inherited:
                interfaces.append(ContractUtils.clean_word(val))
        return interfaces

    @ staticmethod
    def clean_word(word):
        res = word.replace("\\n", "").replace("\\r", "").strip()
        return res

    @ staticmethod
    def get_implementation_non_null(data) -> list:
        '''
            return an implementation address if found. None otherwise
            input [{key: valeu}]
        '''
        res = []
        for key_pair in data:
            for key in key_pair:
                val = key_pair[key]
                if val != "0x0000000000000000000000000000000000000000":
                    res.append(val)
        return res

    @ staticmethod
    def cache_contract(path, contract: MyContract):
        Utils.store_smart_contracts(f'{path}', f'{contract.name}-{contract.addr}', contract.source)
        Utils.store_abi(f'{path}', f'{contract.name}-{contract.addr}-abi', contract.abi)

    @ staticmethod
    def parse_contract_source(contract_name, source):
        parsed_source = ""
        if type(source) is dict:
            # print(contracts)
            for contract_path in source.keys():
                contract_def = f"contract {contract_name}"
                match = re.search(contract_def, source[contract_path])
                if match != None:
                    parsed_source = source[contract_path].replace("\n", "").replace("\\n", "").replace("\r", "").replace("\t", "")
                    break
            return parsed_source
        elif source.startswith("{{"):
            try:
                contracts = json.loads(source[1:-1])["sources"]
            except Exception:
                logging.error(f"Source is not in json format - {source}")            # print(contracts)
            for contract_path in contracts.keys():
                # contract_name_in_key = contract_path.split("/")[-1].split(".")[0]
                contract_def = f"contract {contract_name}"
                match = re.search(contract_def, contracts[contract_path]["content"])
                if match != None:
                    parsed_source = contracts[contract_path]["content"].replace("\n", " ").replace("\\n", " ").replace("\r", " ").replace("\t", " ")
                    break

        else:
            parsed_source = source

        return parsed_source
